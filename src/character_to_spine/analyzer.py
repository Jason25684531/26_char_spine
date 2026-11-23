"""圖片讀取、去背與 parts.json 檢查。語意辨識（哪裡是頭、手）不在這裡：由 Skill 層的 Agent 寫出 parts.json。"""
from pathlib import Path

import math

import cv2
import numpy as np
from PIL import Image, ImageDraw

from . import C2SError, load_json, save_json
from .rig_builder import PRESETS, RESERVED_BONES, ROLES

ALPHA_MIN = 8  # alpha 低於此值視為背景


def load_rgba(image_path):
    """回傳 (HxWx4 uint8, alpha 來源)。沒有透明度的圖片用邊界 flood fill 去背。"""
    rgba = np.array(Image.open(image_path).convert("RGBA"))
    if rgba[..., 3].min() < 255:
        return rgba, "embedded"
    rgba[..., 3] = _flood_alpha(rgba[..., :3])
    return rgba, "flood-fill"


def _flood_alpha(rgb, tol=14):
    # ponytail: 只處理接近純色的背景；漸層或複雜背景請改用外部遮罩（parts.json 的 mask）。
    h, w = rgb.shape[:2]
    img = rgb.copy()  # 必須是獨立的連續記憶體；ascontiguousarray 對 1x1 切片會回傳 OpenCV 不接受的 view
    border = np.concatenate([img[0], img[-1], img[:, 0], img[:, -1]]).astype(int)
    bg = np.median(border, axis=0)
    mask = np.zeros((h + 2, w + 2), np.uint8)
    flags = 4 | cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE | (255 << 8)
    seeds = [(x, y) for x in range(0, w, 8) for y in (0, h - 1)] + [(x, y) for y in range(0, h, 8) for x in (0, w - 1)]
    for x, y in seeds:
        if mask[y + 1, x + 1] == 0 and np.abs(img[y, x].astype(int) - bg).max() <= tol * 2:
            cv2.floodFill(img, mask, (x, y), 0, (tol,) * 3, (tol,) * 3, flags)
    return np.where(mask[1:-1, 1:-1] > 0, 0, 255).astype(np.uint8)


def _grid_overlay(rgba, step=50):
    """原圖疊上標了像素座標的格線，讓看圖寫 parts.json 的 Agent 或人能讀出座標。"""
    h, w = rgba.shape[:2]
    a = rgba[..., 3:4].astype(float) / 255
    img = Image.fromarray((rgba[..., :3] * a + 255 * (1 - a)).astype(np.uint8))
    draw = ImageDraw.Draw(img)
    for x in range(0, w, step):
        draw.line([(x, 0), (x, h)], fill=(0, 160, 255) if x % (step * 2) else (255, 0, 120), width=1)
        draw.text((x + 2, 2), str(x), fill=(255, 0, 120))
    for y in range(0, h, step):
        draw.line([(0, y), (w, y)], fill=(0, 160, 255) if y % (step * 2) else (255, 0, 120), width=1)
        draw.text((2, y + 2), str(y), fill=(255, 0, 120))
    return img


def _num(n):
    return isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n)


def _is_point(v, size):
    """[x, y] 有限數字，且在原圖周圍一倍範圍內（允許稍微超出圖片邊緣，擋掉誤植的極端值）。"""
    w, h = size
    return (isinstance(v, (list, tuple)) and len(v) == 2 and all(_num(n) for n in v)
            and -w <= v[0] <= 2 * w and -h <= v[1] <= 2 * h)


