"""依 parts.json 把角色切成透明分層 PNG，並誠實回報被遮擋／需要人工修補的部分。"""
import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from . import C2SError, NeedsInput, load_json, save_json
from .analyzer import ALPHA_MIN
from .providers import REPAIR_PROVIDERS
from .rig_builder import PRESETS, default_role, required_parts

# 被遮住的面積超過部件的這個比例，就不把自動填補當成完成，改列人工修補任務
MAX_AUTO_HIDDEN_RATIO = 0.35
# 補圖可靠度門檻（校準依據見 docs/DECISIONS.md D-31）。不可靠的補圖若在動畫中露出，refine 會改為 needs_manual。
HOLDOUT_MAX = 0.08
CONTOUR_HIDDEN_MAX = 0.25


def part_mask(part, shape):
    if "mask" in part:
        return np.array(Image.open(part["mask"]).convert("L")) > 127
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [np.array(part["polygon"], np.int32)], 1)
    return m.astype(bool)


SHADOW_COLOR_TOL = 48  # 與影子典型顏色的 RGB 距離超過此值，就不是影子


def _ground_keeps_shadow(parts, masks, rgba):
    """地面影子留在地上不跟著跳，所以它的範圍只能有影子：顏色不像影子、且連到身體部件附近（角色高度 3% 內）的像素區塊
    （多邊形多畫到的腳尖、裙襬）改歸最近的身體部件。影子的典型顏色取遠離身體那一段的中位數。原地修改 masks。"""
    fg = rgba[..., 3] > ALPHA_MIN
    ground = [p["name"] for p in parts if (p.get("role") or default_role(p["name"])) == "ground"]
    others = [p["name"] for p in parts if p["name"] not in ground]
    if not ground or not others:
        return
    body = np.any([masks[n] for n in others], axis=0)
    ys = np.nonzero(body)[0]
    k = max(3, round(0.03 * (ys.max() - ys.min() + 1)))
    near = cv2.dilate(body.astype(np.uint8), np.ones((2 * k + 1, 2 * k + 1), np.uint8)).astype(bool)
    rgb = rgba[..., :3].astype(int)
    dist = np.stack([cv2.distanceTransform((~masks[n]).astype(np.uint8), cv2.DIST_L2, 3) for n in others])
    for g in ground:
        far = masks[g] & fg & ~near
        if far.sum() < 20:  # 影子幾乎都在腳下，量不到典型顏色：不動
            continue
        ref = np.median(rgb[far], axis=0)
        unlike = masks[g] & fg & ~body & (np.linalg.norm(rgb - ref, axis=2) > SHADOW_COLOR_TOL)
        n, lab = cv2.connectedComponents(unlike.astype(np.uint8))
        touching = np.unique(lab[unlike & near])  # 不像影子的區塊只要有一部分貼著身體，整塊都歸身體
        moved = np.isin(lab, touching[touching > 0])
        masks[g] &= ~moved
        owner = dist.argmin(axis=0)
        for i, n in enumerate(others):
            masks[n] |= moved & (owner == i)


def _bbox(mask):
    ys, xs = np.nonzero(mask)
    return int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)


