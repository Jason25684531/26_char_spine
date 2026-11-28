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

# 數值依據：docs/motion/reference_analysis.md（四支參考影片，括號內為規則編號）與 Spine-SKILL（docs/motion/spine_skill_mapping.md）
IDLE = {  # 週期 1.3 秒（I1：影片 1.0～1.33 秒）：呼吸下沉、頭部起伏約 2.5%（I2），手比頭早 0.15 秒（I4/I5），頭髮晚 0.1 秒（I7）
    "hip": {"translate": lambda s, a, h: [(0, 0, 0), (0.65, 0, -0.02 * h), (1.3, 0, 0)]},
    "body": {"scale": lambda s, a, h: [(0, 1, 1), (0.65, 1.015, 0.985), (1.3, 1, 1)]},
    "head": {"rotate": lambda s, a, h: [(0, 0), (0.33, 1.5), (0.98, -1.5), (1.3, 0)]},  # I6：±1～2°
    "arm": {"rotate": lambda s, a, h: [(0, 0), (0.5, 4 * s), (1.3, 0)]},
    "hair": {"rotate": lambda s, a, h: [(0, 0), (0.43, 3), (1.08, -3), (1.3, 0)]},
    "skirt": {"scale": lambda s, a, h: [(0, 1, 1), (0.75, 1.012, 0.99), (1.3, 1, 1)]},
    "prop": {"rotate": lambda s, a, h: [(0, 0), (0.65, -1 * s), (1.3, 0)]},  # P1：雙手捧著的道具 ±1°
    "accessory": {"rotate": lambda s, a, h: [(0, 0), (0.43, 1.5), (1.13, -1), (1.3, 0)]},
}

ARM_PEAK = 135  # Happy 舉起的手：從下垂舉到水平以上 45°（H4：影片 45～60°）


def _happy_arm(s, a, h):
    """H4：每個循環一隻手舉起揮動（±10°），另一隻張開往下；兩個循環左右交替。"""
    if s == a:
        return [(0, 0), (0.13, -10 * s), (0.33, ARM_PEAK * s), (0.5, (ARM_PEAK - 20) * s), (0.67, ARM_PEAK * s),
                (0.84, (ARM_PEAK - 20) * s), (1.0, 60 * s), (1.2, 0)]
    return [(0, 0), (0.33, 30 * s), (0.8, 22 * s), (1.2, 0)]