def check_parts(parts_doc, size, base_dir):
    """回傳 (正規化後的 parts 清單, 錯誤訊息清單)。mask 路徑會轉成絕對路徑。"""
    errors, out, seen, zs = [], [], set(), {}
    w, h = size
    if not isinstance(parts_doc, dict) or not isinstance(parts_doc.get("parts"), list):
        return [], ["parts.json 必須是含有 parts 陣列的物件：{\"parts\": [...]}"]
    for i, p in enumerate(parts_doc["parts"]):
        if not isinstance(p, dict):
            errors.append(f"parts[{i}]: 每個部件必須是物件，收到 {p!r}")
            continue
        name = p.get("name", "")
        if not isinstance(name, str) or not name or not name.replace("_", "").isalnum() or not name.isascii():
            errors.append(f"parts[{i}]: name 必須是英數字與底線，收到 {name!r}")
            continue
        if name in seen:
            errors.append(f"{name}: 名稱重複")
            continue
        if name in RESERVED_BONES:
            errors.append(f"{name}: 這是骨架保留名稱，請改用其他名稱")
            continue
        seen.add(name)
        q = dict(p)
        z = p.get("z")
        if _num(z):
            if z in zs:
                errors.append(f"{name}: z={z} 與 {zs[z]} 相同，前後順序必須唯一")
            zs[z] = name
        else:
            errors.append(f"{name}: 需要數字 z（越大越前面）")
        if "role" in p and p["role"] not in ROLES:
            errors.append(f"{name}: role {p['role']!r} 不支援（可用：{', '.join(ROLES)}）")
        if "motion" in p and (not _num(p["motion"]) or p["motion"] < 0):
            errors.append(f"{name}: motion 必須是 >= 0 的數字")
        if p.get("pivot") is not None and not _is_point(p["pivot"], size):
            errors.append(f"{name}: pivot 必須是圖片範圍附近的 [x, y]")
        if "mask" in p:
            m = Path(p["mask"])
            m = m if m.is_absolute() else Path(base_dir) / m
            if not m.exists():
                errors.append(f"{name}: 找不到遮罩 {m}")
            elif Image.open(m).size != (w, h):
                errors.append(f"{name}: 遮罩尺寸 {Image.open(m).size} 與原圖 {(w, h)} 不同")
            q["mask"] = str(m.resolve())
        else:
            poly = p.get("polygon")
            if not isinstance(poly, list) or len(poly) < 3 or not all(_is_point(v, size) for v in poly):
                errors.append(f"{name}: 需要 polygon（至少 3 個 [x, y] 點，座標在圖片範圍附近）或 mask")
            elif max(v[0] for v in poly) < 0 or min(v[0] for v in poly) >= w or max(v[1] for v in poly) < 0 or min(v[1] for v in poly) >= h:
                errors.append(f"{name}: polygon 完全在圖片範圍外（圖片 {w}x{h}）")
        out.append(q)
    return out, errors


def analyze(image, workdir, parts_path=None, preset="humanoid-chibi"):
    image, wd = Path(image), Path(workdir)
    if not image.exists():
        raise C2SError(f"找不到圖片：{image}")
    if preset not in PRESETS:
        raise C2SError(f"未知的 preset：{preset}（可用：{', '.join(PRESETS)}）")
    wd.mkdir(parents=True, exist_ok=True)
    rgba, alpha_source = load_rgba(image)
    fg = rgba[..., 3] > ALPHA_MIN
    if not fg.any():
        raise C2SError("圖片沒有前景像素")
    Image.fromarray(rgba).save(wd / "source_rgba.png")  # 工作複本，原圖不動
    _grid_overlay(rgba).save(wd / "grid_overlay.png")
    ys, xs = np.nonzero(fg)
    h, w = fg.shape
    required = PRESETS[preset]["required"]
    result = {
        "image": str(image.resolve()),
        "size": [w, h],
        "alpha_source": alpha_source,
        "bbox": [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)],
        "foreground_ratio": round(float(fg.mean()), 4),
        "components": int(cv2.connectedComponents(fg.astype(np.uint8))[0] - 1),
        "preset": preset,
    }

    # 工作目錄內的 parts.json 優先：那是使用者被告知要修改的檔案，不能被圖片旁的原始版本蓋掉
    candidates = [Path(parts_path)] if parts_path else [wd / "parts.json", image.with_suffix(".parts.json")]
    if parts_path and not Path(parts_path).exists():
        raise C2SError(f"找不到 parts 檔：{parts_path}")
    found = next((c for c in candidates if c.exists()), None)
    names, errors = [], []
    if found:
        try:
            doc = load_json(found)
        except (ValueError, UnicodeDecodeError) as e:  # JSONDecodeError 是 ValueError
            doc, errors = None, [f"{found.name} 不是合法的 JSON：{e}"]
        parts, errors = check_parts(doc, (w, h), found.parent) if doc is not None else ([], errors)
        names = [p["name"] for p in parts]
        if not errors:
            save_json(wd / "parts.json", {"version": 1, "image": image.name, "preset": preset, "parts": parts})
    else:
        save_json(wd / "parts.template.json", {
            "version": 1, "image": image.name, "preset": preset,
            "_說明": "座標為原圖像素（左上為原點）。polygon 要包含被其他部件遮住的範圍；z 越大越前面；"
                    "_l/_r 指畫面左／右；pivot、parent 可省略。完成後存成 parts.json 再執行 c2s prepare。",
            "parts": [{"name": n, "polygon": [], "z": i, "pivot": None} for i, n in enumerate(required)],
        })
    missing = [n for n in required if n not in names]
    result.update(parts_file=str(found) if found else None, parts=names, parts_errors=errors, missing_required=missing)
    result["status"] = "ok" if found and not errors and not missing else "needs_parts"
    if result["status"] != "ok":
        result["next_steps"] = [
            f"由 Agent（Skill）或人工檢視圖片後撰寫 {wd / 'parts.json'}（範本：parts.template.json）",
            "必要部件：" + ", ".join(required),
            f"完成後執行：c2s prepare \"{image}\"",
        ]
    save_json(wd / "analysis.json", result)
    return result