def _cut(part, rgba, masks, parts, repair):
    """回傳 (RGBA 圖層, metadata 條目, 補圖遮罩或 None)。圖層與遮罩都裁切到部件自身範圍。"""
    fg = rgba[..., 3] > ALPHA_MIN
    above = np.zeros(fg.shape, bool)
    for other in parts:
        if other["z"] > part["z"]:
            above |= masks[other["name"]]
    mine = masks[part["name"]] & fg
    visible, hidden = mine & ~above, mine & above
    entry = {"name": part["name"], "z": part["z"], "parent": part.get("parent"), "role": part.get("role"),
             "motion": part.get("motion", 1.0), "attach": part.get("attach", [])}
    if not visible.any():
        entry.update(status="needs_manual", reason="完全被其他部件遮住或範圍內沒有前景，無法自動產生")
        return None, entry, None
    x, y, w, h = _bbox(mine)
    crop = rgba[y:y + h, x:x + w].copy()
    vis, hid = visible[y:y + h, x:x + w], hidden[y:y + h, x:x + w]
    solid = vis & (crop[..., 3] > 200)  # 半透明的邊緣像素混了背景色，不拿來當修補來源
    crop[..., 3] = np.where(vis, crop[..., 3], 0)
    ratio = hidden.sum() / mine.sum()
    entry.update(x=x, y=y, w=w, h=h, hidden_ratio=round(float(ratio), 4))
    if not hid.any():
        entry["status"] = "ok"
        return crop, entry, None
    # 遮擋者範圍先在整張畫布內縮 4px 再裁切：部件之間為了不留縫而刻意重疊的淺接縫不算「被遮住的輪廓」，
    # 裁切邊緣的輪廓也不會被誤刪
    deep = cv2.erode(above.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)[y:y + h, x:x + w]
    holdout, contour = _repair_risk(crop[..., :3], solid, hid, mine[y:y + h, x:x + w], deep, repair)
    entry.update(holdout_error=round(holdout, 4), contour_hidden=round(contour, 4),
                 repair_reliable=holdout <= HOLDOUT_MAX and contour <= CONTOUR_HIDDEN_MAX,
                 occluders=[o["name"] for o in parts if o["z"] > part["z"] and (masks[o["name"]] & hidden).any()])
    # 只用這個部件自己看得見的像素往被遮住的區域延伸，避免染到別的部件的顏色
    crop[..., :3] = repair(crop[..., :3], ~solid)
    crop[..., 3] = np.where(hid, 255, crop[..., 3])
    if ratio > MAX_AUTO_HIDDEN_RATIO:
        entry.update(status="needs_manual", reason=f"被遮擋面積 {ratio:.0%} 超過自動修補上限 "
                     f"{MAX_AUTO_HIDDEN_RATIO:.0%}，目前的填補只是草稿")
    else:
        entry["status"] = "auto_repaired"
    return crop, entry, hid


