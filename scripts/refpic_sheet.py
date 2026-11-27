"""關鍵影格總表：每個案例一列（Idle 1.0s，Happy 0／0.2／0.5／0.7／0.9s），用實際採用的動作（含 tuning）。
草稿露出處另起一列標紅。Python Simulation Preview，不是 Spine 算圖。

python scripts/refpic_sheet.py <output/refpic/標籤> <輸出.png>
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from character_to_spine import load_json  # noqa: E402
from character_to_spine.preview import render, warp_slots  # noqa: E402

FRAMES = [("idle", 1.0), ("happy", 0.0), ("happy", 0.2), ("happy", 0.5), ("happy", 0.7), ("happy", 0.9)]
CELL = 300
SS = 3


def _shrink(rgb):
    return np.array(Image.fromarray(rgb.clip(0, 255).astype(np.uint8)).resize((CELL, CELL), Image.LANCZOS)).astype(float)


def row(wd):
    skel, meta = load_json(wd / "spine" / "character.json"), load_json(wd / "metadata.json")
    bx, by, bw, bh = meta["bbox"]
    pad = int(bh * 0.2)
    big = CELL * SS  # 先放大渲染再縮小：直接縮到 15% 會出現摩爾紋
    s = big / (max(bw, bh) + 2 * pad)
    canvas = (big, big)
    origin = ((meta["origin"][0] - bx - bw / 2) * s + big / 2, (meta["origin"][1] - by + pad) * s)
    plain, marked = [], []
    for anim, t in FRAMES:
        rgb = render(skel, wd / "spine" / "images", canvas, origin, anim, t, s, {})[0]
        through, mark = np.ones(rgb.shape[:2]), np.zeros(rgb.shape[:2])
        for _, wp, m in reversed(list(warp_slots(skel, wd / "spine" / "images", canvas, origin, anim, t, s, {}, wd / "repair_masks"))):
            a = wp[..., 3] / 255
            if m is not None:
                mark = np.maximum(mark, m * a * through)
            through *= 1 - a
        red = rgb.copy()
        red[mark > 0.3] = red[mark > 0.3] * 0.4 + np.array([255, 0, 0]) * 0.6
        plain.append(_shrink(rgb))
        marked.append(_shrink(red))
    return np.hstack(plain), np.hstack(marked)


def main(root, out):
    cases = [d for d in sorted(Path(root).iterdir()) if (d / "output").exists()]
    rows = []
    for c in cases:
        wd = next(d for d in (c / "output").iterdir() if d.is_dir())
        if not (wd / "spine" / "character.json").exists():
            continue
        p, m = row(wd)
        for arr, tag in ((p, ""), (m, "（紅＝草稿露出）")):
            im = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
            ImageDraw.Draw(im).text((4, 4), f"{c.name} {tag}".encode("ascii", "ignore").decode() + ("  [red=draft]" if tag else ""), fill=(200, 0, 0))
            rows.append(im)
    head = Image.new("RGB", (CELL * len(FRAMES), 20), "white")
    ImageDraw.Draw(head).text((4, 4), "Python Simulation Preview | " + " | ".join(f"{a} {t}s" for a, t in FRAMES), fill=(0, 0, 0))
    sheet = Image.new("RGB", (CELL * len(FRAMES), 20 + CELL * len(rows)), "white")
    sheet.paste(head, (0, 0))
    for i, r in enumerate(rows):
        sheet.paste(r, (0, 20 + i * CELL))
    sheet.save(out)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
