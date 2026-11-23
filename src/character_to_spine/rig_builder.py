"""由圖層 metadata 建立骨架。座標一律從 metadata 推算，沒有任何寫死的角色座標。"""
import math
from pathlib import Path

import numpy as np
from PIL import Image

from . import C2SError, NeedsInput, load_json, save_json

PRESETS = {
    "humanoid-chibi": {
        # 骨頭: 父骨頭（順序即建立順序）。hip 是虛擬骨頭，位置取 body 的 pivot。
        "bones": {"hip": "root", "body": "hip", "head": "body", "arm_l": "body", "arm_r": "body",
                  "leg_l": "hip", "leg_r": "hip"},
        "required": ["head", "body", "arm_l", "arm_r", "leg_l", "leg_r"],
        # 預設關節位置：圖層外框內的比例 (fx, fy)，y 向下。_l/_r 指畫面左／右。parts.json 的 pivot 可覆寫。
        "anchors": {"body": (0.5, 0.95), "head": (0.5, 0.9), "arm_l": (0.8, 0.12), "arm_r": (0.2, 0.12),
                    "leg_l": (0.5, 0.08), "leg_r": (0.5, 0.08)},
    },
}
# 動畫依 role 決定套用哪一組動作；必要部件的 role 由名稱推得，其餘部件預設 accessory
ROLES = ("head", "body", "arm", "leg", "hair", "skirt", "prop", "accessory")
RESERVED_BONES = ("root", "hip")


def default_role(name):
    base = name.rsplit("_", 1)[0] if name.endswith(("_l", "_r")) else name
    return base if base in ("head", "body", "arm", "leg") else "accessory"


def _rot(vec, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return vec[0] * c - vec[1] * s, vec[0] * s + vec[1] * c


def build_rig(workdir, preset=None):
    wd = Path(workdir)
    if not (wd / "metadata.json").exists():
        raise NeedsInput(f"{wd} 尚未切圖，請先執行 c2s prepare")
    meta = load_json(wd / "metadata.json")
    preset_name = preset or meta.get("preset", "humanoid-chibi")
    if preset_name not in PRESETS:
        raise C2SError(f"未知的 preset：{preset_name}")
    cfg = PRESETS[preset_name]
    parts = {e["name"]: e for e in meta["parts"] if "file" in e}
    missing = [n for n in cfg["required"] if n not in parts]
    if missing:
        raise NeedsInput("無法綁定骨架，缺少必要部件的圖層：" + ", ".join(missing) + f"。請依 {wd / 'repair_tasks.md'} 補齊後重新執行 c2s prepare")

    ox, oy = meta["origin"]
    world = lambda px, py: (px - ox, oy - py)  # 原圖像素（y 向下）→ Spine 世界座標（y 向上，原點在腳底）

    parents = dict(cfg["bones"])
    for name, e in parts.items():
        if name not in parents:
            parents[name] = e.get("parent") or "body"
    all_parts = {e["name"] for e in meta["parts"]}
    for name, parent in parents.items():
        if parent == "root" or parent in parents:
            continue
        if parent in all_parts:
            raise NeedsInput(f"部件 {name} 的 parent {parent} 還沒有圖層，請依 {wd / 'repair_tasks.md'} 補上後重新執行 c2s prepare")
        raise C2SError(f"部件 {name} 的 parent {parent!r} 不存在")

    pose = {"root": (0.0, 0.0, 0.0), "hip": (*world(*parts["body"]["pivot"]), 0.0)}  # 名稱: (世界 x, y, 旋轉)
    length = {}
    for name, e in parts.items():
        alpha = np.array(Image.open(wd / e["file"]))[..., 3] > 8
        ys, xs = np.nonzero(alpha)
        pos = world(*e["pivot"])
        cx, cy = world(e["x"] + xs.mean(), e["y"] + ys.mean())
        dist = math.hypot(cx - pos[0], cy - pos[1])
        # 骨頭從關節指向圖層重心，在 Spine 裡看起來才會順著肢體
        pose[name] = (*pos, math.degrees(math.atan2(cy - pos[1], cx - pos[0])) if dist >= 2 else 0.0)
        length[name] = round(dist * 2, 1)

    bones, placed, pending = [{"name": "root"}], {"root"}, [n for n in parents if n in pose]
    while pending:
        ready = [n for n in pending if parents[n] in placed]
        if not ready:
            raise C2SError("骨架 parent 關係有循環：" + ", ".join(pending))
        for n in ready:
            px, py, prot = pose[parents[n]]
            x, y, rot = pose[n]
            lx, ly = _rot((x - px, y - py), -prot)
            bones.append({"name": n, "parent": parents[n], "x": round(lx, 2), "y": round(ly, 2),
                          "rotation": round(rot - prot, 2), "length": length.get(n, 0),
                          "world": [round(x, 2), round(y, 2), round(rot, 2)]})
            placed.add(n)
            pending.remove(n)

    attachments = {}
    for name, e in parts.items():
        x, y, rot = pose[name]
        cx, cy = world(e["x"] + e["w"] / 2, e["y"] + e["h"] / 2)
        lx, ly = _rot((cx - x, cy - y), -rot)
        attachments[name] = {"x": round(lx, 2), "y": round(ly, 2), "rotation": round(-rot, 2),
                             "width": e["w"], "height": e["h"]}
    slots = [{"name": e["name"], "bone": e["name"], "attachment": e["name"]}
             for e in sorted(parts.values(), key=lambda e: e["z"])]  # 由後到前
    rig = {"preset": preset_name, "height": meta["bbox"][3], "bbox": meta["bbox"], "origin": meta["origin"],
           "bones": bones, "slots": slots, "attachments": attachments,
           "roles": {n: e.get("role") or default_role(n) for n, e in parts.items()},
           "motion": {n: e.get("motion", 1.0) for n, e in parts.items()}}
    save_json(wd / "rig.json", rig)
    return {"status": "ok", "bones": [b["name"] for b in bones], "slots": [s["name"] for s in slots]}