def _repair_risk(rgb, solid, hid, region, deep_above, repair):
    """補圖可靠度的兩個實測值。
    holdout_error：在破洞外圍挖掉一圈（寬度＝破洞的厚度）看得見的像素，連同破洞一起補，量該圈與真值的平均誤差（0~1）。
        紋理越複雜，邊緣延伸越補不回來。
    contour_hidden：部件輪廓線落在被遮擋區的比例。那段形狀是看圖猜的，任何補圖都補不出來。"""
    k3 = np.ones((3, 3), np.uint8)
    erode = lambda m, n: cv2.erode(m.astype(np.uint8), k3, iterations=n, borderType=cv2.BORDER_CONSTANT, borderValue=0).astype(bool)
    hid_u8 = hid.astype(np.uint8)
    perimeter = max(1.0, sum(cv2.arcLength(c, True) for c in cv2.findContours(hid_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]))
    # 圈寬＝破洞平均厚度（2×面積÷周長），不超過部件短邊的 1/4，免得把可見像素挖光
    width = min(max(2.0, 2 * hid.sum() / perimeter), 0.25 * min(hid.shape))
    dist = cv2.distanceTransform((~hid).astype(np.uint8), cv2.DIST_L2, 3)
    core = erode(solid, 2)  # 內縮 2px：部件自己的輪廓線與反鋸齒邊緣不算進紋理
    ring = core & (dist <= width + 2)
    known = core & ~ring
    if ring.sum() < 16 or known.sum() < max(50, ring.sum() // 2):
        holdout = 1.0  # 可見像素太少，無法驗證，也就不能宣稱可靠
    else:
        pred = repair(rgb, ~known)
        holdout = float(np.abs(pred[ring].astype(float) - rgb[ring]).mean() / 255)
    edge = region & ~erode(region, 1)
    return holdout, float((edge & deep_above).sum() / max(1, edge.sum()))


def _apply_override(path, entry, canvas_size):
    """人工修好的圖層：可以是整張畫布大小（保留原座標），或與自動圖層相同大小。"""
    try:
        img = Image.open(path).convert("RGBA")
    except OSError as e:  # 含 UnidentifiedImageError
        raise C2SError(f"{path} 不是可讀取的圖片：{e}") from e
    if img.size == tuple(canvas_size):
        arr = np.array(img)
        if not (arr[..., 3] > ALPHA_MIN).any():
            raise C2SError(f"{path} 是全透明的")
        x, y, w, h = _bbox(arr[..., 3] > ALPHA_MIN)
        arr = arr[y:y + h, x:x + w]
        entry.update(x=x, y=y, w=w, h=h)
    elif "w" in entry and img.size == (entry["w"], entry["h"]):
        arr = np.array(img)
    else:
        want = f"{canvas_size[0]}x{canvas_size[1]}（整張畫布）"
        if "w" in entry:
            want += f" 或 {entry['w']}x{entry['h']}（與自動圖層相同）"
        raise C2SError(f"{path} 尺寸 {img.size[0]}x{img.size[1]} 無法定位，需要 {want}")
    entry.update(status="replaced", reason=None)
    return arr


def composite(layers, canvas_size):
    """layers: [(RGBA, x, y)] 由後到前。回傳 (疊在白底上的 RGB float, alpha 0~1)。"""
    w, h = canvas_size
    out, alpha = np.full((h, w, 3), 255.0), np.zeros((h, w))
    for arr, x, y in layers:
        a = arr[..., 3:4].astype(float) / 255
        region = out[y:y + arr.shape[0], x:x + arr.shape[1]]
        region[:] = arr[..., :3] * a + region * (1 - a)
        ar = alpha[y:y + arr.shape[0], x:x + arr.shape[1]]
        ar[:] = a[..., 0] + ar * (1 - a[..., 0])
    return out, alpha


def masked_mae(a, b):
    """比較兩個 composite 結果，只計算任一方有前景的範圍，空白背景不會把差異稀釋掉。顏色與 alpha 差異取大者。"""
    region = (a[1] > 0.02) | (b[1] > 0.02)
    if not region.any():
        return 0.0
    diff = np.maximum(np.abs(a[0] - b[0]).mean(axis=2) / 255, np.abs(a[1] - b[1]))
    return float(diff[region].mean())


def _same_png(path, arr):
    return path.exists() and np.array_equal(np.array(Image.open(path).convert("RGBA")), arr)


def prepare(workdir, only=None, replace=None):
    """切圖。每次都重算全部部件（部件之間的遮擋互相影響），但只寫入內容有變的圖層檔。
    only：強制重寫這個部件的圖層；replace：{部件名: 人工修好的 PNG}，驗證通過才保存到永久的 overrides 目錄。"""
    wd = Path(workdir)
    if not (wd / "source_rgba.png").exists() or not (wd / "parts.json").exists():
        raise NeedsInput(f"{wd} 尚未完成分析或缺少 parts.json，請先執行 c2s analyze 並補上 parts.json")
    rgba = np.array(Image.open(wd / "source_rgba.png"))
    h, w = rgba.shape[:2]
    doc = load_json(wd / "parts.json")
    src = Path(doc.get("source", wd / "parts.json"))
    if src.resolve() != (wd / "parts.json").resolve() and src.exists() and src.stat().st_mtime > (wd / "parts.json").stat().st_mtime:
        raise NeedsInput(f"{src} 比工作目錄內的複本新（改過了），請重新執行 c2s analyze 或 c2s run，修改才會生效")
    parts = sorted(doc["parts"], key=lambda p: p["z"])
    names = [p["name"] for p in parts]
    preset = PRESETS[doc.get("preset", "humanoid-chibi")]
    replace = {k: Path(v) for k, v in (replace or {}).items()}
    for name in ([only] if only else []) + list(replace):
        if name not in names:
            raise C2SError(f"沒有名為 {name} 的部件（現有：{', '.join(names)}）")
    for src in replace.values():
        if not src.is_file():
            raise C2SError(f"找不到替換用的圖片：{src}")

    masks = {p["name"]: part_mask(p, (h, w)) for p in parts}
    _ground_keeps_shadow(parts, masks, rgba)
    (wd / "quality" / "quality_report.json").unlink(missing_ok=True)  # 圖層變了，舊的品質報告不再有效
    repair = REPAIR_PROVIDERS["opencv"]
    odir = overrides_dir(wd, doc)
    results = []  # (entry, layer 或 None, 補圖遮罩或 None)
    for p in parts:
        name = p["name"]
        layer, entry, filled = _cut(p, rgba, masks, parts, repair)
        override = replace.get(name) or odir / f"{name}.png"
        if override.exists():
            layer = _apply_override(override, entry, (w, h))  # 尺寸不對會在寫入任何檔案前就失敗
            filled = None  # 人工修補圖沒有「自動補的像素」
        if layer is not None:
            entry["file"] = f"layers/{name}.png"
            fx, fy = preset["anchors"].get(name, (0.5, 0.5))
            entry["pivot"] = p.get("pivot") or [round(entry["x"] + fx * entry["w"], 1), round(entry["y"] + fy * entry["h"], 1)]
        results.append((entry, layer, filled))

    (wd / "layers").mkdir(exist_ok=True)
    shutil.rmtree(wd / "repair_masks", ignore_errors=True)
    written = []
    for entry, layer, filled in results:
        if filled is not None and layer is not None:  # 補上的像素：品質檢查用來量測動畫中是否露出
            (wd / "repair_masks").mkdir(exist_ok=True)
            Image.fromarray(filled.astype(np.uint8) * 255).save(wd / "repair_masks" / f"{entry['name']}.png")
        if layer is None:
            continue
        path = wd / entry["file"]
        if entry["name"] == only or not _same_png(path, layer):
            Image.fromarray(layer).save(path)
            written.append(entry["name"])
    produced = {f"{e['name']}.png" for e, layer, _ in results if layer is not None}
    for stale in (wd / "layers").glob("*.png"):  # 部件被刪除或變成完全被遮住時，舊圖層不能留著被當成有效輸出
        if stale.name not in produced:
            stale.unlink()
    for name, new in replace.items():
        odir.mkdir(parents=True, exist_ok=True)
        dest = odir / f"{name}.png"
        if dest.exists() and dest.resolve() != new.resolve():
            shutil.copyfile(dest, dest.with_suffix(".png.bak"))  # 人工修補圖不可回復，覆蓋前先備份
        if not dest.exists() or dest.resolve() != new.resolve():
            shutil.copyfile(new, dest)
    entries = [e for e, _, _ in results]

    assigned = np.zeros((h, w), bool)
    for m in masks.values():
        assigned |= m
    fg = rgba[..., 3] > ALPHA_MIN
    body = fg & assigned  # 只算部件範圍內的像素：散落的特效不影響骨架原點與尺寸
    if not body.any():
        raise C2SError("parts.json 的範圍內沒有任何前景像素，請檢查座標")
    ys, xs = np.nonzero(body)
    drawable = [(e, layer) for e, layer, _ in results if layer is not None]
    recomposed = composite([(layer, e["x"], e["y"]) for e, layer in drawable], (w, h))
    source_rgba = rgba.copy()
    source_rgba[..., 3] = np.where(assigned, source_rgba[..., 3], 0)
    source = composite([(source_rgba, 0, 0)], (w, h))
    meta = {
        "image": doc.get("image"), "canvas": [w, h], "preset": doc.get("preset", "humanoid-chibi"), "absent": doc.get("absent", []),
        "bbox": [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)],
        # 骨架原點：角色腳底中央（原圖像素座標）
        "origin": [round(float(xs.min() + xs.max()) / 2, 1), int(ys.max()) + 1],
        "unassigned_ratio": round(float((fg & ~assigned).sum() / fg.sum()), 4),
        "recompose_mae": round(masked_mae(recomposed, source), 5),
        "unassigned_regions": _unassigned_regions(fg & ~assigned, masks),
        "parts": entries,
    }
    save_json(wd / "metadata.json", meta)
    missing_required, manual = write_reports(wd)
    shown = recomposed[0].copy()
    shown[fg & ~assigned] = (255, 0, 255)  # 洋紅色：前景像素沒被任何部件涵蓋（漏畫或特效）
    _write_preview(wd, composite([(rgba, 0, 0)], (w, h))[0], shown, entries)
    status = "needs_parts" if missing_required else "needs_repair" if manual else "ok"
    return {"status": status, "layers": [e["name"] for e, _ in drawable], "written": written,
            "missing_required": missing_required, "needs_manual": manual,
            "recompose_mae": meta["recompose_mae"], "unassigned_ratio": meta["unassigned_ratio"]}