HAPPY = {  # 週期 1.2 秒，2 次（左右交替）：蹲 0.13s（H1）→ 起跳 0.2s 升 11.5%（H2）→ 落地緩衝 → 一次小彈跳 3.5%（H3）→ 回穩
    # hip 在離地、著地的瞬間都有 y=0 的關鍵格（腳鎖在地面要求每一段不跨過地面）
    "hip": {"translate": lambda s, a, h: [(0, 0, 0), (0.13, 0, -0.035 * h), (0.18, 0, 0), (0.33, 0, 0.115 * h),
                                          (0.53, 0, 0), (0.6, 0, -0.03 * h), (0.67, 0, 0), (0.79, 0, 0.035 * h),
                                          (0.91, 0, 0), (0.96, 0, -0.02 * h), (1.2, 0, 0)]},
    # Spine-SKILL P0-4：伸展最大在起跳（往上速度最大），頂點回原形，著地壓扁
    "body": {"scale": lambda s, a, h: [(0, 1, 1), (0.13, 1.05, 0.93), (0.22, 0.96, 1.06), (0.33, 1, 1), (0.6, 1.05, 0.94),
                                       (0.7, 0.98, 1.03), (0.79, 1, 1), (0.96, 1.03, 0.97), (1.2, 1, 1)],
             "rotate": lambda s, a, h: [(0, 0), (0.33, 4 * a), (1.2, 0)]},
    "head": {"rotate": lambda s, a, h: [(0, 0), (0.13, -3 * a), (0.45, 10 * a), (0.85, -3 * a), (1.2, 0)]},  # H5：約 11°
    "arm": {"rotate": _happy_arm},
    "leg": {"rotate": lambda s, a, h: [(0, 0), (0.33, 12 * s), (0.53, 0), (1.2, 0)]},
    # 被道具帶著的手（雙手抱樂器）：幅度受接觸約束限制，改用一個週期 5 次的撥弦節奏表現動作（最大轉角與 arm 相同，約束上限不變）
    "arm_strum": {"rotate": lambda s, a, h: [(0, 0), (0.2, ARM_PEAK * s), (0.4, -ARM_PEAK * s), (0.6, ARM_PEAK * s),
                                             (0.8, -ARM_PEAK * s), (1.0, ARM_PEAK * s), (1.2, 0)]},
    # 次要動作（I7、Spine-SKILL P0-6）：落後帶動它的身體 0.07～0.1 秒，著地後還有餘擺
    "hair": {"rotate": lambda s, a, h: [(0, 0), (0.25, -4 * a), (0.43, 6 * a), (0.68, -8 * a), (0.88, 4 * a), (1.04, -3 * a), (1.2, 0)]},
    "skirt": {"scale": lambda s, a, h: [(0, 1, 1), (0.23, 1.04, 0.95), (0.32, 0.97, 1.05), (0.43, 1, 1), (0.7, 1.04, 0.95),
                                        (0.8, 0.98, 1.03), (0.89, 1, 1), (1.06, 1.02, 0.98), (1.2, 1, 1)]},
    "prop": {"rotate": lambda s, a, h: [(0, 0), (0.23, -6 * s), (0.5, 8 * s), (0.85, -4 * s), (1.2, 0)]},
    "accessory": {"rotate": lambda s, a, h: [(0, 0), (0.23, -2 * a), (0.55, 5 * a), (0.95, -2 * a), (1.2, 0)]},
    # 地面影子留在原地：蹲下、落地時略大，跳到最高時縮小（時間對齊 hip）
    "ground": {"scale": lambda s, a, h: [(0, 1, 1), (0.13, 1.04, 1.04), (0.33, 0.8, 0.8), (0.53, 1, 1), (0.6, 1.03, 1.03),
                                         (0.79, 0.93, 0.93), (0.91, 1, 1), (0.96, 1.02, 1.02), (1.2, 1, 1)]},
}

TEMPLATES = {"idle": (IDLE, 1.3, 1), "happy": (HAPPY, 1.2, 2)}  # 模板、週期秒數、循環次數


def _slopes(times, values):
    """每個關鍵格的切線斜率（Fritsch-Carlson 單調插值）：數值穿越關鍵格時保留速度，極值處為 0，不會衝過頭。
    首尾數值相同（循環）時，接縫兩側用同一個斜率，循環接起來沒有停頓（Spine-SKILL：接縫要看速度，不只看數值）。"""
    n = len(times)
    h = [times[i + 1] - times[i] for i in range(n - 1)]
    d = [(values[i + 1] - values[i]) / h[i] if h[i] else 0.0 for i in range(n - 1)]

    def fc(d0, d1, h0, h1):
        if d0 * d1 <= 0:
            return 0.0
        w1, w2 = 2 * h1 + h0, h1 + 2 * h0
        return (w1 + w2) / (w1 / d0 + w2 / d1)
    m = [0.0] * n
    for i in range(1, n - 1):
        m[i] = fc(d[i - 1], d[i], h[i - 1], h[i])
    if n > 2 and abs(values[0] - values[-1]) < 1e-9:
        m[0] = m[-1] = fc(d[-1], d[0], h[-1], h[0])
    return m


