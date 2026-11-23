"""依 parts.json 把角色切成透明分層 PNG，並誠實回報被遮擋／需要人工修補的部分。"""
import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from . import C2SError, NeedsInput, load_json, save_json
from .analyzer import ALPHA_MIN
from .providers import REPAIR_PROVIDERS
from .rig_builder import PRESETS

# 被遮住的面積超過部件的這個比例，就不把自動填補當成完成，改列人工修補任務
MAX_AUTO_HIDDEN_RATIO = 0.35


def part_mask(part, shape):
    if "mask" in part:
        return np.array(Image.open(part["mask"]).convert("L")) > 127
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [np.array(part["polygon"], np.int32)], 1)
    return m.astype(bool)


def _bbox(mask):
    ys, xs = np.nonzero(mask)
    return int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)


def _cut(part, rgba, masks, parts, repair):
    """回傳 (RGBA 圖層, metadata 條目)。圖層已裁切到自身範圍。"""
    fg = rgba[..., 3] > ALPHA_MIN
    above = np.zeros(fg.shape, bool)
    for other in parts:
        if other["z"] > part["z"]:
            above |= masks[other["name"]]
    mine = masks[part["name"]] & fg
    visible, hidden = mine & ~above, mine & above
    entry = {"name": part["name"], "z": part["z"], "parent": part.get("parent"),
             "role": part.get("role"), "motion": part.get("motion", 1.0)}
    if not visible.any():
        entry.update(status="needs_manual", reason="完全被其他部件遮住或範圍內沒有前景，無法自動產生")
        return None, entry
    x, y, w, h = _bbox(mine)
    crop = rgba[y:y + h, x:x + w].copy()
    vis, hid = visible[y:y + h, x:x + w], hidden[y:y + h, x:x + w]
    solid = vis & (crop[..., 3] > 200)  # 半透明的邊緣像素混了背景色，不拿來當修補來源
    crop[..., 3] = np.where(vis, crop[..., 3], 0)
    ratio = hidden.sum() / mine.sum()
    if hid.any():
        # 只用這個部件自己看得見的像素往被遮住的區域延伸，避免染到別的部件的顏色
        crop[..., :3] = repair(crop[..., :3], ~solid)
        crop[..., 3] = np.where(hid, 255, crop[..., 3])
        if ratio > MAX_AUTO_HIDDEN_RATIO:
            entry.update(status="needs_manual", reason=f"被遮擋面積 {ratio:.0%} 超過自動修補上限 "
                         f"{MAX_AUTO_HIDDEN_RATIO:.0%}，目前的填補只是草稿")
        else:
            entry["status"] = "auto_repaired"
    else:
        entry["status"] = "ok"
    entry.update(x=x, y=y, w=w, h=h, hidden_ratio=round(float(ratio), 4))
    return crop, entry