def overrides_dir(wd, doc):
    """人工修補圖的永久位置：正式 parts.json 旁的 <圖名>.overrides/。來源就在工作目錄時才退回 工作目錄/overrides/。"""
    src = Path(doc.get("source", wd / "parts.json")).resolve()
    if src.parent == Path(wd).resolve():
        return Path(wd) / "overrides"
    return src.parent / f"{Path(doc.get('image') or src.name.split('.')[0]).stem}.overrides"


def _unassigned_regions(mask, masks, top=10, min_area=20):
    """未被任何部件涵蓋的前景區塊（最大的幾塊），附上最近的部件，供 Agent 判斷是漏畫還是特效。"""
    n, _, stats, cents = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
    boxes = {k: _bbox(m) for k, m in masks.items() if m.any()}
    out = []
    for i in sorted(range(1, n), key=lambda i: -stats[i, 4])[:top]:
        x, y, w, h, area = (int(v) for v in stats[i])
        if area < min_area:
            break
        cx, cy = cents[i]
        gap = lambda b: max(b[0] - cx, 0, cx - (b[0] + b[2])) ** 2 + max(b[1] - cy, 0, cy - (b[1] + b[3])) ** 2
        near = min(boxes, key=lambda k: gap(boxes[k])) if boxes else None
        out.append({"bbox": [x, y, w, h], "area": area, "nearest_part": near,
                    "distance_px": round(gap(boxes[near]) ** 0.5, 1) if near else None})
    return out


