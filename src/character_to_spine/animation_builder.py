"""動畫模板 → Spine 關鍵影格。可在 Spine 內逐格修改。

模板依骨頭的 role 查表。數值是「motion = 1 時」的幅度：
旋轉為角度，位移為角色高度的比例；s 是肢體在身體哪一側（畫面左 -1、右 +1，讓旋轉朝外），
a 是第幾次循環的方向（+1／-1，讓左右交替）。實際幅度再乘上每根骨頭的 motion 係數。
"""
import math
from pathlib import Path

from . import C2SError, NeedsInput, load_json, save_json

MOTIONS = ("idle", "happy")
CHANNELS = {"rotate": ["value"], "translate": ["x", "y"], "scale": ["x", "y"]}

IDLE = {  # 週期 2.0 秒，1 次：呼吸、輕微點頭
    "hip": {"translate": lambda s, a, h: [(0, 0, 0), (1.0, 0, -0.008 * h), (2.0, 0, 0)]},
    "body": {"scale": lambda s, a, h: [(0, 1, 1), (1.0, 1.012, 1.02), (2.0, 1, 1)]},
    "head": {"rotate": lambda s, a, h: [(0, 0), (0.5, 1.5), (1.5, -1.5), (2.0, 0)]},
    "arm": {"rotate": lambda s, a, h: [(0, 0), (1.0, 3 * s), (2.0, 0)]},
    "hair": {"rotate": lambda s, a, h: [(0, 0), (0.7, 2), (1.7, -1.5), (2.0, 0)]},
    "skirt": {"scale": lambda s, a, h: [(0, 1, 1), (1.1, 1.015, 0.99), (2.0, 1, 1)]},
    "prop": {"rotate": lambda s, a, h: [(0, 0), (1.0, -1.5 * s), (2.0, 0)]},
    "accessory": {"rotate": lambda s, a, h: [(0, 0), (0.8, 1.5), (1.8, -1), (2.0, 0)]},
}

HAPPY = {  # 週期 1.2 秒，2 次：蹲 → 跳 → 落地緩衝
    "hip": {"translate": lambda s, a, h: [(0, 0, 0), (0.2, 0, -0.04 * h), (0.5, 0, 0.14 * h), (0.8, 0, 0),
                                          (0.9, 0, -0.025 * h), (1.2, 0, 0)]},
    "body": {"scale": lambda s, a, h: [(0, 1, 1), (0.2, 1.06, 0.92), (0.5, 0.96, 1.06), (0.9, 1.05, 0.94), (1.2, 1, 1)],
             "rotate": lambda s, a, h: [(0, 0), (0.5, 4 * a), (1.2, 0)]},
    "head": {"rotate": lambda s, a, h: [(0, 0), (0.2, -4 * a), (0.5, 8 * a), (0.9, -3 * a), (1.2, 0)]},
    "arm": {"rotate": lambda s, a, h: [(0, 0), (0.2, -10 * s), (0.5, 110 * s), (0.7, 95 * s), (0.9, 30 * s), (1.2, 0)]},
    "leg": {"rotate": lambda s, a, h: [(0, 0), (0.5, 12 * s), (0.8, 0), (1.2, 0)]},
    # 被道具帶著的手（雙手抱樂器）：幅度受接觸約束限制，改用一個週期 5 次的撥弦節奏表現動作（最大轉角與 arm 相同，約束上限不變）
    "arm_strum": {"rotate": lambda s, a, h: [(0, 0), (0.2, 110 * s), (0.4, -110 * s), (0.6, 110 * s), (0.8, -110 * s),
                                             (1.0, 110 * s), (1.2, 0)]},
    # 次要動作：比主體晚一拍，模擬頭髮、裙擺被甩動
    "hair": {"rotate": lambda s, a, h: [(0, 0), (0.3, 6 * a), (0.6, -8 * a), (0.95, 4 * a), (1.2, 0)]},
    "skirt": {"scale": lambda s, a, h: [(0, 1, 1), (0.3, 1.05, 0.94), (0.6, 0.97, 1.06), (0.95, 1.04, 0.96), (1.2, 1, 1)]},
    "prop": {"rotate": lambda s, a, h: [(0, 0), (0.3, -8 * s), (0.6, 10 * s), (0.95, -4 * s), (1.2, 0)]},
    "accessory": {"rotate": lambda s, a, h: [(0, 0), (0.3, 4 * a), (0.6, -5 * a), (0.95, 2 * a), (1.2, 0)]},
    # 地面影子留在原地：角色蹲下時略大、跳到最高時縮小（時間對齊 hip 的蹲跳）
    "ground": {"scale": lambda s, a, h: [(0, 1, 1), (0.2, 1.04, 1.04), (0.5, 0.8, 0.8), (0.8, 1, 1), (0.9, 1.02, 1.02), (1.2, 1, 1)]},
}

TEMPLATES = {"idle": (IDLE, 2.0, 1), "happy": (HAPPY, 1.2, 2)}  # 模板、週期秒數、循環次數


def _keys(frames, channels):
    """frames: [(time, v1[, v2])] → Spine keys。相鄰兩格之間用平切線 bezier（緩入緩出）。
    4.x 的 curve 是絕對座標：每個 channel 四個數字 [t1, v1, t2, v2]。"""
    keys = []
    for i, frame in enumerate(frames):
        t, values = frame[0], frame[1:]
        key = {"time": round(t, 4)} if t else {}
        key.update({c: round(v, 3) for c, v in zip(channels, values)})
        if i < len(frames) - 1:
            t1, nxt = frames[i + 1][0], frames[i + 1][1:]
            third = (t1 - t) / 3
            key["curve"] = [round(n, 4) for v, v1 in zip(values, nxt) for n in (t + third, v, t1 - third, v1)]
        keys.append(key)
    return keys