def _keys(frames, channels):
    """frames: [(time, v1[, v2])] → Spine keys，bezier 切線見 _slopes。
    4.x 的 curve 是絕對座標：每個 channel 四個數字 [t1, v1, t2, v2]，時間控制點在 1/3 處。"""
    times = [f[0] for f in frames]
    slopes = [_slopes(times, [f[1 + j] for f in frames]) for j in range(len(channels))]
    keys = []
    for i, frame in enumerate(frames):
        t, values = frame[0], frame[1:]
        key = {"time": round(t, 4)} if t else {}
        key.update({c: round(v, 3) for c, v in zip(channels, values)})
        if i < len(frames) - 1:
            t1, nxt = frames[i + 1][0], frames[i + 1][1:]
            third = (t1 - t) / 3
            key["curve"] = [round(n, 4) for j, (v, v1) in enumerate(zip(values, nxt))
                            for n in (t + third, v + slopes[j][i] * third, t1 - third, v1 - slopes[j][i + 1] * third)]
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
        # 一方是另一方的祖先時（道具帶著抱它的手、手拿著道具），祖先的旋轉連同子骨頭一起帶動、不影響接觸，
        # 只限制子骨頭自己的旋轉。不再為了接觸縮小祖先的動作（「過度縮小動作」）
        pair = (c["a"], c["b"])
        for bone in [b for b in pair if not any(b in ancestors(o) for o in pair if o != b)]:
            make = template.get(_template_role(rig, bone, template), {}).get("rotate")
            if not make:
                continue
            peak = math.radians(max(abs(v) for _, v in make(1, 1, h)))
            r = math.hypot(world[bone][0] - c["point"][0], world[bone][1] - c["point"][1])
            if peak and r:
                limits[bone] = min(limits.get(bone, 1.0), CONTACT_TOL * h / (peak * r))
    return limits


RAISE_TARGET = ARM_PEAK - 90  # Happy 舉手的終點方向：外側水平再往上 45°（模板假設手臂下垂 -90°，舉 ARM_PEAK 到這裡）
MIN_RAISE = 30  # 已經舉起或伸直的手臂仍保留的揮動角度
PROP_TILT = 0.25  # 單手拿的道具跟著手傾斜的比例（其餘反向抵銷，保持直立）


def arm_reach(rotation, s):
    """依手臂初始方向（骨頭世界角度，y 向上）算出 Happy 舉手的比例：舉到 RAISE_TARGET 實際需要的角度 ÷ 模板的 ARM_PEAK。
    已經舉起的手臂照模板再轉 ARM_PEAK 會甩過頭、撞臉、露出背後的草稿（v1.0 只能靠縮小整段動作避開）。"""
    target = RAISE_TARGET if s > 0 else 180 - RAISE_TARGET
    need = s * ((target - rotation + 180) % 360 - 180)  # 朝外側（s 的方向）還要轉幾度
    return min(ARM_PEAK, max(MIN_RAISE, need)) / ARM_PEAK


ANCHOR_BOTTOM = ("body", "skirt")  # 擠壓伸展時下緣固定：以腰為中心縮放會讓長袍、裙襬往上縮，露出底下的腿（草稿）


def _bottom_drop(rig, bone):
    """骨頭原點到圖層下緣的世界距離（下緣在原點下方為正）。附件在世界座標中是正立的（rotation = -骨頭角度）。"""
    x, y, rot = next(b["world"] for b in rig["bones"] if b["name"] == bone)
    att = rig["attachments"][bone]
    r = math.radians(rot)
    center_y = y + att["x"] * math.sin(r) + att["y"] * math.cos(r)
    return y - (center_y - att["height"] / 2)