def write_reports(wd):
    """依 metadata.json 重寫 missing_parts.json 與 repair_tasks.md。回傳 (缺少的必要部件, 需人工修補的部件)。"""
    meta = load_json(Path(wd) / "metadata.json")
    entries = meta["parts"]
    names = {e["name"] for e in entries}
    missing_required = [n for n in required_parts(meta.get("preset", "humanoid-chibi"), meta.get("absent", [])) if n not in names]
    manual = [{"name": e["name"], "reason": e["reason"], "hidden_ratio": e.get("hidden_ratio"), "layer": e.get("file")}
              for e in entries if e["status"] == "needs_manual"]
    save_json(Path(wd) / "missing_parts.json", {"missing_required": missing_required, "needs_manual": manual,
                                                "unassigned_ratio": meta["unassigned_ratio"],
                                                "unassigned_regions": meta.get("unassigned_regions", [])})
    _write_repair_tasks(Path(wd), missing_required, manual, entries, meta)
    return missing_required, [m["name"] for m in manual]


def _write_repair_tasks(wd, missing_required, manual, entries, meta):
    lines = ["# 修補任務", "", "由 `c2s prepare` 產生。修完後不需要重新分析，照下方指令接續即可。", ""]
    if missing_required:
        lines += ["## 缺少的必要部件", ""] + [f"- [ ] `{n}`：在 parts.json 補上 polygon 或 mask 後重新執行 `c2s prepare`" for n in missing_required] + [""]
    if meta.get("absent"):
        lines += ["## 畫面上看不到的必要部件（可選擇補畫）", "",
                  "parts.json 宣告這些部件在原圖完全看不到，目前沒有骨頭也沒有動畫。要讓它動，畫好後在 parts.json 加上該部件、"
                  "從 absent 移除，再執行 `c2s run`。", ""] + [f"- [ ] `{n}`" for n in meta["absent"]] + [""]
    if manual:
        lines += ["## 需要人工修補的圖層", ""]
        for m in manual:
            lines += [f"- [ ] `{m['name']}`：{m['reason']}",
                      f"  - 草稿圖層：`{m['layer'] or '（無，需整張重畫）'}`",
                      f"  - 修好後執行：`c2s prepare --replace {m['name']}=<修好的.png>`"
                      f"（PNG 尺寸要等於整張畫布 {meta['canvas'][0]}x{meta['canvas'][1]}，或與草稿圖層相同）"]
        lines.append("")
    auto = [e for e in entries if e["status"] == "auto_repaired"]
    if auto:
        lines += ["## 已自動填補（OpenCV 邊緣延伸）", ""]
        for e in auto:
            note = "可靠" if e.get("repair_reliable", True) else (
                f"**不可靠**（留出誤差 {e.get('holdout_error')}、被遮輪廓 {e.get('contour_hidden')}）"
                + (f"，動畫中露出 {e['exposure']:.1%}（門檻內），建議目視" if e.get("exposure") else "，動畫中沒有露出"))
            lines.append(f"- `{e['name']}`：{note}")
        lines.append("")
    if meta["unassigned_ratio"] > 0.01:
        lines += ["## 未分配像素", "", f"- 有 {meta['unassigned_ratio']:.1%} 的前景像素不屬於任何部件。"
                  "緊貼部件的小區塊多半是漏畫（擴大該部件的 polygon）；遠離角色的多半是特效，可以忽略。", ""]
        lines += [f"- 區塊 x={r['bbox'][0]} y={r['bbox'][1]} 寬={r['bbox'][2]} 高={r['bbox'][3]}，{r['area']} 像素，"
                  f"最近的部件 `{r['nearest_part']}`（距離 {r['distance_px']}px）" for r in meta.get("unassigned_regions", [])] + [""]
    if len(lines) == 4:
        lines.append("目前沒有待處理的修補任務。")
    (wd / "repair_tasks.md").write_text("\n".join(lines), encoding="utf-8")


