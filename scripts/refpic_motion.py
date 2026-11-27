"""Happy 實際動作量：每個案例手臂、身體、腿的最大轉角（度），以及 hip 跳躍高度（角色高度的比例）。

python scripts/refpic_motion.py <工作目錄的上層：output/refpic/<標籤> 或沙盒前綴 v10_>
"""
import json
import sys
import tempfile
from pathlib import Path


def peaks(wd):
    a = json.loads((wd / "animations.json").read_text(encoding="utf-8"))["happy"]["bones"]
    rig = json.loads((wd / "rig.json").read_text(encoding="utf-8"))
    roles = rig["roles"]
    rot = lambda b: max((abs(k.get("value", 0)) for k in a.get(b, {}).get("rotate", [])), default=0.0)
    out = {r: round(max((rot(b) for b, x in roles.items() if x == r), default=0.0), 1) for r in ("arm", "leg")}
    out["arm_min"] = round(min((rot(b) for b, x in roles.items() if x == "arm"), default=0.0), 1)
    out["body"] = rot("body")
    out["jump"] = round(max(k.get("y", 0) for k in a["hip"]["translate"]) / rig["height"], 3)
    return out


def main(arg):
    p = Path(arg)
    boxes = sorted(p.iterdir()) if p.is_dir() else sorted((Path(tempfile.gettempdir()) / "c2s_acceptance").glob(arg + "*"))
    rows = {}
    for b in boxes:
        wd = next((d for d in (b / "output").iterdir() if d.is_dir() and (d / "animations.json").exists()), None) \
            if (b / "output").exists() else None
        if wd:
            rows[b.name.split("_", 1)[-1] if not p.is_dir() else b.name] = peaks(wd)
    for k, v in rows.items():
        print(f"{k:<16} {v}")
    return rows


if __name__ == "__main__":
    main(sys.argv[1])
