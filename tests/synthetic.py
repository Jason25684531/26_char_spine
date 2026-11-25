"""合成 Q 版角色：每個部件的真實範圍已知，供回歸測試使用。

python tests/synthetic.py <輸出目錄>   產生兩個角色到指定目錄
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def circle(cx, cy, r, n=32):
    return [[round(cx + r * math.cos(2 * math.pi * i / n)), round(cy + r * math.sin(2 * math.pi * i / n))] for i in range(n)]


# 名稱: (多邊形, 顏色, z, 其他 parts.json 欄位)
CHARACTERS = {
    "synth_a": {
        "size": (300, 420), "background": None, "use_masks": True,
        "parts": {
            "leg_l": (rect(115, 280, 143, 390), (60, 80, 160), 1, {}),
            "leg_r": (rect(157, 280, 185, 390), (70, 90, 175), 2, {}),
            "body": (rect(105, 175, 195, 300), (220, 80, 80), 3, {}),
            "head": (circle(150, 115, 62), (250, 220, 190), 4, {}),
            "arm_l": (rect(72, 180, 110, 280), (235, 185, 145), 5, {}),
            "arm_r": (rect(190, 180, 228, 280), (240, 195, 155), 6, {}),
        },
    },
    "synth_b": {
        "size": (420, 360), "background": (200, 230, 200), "use_masks": False,
        "parts": {
            "hair_back": (circle(200, 110, 85), (90, 50, 30), 0, {"parent": "head", "role": "hair"}),
            "leg_l": (rect(165, 270, 195, 340), (50, 50, 60), 1, {}),
            "leg_r": (rect(215, 270, 245, 340), (55, 55, 70), 2, {}),
            "body": (rect(150, 190, 260, 290), (80, 120, 200), 3, {}),
            "head": (circle(205, 115, 70), (250, 215, 180), 4, {}),
            "arm_l": (rect(110, 195, 152, 265), (240, 200, 170), 5, {}),
            "arm_r": (rect(258, 195, 300, 265), (235, 195, 160), 6, {}),
            "flag": ([[290, 110], [345, 130], [298, 150], [298, 270], [290, 270]], (250, 200, 40), 7,
                     {"parent": "arm_r", "role": "prop"}),
        },
    },
}


def truth_bbox(polygon):
    xs, ys = [p[0] for p in polygon], [p[1] for p in polygon]
    return [min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1]


def make(name, out_dir):
    """寫出 <name>.png、<name>.parts.json（遮罩在 <name>_masks/），回傳 (圖片路徑, {部件: 真實 bbox})。"""
    spec = CHARACTERS[name]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    w, h = spec["size"]
    bg = spec["background"]
    img = Image.new("RGBA", (w, h), (*bg, 255) if bg else (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    entries = []
    for part, (poly, color, z, extra) in sorted(spec["parts"].items(), key=lambda kv: kv[1][2]):
        draw.polygon([tuple(p) for p in poly], fill=(*color, 255))
        entry = {"name": part, "z": z, **extra}
        if spec["use_masks"]:
            mask = Image.new("L", (w, h), 0)
            ImageDraw.Draw(mask).polygon([tuple(p) for p in poly], fill=255)
            (out / f"{name}_masks").mkdir(exist_ok=True)
            mask.save(out / f"{name}_masks" / f"{part}.png")
            entry["mask"] = f"{name}_masks/{part}.png"
        else:
            entry["polygon"] = poly
        entries.append(entry)
        if part == "head":  # 眼睛：讓頭部不是單一色塊
            cx = sum(p[0] for p in poly) / len(poly)
            cy = sum(p[1] for p in poly) / len(poly)
            for dx in (-20, 20):
                draw.ellipse([cx + dx - 6, cy - 6, cx + dx + 6, cy + 6], fill=(40, 30, 30, 255))
    image_path = out / f"{name}.png"
    img.save(image_path)
    (out / f"{name}.parts.json").write_text(json.dumps(
        {"version": 1, "image": image_path.name, "preset": "humanoid-chibi", "parts": entries}, indent=2), encoding="utf-8")
    return image_path, {p: truth_bbox(v[0]) for p, v in spec["parts"].items()}


def make_custom(out_dir, name, size, parts):
    """parts：[(名稱, 多邊形, 顏色或 "stripes", z, 其他欄位)]。由後往前畫，寫出 <name>.png 與 <name>.parts.json。"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    w, h = size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for part, poly, color, z, extra in sorted(parts, key=lambda p: p[3]):
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).polygon([tuple(p) for p in poly], fill=255)
        if color == "stripes":  # 高對比細條紋：邊緣延伸補不回來
            fill = Image.new("RGBA", (w, h))
            d = ImageDraw.Draw(fill)
            for x in range(0, w, 6):
                d.rectangle([x, 0, x + 2, h], fill=(20, 20, 20, 255))
                d.rectangle([x + 3, 0, x + 5, h], fill=(240, 240, 240, 255))
        else:
            fill = Image.new("RGBA", (w, h), (*color, 255))
        img.paste(fill, (0, 0), mask)
    path = out / f"{name}.png"
    img.save(path)
    (out / f"{name}.parts.json").write_text(json.dumps({"version": 1, "parts": [
        {"name": n, "polygon": poly, "z": z, **extra} for n, poly, _, z, extra in parts]}), encoding="utf-8")
    return path


if __name__ == "__main__":
    for n in CHARACTERS:
        print(make(n, sys.argv[1] if len(sys.argv) > 1 else "examples/synthetic")[0])
