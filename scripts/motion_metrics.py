"""手臂動作量與品質閘門，給動畫優化做前後比較。

python scripts/motion_metrics.py <工作目錄> [...]

每個 attach 接觸點跟著各自的骨頭移動，扣掉身體（body 骨頭）本身的移動後，量它相對原位的最大位移（原圖像素）。
這是觀眾看到的「手在動」：整個角色一起跳不算，手相對身體揮動才算。
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from character_to_spine import load_json, quality  # noqa: E402
from character_to_spine.animation_builder import duration  # noqa: E402
from character_to_spine.preview import world_matrices  # noqa: E402
from visual_report import measure as exposure_by_part  # noqa: E402

FPS = 30


def measure(wd):
    wd = Path(wd)
    skel = load_json(wd / "spine" / "character.json")
    rig = load_json(wd / "rig.json")
    q = load_json(wd / "quality" / "quality_report.json") if (wd / "quality" / "quality_report.json").exists() else None
    setup = world_matrices(skel)
    out = {"workdir": wd.name, "travel_px": {}, "path_px_per_s": {}, "peak_rotation_deg": {}}
    anim = skel["animations"]["happy"]
    for c in rig.get("contacts", []):
        p0 = np.array([*c["point"], 1.0])
        for bone in (c["a"], c["b"]):
            local = np.linalg.inv(setup[bone]) @ p0
            rest = np.linalg.inv(setup["body"]) @ p0
            travel = path = 0.0
            prev = rest
            for i in range(round(duration(anim) * FPS) + 1):
                w = world_matrices(skel, "happy", i / FPS)
                pos = np.linalg.inv(w["body"]) @ w[bone] @ local
                travel = max(travel, float(np.linalg.norm((pos - rest)[:2])))
                path += float(np.linalg.norm((pos - prev)[:2]))  # 手實際走過的路徑：同樣幅度、動得越頻繁越長
                prev = pos
            key = f"{bone}@{c['a']}+{c['b']}"
            out["travel_px"][key] = round(travel, 1)
            out["path_px_per_s"][key] = round(path / duration(anim), 1)
    for bone, tls in anim["bones"].items():
        if "rotate" in tls and rig["roles"].get(bone) in ("arm", "prop"):
            out["peak_rotation_deg"][bone] = round(max(abs(k.get("value", 0)) for k in tls["rotate"]), 2)
    out["fill_exposure"] = fill_exposure(wd, skel)
    if q:
        worst = q["rounds"][q["chosen_round"]]["worst"]
        out["attach_min"] = {k[7:]: v["value"] for k, v in worst.items() if k.startswith("attach:")}
        out["unresolved"] = [f"{a['kind']}:{a['subject']}" for a in q["unresolved"]]
        out["downgraded"] = q["downgraded_to_needs_manual"]
        out["watch"] = q.get("unreliable_exposed_within_threshold", {})
        out["tuning"] = q["tuning"]
    return out


def fill_exposure(wd, skel):
    """每個有自動補圖的部件（包含已判為需人工的）：動畫中補圖被看見的最大比例。量法與修補報告相同。"""
    return {p: round(m["ratio"], 4) for p, m in sorted(exposure_by_part(quality._context(wd), skel).items()) if m["px"] > 0}


if __name__ == "__main__":
    for wd in sys.argv[1:]:
        print(json.dumps(measure(wd), ensure_ascii=False))
