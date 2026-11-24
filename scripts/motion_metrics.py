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
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from character_to_spine import load_json, quality  # noqa: E402
from character_to_spine.animation_builder import duration  # noqa: E402
from character_to_spine.preview import world_matrices  # noqa: E402
from character_to_spine.report import measure as exposure_by_part  # noqa: E402

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
    out["limb_travel"] = limb_travel(wd, skel)
    out["fill_exposure"] = fill_exposure(wd, skel)
    if q:
        worst = q["worst"]
        out["attach_min"] = {k[7:]: v["value"] for k, v in worst.items() if k.startswith("attach:")}
        out["unresolved"] = [f"{a['kind']}:{a['subject']}" for a in q["unresolved"]]
        out["downgraded"] = q["downgraded_to_needs_manual"]
        out["watch"] = q.get("unreliable_exposed_within_threshold", {})
        out["tuning"] = q["tuning"]
    return out


LIMB_ROLES = ("arm", "leg", "hair", "skirt", "prop")


def limb_travel(wd, skel):
    """{部件: {動畫: 比例}}：肢端（圖層上離 pivot 最遠的像素）扣掉 body 骨頭移動後的最大位移 ÷ 角色高度。
    不需要 attach，沒有持物的角色也量得到手臂；全部肢體都接近 0 就是「只剩整個角色上下跳」。"""
    wd = Path(wd)
    meta, rig = load_json(wd / "metadata.json"), load_json(wd / "rig.json")
    ox, oy = meta["origin"]
    setup = world_matrices(skel)
    inv = np.linalg.inv
    frames = {name: [world_matrices(skel, name, i / FPS) for i in range(round(duration(a) * FPS) + 1)]
              for name, a in skel["animations"].items()}
    out = {}
    for e in meta["parts"]:
        n = e["name"]
        if "file" not in e or rig["roles"].get(n) not in LIMB_ROLES:
            continue
        ys, xs = np.nonzero(np.array(Image.open(wd / e["file"]))[..., 3] > 127)
        i = ((xs + e["x"] - e["pivot"][0]) ** 2 + (ys + e["y"] - e["pivot"][1]) ** 2).argmax()
        tip = np.array([xs[i] + e["x"] - ox, oy - (ys[i] + e["y"]), 1.0])
        local, rest = inv(setup[n]) @ tip, inv(setup["body"]) @ tip
        out[n] = {name: round(max(float(np.linalg.norm((inv(w["body"]) @ w[n] @ local - rest)[:2])) for w in ws)
                              / rig["height"], 4) for name, ws in frames.items()}
    return out


def fill_exposure(wd, skel):
    """每個有自動補圖的部件（包含已判為需人工的）：動畫中補圖被看見的最大比例。量法與修補報告相同。"""
    return {p: round(m["ratio"], 4) for p, m in sorted(exposure_by_part(quality._context(wd), skel).items()) if m["px"] > 0}


if __name__ == "__main__":
    for wd in sys.argv[1:]:
        print(json.dumps(measure(wd), ensure_ascii=False))