def _write_preview(wd, source, recomposed, entries):
    """layer_preview.png：原圖 | 圖層重組（洋紅＝未分配像素） | 部件範圍標示。"""
    h, w = source.shape[:2]
    label = Image.fromarray((source * 0.35 + 255 * 0.65).astype(np.uint8))
    draw = ImageDraw.Draw(label)
    palette = [(230, 60, 60), (60, 140, 230), (40, 170, 90), (230, 150, 30), (150, 80, 200), (30, 170, 180), (200, 80, 150)]
    for i, e in enumerate(e for e in entries if "file" in e):
        c = palette[i % len(palette)]
        draw.rectangle([e["x"], e["y"], e["x"] + e["w"] - 1, e["y"] + e["h"] - 1], outline=c, width=2)
        draw.text((e["x"] + 4, e["y"] + 3), f"{e['name']} z{e['z']} {e['status']}", fill=c)
        px, py = e["pivot"]
        draw.ellipse([px - 4, py - 4, px + 4, py + 4], fill=c, outline=(0, 0, 0))
    sheet = Image.new("RGB", (w * 3 + 20, h), (255, 255, 255))
    for i, img in enumerate([Image.fromarray(source.astype(np.uint8)), Image.fromarray(recomposed.astype(np.uint8)), label]):
        sheet.paste(img, (i * (w + 10), 0))
    sheet.save(wd / "layer_preview.png")