def _apply_override(path, entry, canvas_size):
    """人工修好的圖層：可以是整張畫布大小（保留原座標），或與自動圖層相同大小。"""
    img = Image.open(path).convert("RGBA")
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
    only：強制重寫這個部件的圖層；replace：{部件名: 人工修好的 PNG}，驗證通過才保存到 overrides/。"""
    wd = Path(workdir)
    if not (wd / "source_rgba.png").exists() or not (wd / "parts.json").exists():
        raise NeedsInput(f"{wd} 尚未完成分析或缺少 parts.json，請先執行 c2s analyze 並補上 parts.json")
    rgba = np.array(Image.open(wd / "source_rgba.png"))
    h, w = rgba.shape[:2]
    doc = load_json(wd / "parts.json")
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
    repair = REPAIR_PROVIDERS["opencv"]
    results = []  # (entry, layer 或 None)
    for p in parts:
        name = p["name"]
        layer, entry = _cut(p, rgba, masks, parts, repair)
        override = replace.get(name) or wd / "overrides" / f"{name}.png"
        if override.exists():
            layer = _apply_override(override, entry, (w, h))  # 尺寸不對會在寫入任何檔案前就失敗
        if layer is not None:
            entry["file"] = f"layers/{name}.png"
            fx, fy = preset["anchors"].get(name, (0.5, 0.5))
            entry["pivot"] = p.get("pivot") or [round(entry["x"] + fx * entry["w"], 1), round(entry["y"] + fy * entry["h"], 1)]
        results.append((entry, layer))

    (wd / "layers").mkdir(exist_ok=True)
    written = []
    for entry, layer in results:
        if layer is None:
            continue
        path = wd / entry["file"]
        if entry["name"] == only or not _same_png(path, layer):
            Image.fromarray(layer).save(path)
            written.append(entry["name"])
    for name, src in replace.items():
        (wd / "overrides").mkdir(exist_ok=True)
        shutil.copyfile(src, wd / "overrides" / f"{name}.png")
    entries = [e for e, _ in results]

    assigned = np.zeros((h, w), bool)
    for m in masks.values():
        assigned |= m
    fg = rgba[..., 3] > ALPHA_MIN
    body = fg & assigned  # 只算部件範圍內的像素：散落的特效不影響骨架原點與尺寸
    if not body.any():
        raise C2SError("parts.json 的範圍內沒有任何前景像素，請檢查座標")
    ys, xs = np.nonzero(body)
    drawable = [(e, layer) for e, layer in results if layer is not None]
    recomposed = composite([(layer, e["x"], e["y"]) for e, layer in drawable], (w, h))
    source_rgba = rgba.copy()
    source_rgba[..., 3] = np.where(assigned, source_rgba[..., 3], 0)
    source = composite([(source_rgba, 0, 0)], (w, h))
    meta = {
        "image": doc.get("image"), "canvas": [w, h], "preset": doc.get("preset", "humanoid-chibi"),
        "bbox": [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)],
        # 骨架原點：角色腳底中央（原圖像素座標）
        "origin": [round(float(xs.min() + xs.max()) / 2, 1), int(ys.max()) + 1],
        "unassigned_ratio": round(float((fg & ~assigned).sum() / fg.sum()), 4),
        "recompose_mae": round(masked_mae(recomposed, source), 5),
        "parts": entries,
    }
    save_json(wd / "metadata.json", meta)

    missing_required = [n for n in preset["required"] if n not in names]
    manual = [{"name": e["name"], "reason": e["reason"], "hidden_ratio": e.get("hidden_ratio"), "layer": e.get("file")}
              for e in entries if e["status"] == "needs_manual"]
    save_json(wd / "missing_parts.json", {"missing_required": missing_required, "needs_manual": manual,
                                          "unassigned_ratio": meta["unassigned_ratio"]})
    _write_repair_tasks(wd, missing_required, manual, entries, meta)
    _write_preview(wd, composite([(rgba, 0, 0)], (w, h))[0], recomposed[0], entries)
    status = "needs_parts" if missing_required else "needs_repair" if manual else "ok"
    return {"status": status, "layers": [e["name"] for e, _ in drawable], "written": written,
            "missing_required": missing_required, "needs_manual": [m["name"] for m in manual],
            "recompose_mae": meta["recompose_mae"], "unassigned_ratio": meta["unassigned_ratio"]}


def _write_repair_tasks(wd, missing_required, manual, entries, meta):
    lines = ["# 修補任務", "", "由 `c2s prepare` 產生。修完後不需要重新分析，照下方指令接續即可。", ""]
    if missing_required:
        lines += ["## 缺少的必要部件", ""] + [f"- [ ] `{n}`：在 parts.json 補上 polygon 或 mask 後重新執行 `c2s prepare`" for n in missing_required] + [""]
    if manual:
        lines += ["## 需要人工修補的圖層", ""]
        for m in manual:
            lines += [f"- [ ] `{m['name']}`：{m['reason']}",
                      f"  - 草稿圖層：`{m['layer'] or '（無，需整張重畫）'}`",
                      f"  - 修好後執行：`c2s prepare --replace {m['name']}=<修好的.png>`"
                      f"（PNG 尺寸要等於整張畫布 {meta['canvas'][0]}x{meta['canvas'][1]}，或與草稿圖層相同）"]
        lines.append("")
    auto = [e["name"] for e in entries if e["status"] == "auto_repaired"]
    if auto:
        lines += ["## 已自動填補（OpenCV 邊緣延伸，品質有限，建議目視檢查）", ""] + [f"- `{n}`" for n in auto] + [""]
    if meta["unassigned_ratio"] > 0.01:
        lines += ["## 未分配像素", "", f"- 有 {meta['unassigned_ratio']:.1%} 的前景像素不屬於任何部件，請檢查 parts.json 的範圍是否漏畫。", ""]
    if len(lines) == 4:
        lines.append("目前沒有待處理的修補任務。")
    (wd / "repair_tasks.md").write_text("\n".join(lines), encoding="utf-8")


def _write_preview(wd, source, recomposed, entries):
    """layer_preview.png：原圖 | 圖層重組 | 部件範圍標示。"""
    h, w = source.shape[:2]
    label = Image.fromarray((recomposed * 0.35 + 255 * 0.65).astype(np.uint8))
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
