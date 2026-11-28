"""用目前的 fusion 重新量測已保存的生成圖（不寫任何檔案）。量測方法修改後，用來比較新舊數值。

python scripts/rejudge.py <工作目錄> <部件> <生成圖>...
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from character_to_spine import load_json  # noqa: E402
from character_to_spine.fusion import fuse, judge  # noqa: E402
from character_to_spine.image_processor import part_mask  # noqa: E402

wd, part, gens = Path(sys.argv[1]), sys.argv[2], sys.argv[3:]
src = np.array(Image.open(wd / "source_rgba.png"))
h, w = src.shape[:2]
doc = load_json(wd / "parts.json")
z = {p["name"]: p["z"] for p in doc["parts"]}
masks = {p["name"]: part_mask(p, (h, w)) for p in doc["parts"]}
above = np.zeros((h, w), bool)
for n, m in masks.items():
    if z[n] > z[part]:
        above |= m
for g in gens:
    _, m = fuse(src, masks[part], above, np.array(Image.open(g).convert("RGBA")))
    print(json.dumps({"file": g, "metrics": m, "reasons": judge(m)}, ensure_ascii=False))