def _timeline(make, s, h, period, count, factor, base):
    """把一個週期重複 count 次（後續週期的第 0 格與前一週期最後一格重疊），幅度乘上 factor。"""
    frames = []
    for i in range(count):
        for t, *vals in make(s, 1 if i % 2 == 0 else -1, h)[1 if i else 0:]:
            frames.append((t + i * period, *[base + (v - base) * factor for v in vals]))
    return frames


CONTACT_TOL = 0.01  # attach 接觸點因旋轉產生的最大位移（角色高度的比例）；校準依據見 docs/DECISIONS.md D-32


def _template_role(rig, bone, template):
    """被道具帶著的手（手掛在道具骨頭下，例如雙手抱吉他）改用撥弦節奏；手裡拿著的東西（道具掛在手下）不適用。"""
    role = rig["roles"].get(bone)
    parent = next((b.get("parent") for b in rig["bones"] if b["name"] == bone), None)
    return "arm_strum" if role == "arm" and rig["roles"].get(parent) == "prop" and "arm_strum" in template else role


def contact_limits(rig, motion):
    """attach 約束：讓「模板最大轉角 × 關節到接觸點的距離 ≤ 容許位移」的幅度上限。{骨頭: 上限}"""
    template = TEMPLATES[motion][0]
    world = {b["name"]: b["world"] for b in rig["bones"] if "world" in b}
    h = rig["height"]
    parent = {b["name"]: b.get("parent") for b in rig["bones"]}

    def ancestors(n):
        while parent.get(n):
            n = parent[n]
            yield n
    limits = {}
    for c in rig.get("contacts", []):
        # 道具帶著手時（手是道具的子骨頭），道具的旋轉連同手一起帶動、不影響接觸，只限制手自己的旋轉。
        # 手拿著道具（道具是手的子骨頭）時維持原本做法：兩者都限制。
        # ponytail: 後者的限制對接觸是多餘的，但目前碰巧壓住了身體草稿的露出；身體補畫後可一併拿掉
        pair = (c["a"], c["b"])
        carried = lambda b: rig["roles"].get(b) == "prop" and any(b in ancestors(o) for o in pair if o != b)
        for bone in [b for b in pair if not carried(b)]:
            make = template.get(_template_role(rig, bone, template), {}).get("rotate")
            if not make:
                continue
            peak = math.radians(max(abs(v) for _, v in make(1, 1, h)))
            r = math.hypot(world[bone][0] - c["point"][0], world[bone][1] - c["point"][1])
            if peak and r:
                limits[bone] = min(limits.get(bone, 1.0), CONTACT_TOL * h / (peak * r))
    return limits


def _animation(rig, motion, tuning=None):
    template, period, count = TEMPLATES[motion]
    world = {b["name"]: b["world"] for b in rig["bones"] if "world" in b}
    body_x = world["body"][0]
    limits = contact_limits(rig, motion)
    tune = (tuning or {}).get(motion, {})
    bones = {}
    for bone, role in [("hip", "hip"), *((b, _template_role(rig, b, template)) for b in rig["roles"])]:
        factor = min(rig["motion"].get(bone, 1.0), limits.get(bone, math.inf)) * tune.get(bone, 1.0)
        if role not in template or factor == 0:
            continue
        s = -1 if world[bone][0] < body_x else 1
        tls = {}
        for tl, make in template[role].items():
            frames = _timeline(make, s, rig["height"], period, count, factor, 1 if tl == "scale" else 0)
            if tl == "scale" and _is_vertical(world[bone][2]):
                # 模板的 scale 是畫面上的（寬, 高）；Spine 的 scaleX 沿著骨頭，骨頭直立時要對調
                frames = [(t, sy, sx) for t, sx, sy in frames]
            tls[tl] = _keys(frames, CHANNELS[tl])
        bones[bone] = tls
    return {"bones": bones}


def _is_vertical(rotation_deg):
    return abs(math.sin(math.radians(rotation_deg))) > abs(math.cos(math.radians(rotation_deg)))


def build_animations(workdir, motion="happy"):
    """一律產生 idle；motion 另外指定要加上的動作。每次都從頭重建 animations.json。"""
    wd = Path(workdir)
    if motion not in MOTIONS:
        raise C2SError(f"未知的動作：{motion}（可用：{', '.join(MOTIONS)}）")
    if not (wd / "rig.json").exists():
        raise NeedsInput(f"{wd} 尚未建立骨架，請先執行 c2s rig")
    rig = load_json(wd / "rig.json")
    tuning = load_json(wd / "tuning.json") if (wd / "tuning.json").exists() else {}
    anims = {m: _animation(rig, m, tuning) for m in dict.fromkeys(["idle", motion])}
    save_json(wd / "animations.json", anims)
    (wd / "quality" / "quality_report.json").unlink(missing_ok=True)  # 動畫變了，舊的品質報告不再有效
    return {"status": "ok", "animations": {n: duration(a) for n, a in anims.items()}}


def duration(animation):
    return max((k.get("time", 0) for tls in animation.get("bones", {}).values() for keys in tls.values() for k in keys), default=0)