def _animation(rig, motion, tuning=None, overrides=None):
    template, period, count = TEMPLATES[motion]
    world = {b["name"]: b["world"] for b in rig["bones"] if "world" in b}
    parent_of = {b["name"]: b.get("parent") for b in rig["bones"]}
    body_x = world["body"][0]
    limits = contact_limits(rig, motion)
    tune = (tuning or {}).get(motion, {})
    over = (overrides or {}).get(motion, {})  # 使用者的自然語言調整（parts.json 的 motion_overrides）
    bones = {}
    holders = {parent_of[b] for b, r in rig["roles"].items() if r == "prop"}  # 單手拿著道具的手（道具掛在手下）
    rotations = {}  # 骨頭: (rotate 影格, 幅度係數)
    for bone, role in [("hip", "hip"), *((b, _template_role(rig, b, template)) for b in rig["roles"])]:
        s = -1 if world[bone][0] < body_x else 1
        reach = 1.0
        if role == "arm" and motion == "happy":
            # 拿著東西的手只舉起展示，不把道具甩過頭砸到臉
            reach = MIN_RAISE / ARM_PEAK if bone in holders else arm_reach(world[bone][2], s)
        wish = rig["motion"].get(bone, 1.0) * reach * over.get("energy", 1.0) * over.get(rig["roles"].get(bone, role), 1.0)
        factor = min(wish, limits.get(bone, math.inf)) * tune.get(bone, 1.0)  # 加大動作也不能讓手離開道具
        if role not in template or factor == 0:
            continue
        tls = {}
        for tl, make in template[role].items():
            frames = _timeline(make, s, rig["height"], period, count, factor, 1 if tl == "scale" else 0)
            if tl == "scale" and role in ANCHOR_BOTTOM:
                # 畫面上的高度縮放 sy 讓下緣移動 d·(1-sy)，在父骨頭座標裡反向位移抵銷
                d, pr = _bottom_drop(rig, bone), math.radians(world.get(parent_of[bone], (0, 0, 0))[2])
                tls["translate"] = _keys([(t, d * (sy - 1) * math.sin(pr), d * (sy - 1) * math.cos(pr)) for t, _, sy in frames],
                                         CHANNELS["translate"])
            if tl == "scale" and _is_vertical(world[bone][2]):
                # 模板的 scale 是畫面上的（寬, 高）；Spine 的 scaleX 沿著骨頭，骨頭直立時要對調
                frames = [(t, sy, sx) for t, sx, sy in frames]
            tls[tl] = _keys(frames, CHANNELS[tl])
            rotations[bone] = (frames, factor) if tl == "rotate" else rotations.get(bone)
        bones[bone] = tls
    hip = bones.get("hip", {}).get("translate", [])
    if any(k.get("y", 0) < 0 for k in hip):
        for bone in (b for b, r in rig["roles"].items() if r == "leg" and parent_of[b] == "hip"):
            # 蹲下、落地時 hip 往下，腿是 hip 的子骨頭會一起沉進地面；hip 在地面以下的每一段取鏡像，腳留在地上
            # （Spine-SKILL：壓縮要抵著支撐面）。模板的 hip 在離地、著地的瞬間都有 y=0 的關鍵格，每一段不會跨過地面
            bones.setdefault(bone, {})["translate"] = _ground_lock(hip)
    for prop, (arm, (frames, _)) in ((p, (parent_of[p], rotations[parent_of[p]])) for p in bones
                                     if rig["roles"].get(p) == "prop" and rotations.get(parent_of[p])):
        # 單手拿的道具反向旋轉保持直立，只留 PROP_TILT 的傾斜：手往外舉時旗桿、托盤不會整根倒向頭
        f = rotations[prop][1] if rotations.get(prop) else 1.0
        bones[prop]["rotate"] = _keys([(t, v * (PROP_TILT * f - 1)) for t, v in frames], CHANNELS["rotate"])
    return {"bones": bones}


def _ground_lock(hip_keys):
    """hip translate 的 y 在地面以下的段落取反、其餘為 0。曲線控制點一起取反，所以腳的世界高度在整段都剛好不變。"""
    out = []
    for i, k in enumerate(hip_keys):
        key = {"time": k["time"]} if "time" in k else {}
        if k.get("y", 0) < 0:
            key["y"] = -k["y"]
        if i < len(hip_keys) - 1:
            below = min(k.get("y", 0), hip_keys[i + 1].get("y", 0)) < 0
            t1, _, t2, _, u1, v1, u2, v2 = k["curve"]
            key["curve"] = [t1, 0, t2, 0, u1, -v1 if below else 0, u2, -v2 if below else 0]
        out.append(key)
    return out


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
    overrides = load_json(wd / "parts.json").get("motion_overrides", {}) if (wd / "parts.json").exists() else {}
    anims = {m: _animation(rig, m, tuning, overrides) for m in dict.fromkeys(["idle", motion])}
    save_json(wd / "animations.json", anims)
    (wd / "quality" / "quality_report.json").unlink(missing_ok=True)  # 動畫變了，舊的品質報告不再有效
    return {"status": "ok", "animations": {n: duration(a) for n, a in anims.items()}}


def duration(animation):
    return max((k.get("time", 0) for tls in animation.get("bones", {}).values() for keys in tls.values() for k in keys), default=0)
