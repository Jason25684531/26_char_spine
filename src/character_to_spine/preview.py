"""不依賴 Spine 的骨架求值與預覽算圖：讀 Spine JSON，算出指定時間的畫面。

用途是檢查自己的輸出（圖層位置、順序、動畫方向），不是 Spine 的算圖結果。
"""
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from . import load_json
from .animation_builder import duration

DEFAULTS = {"rotate": {"value": 0}, "translate": {"x": 0, "y": 0}, "scale": {"x": 1, "y": 1}}


def _sample(keys, kind, t):
    base = DEFAULTS[kind]
    vals = [{c: k.get(c, d) for c, d in base.items()} for k in keys]
    times = [k.get("time", 0) for k in keys]
    if t <= times[0]:
        return vals[0]
    for i in range(len(keys) - 1):
        if t < times[i + 1]:
            u = (t - times[i]) / (times[i + 1] - times[i])
            curve = keys[i].get("curve")
            if curve == "stepped":
                u = 0
            elif curve:
                # ponytail: 本專案產生的 bezier 都是平切線、控制點在 1/3 處，等同 smoothstep。
                # 要預覽任意 bezier 時再改成真正的曲線求解。
                u = u * u * (3 - 2 * u)
            return {c: vals[i][c] + (vals[i + 1][c] - vals[i][c]) * u for c in base}
    return vals[-1]


def _matrix(x, y, rotation, sx=1.0, sy=1.0):
    r = math.radians(rotation)
    c, s = math.cos(r), math.sin(r)
    return np.array([[c * sx, -s * sy, x], [s * sx, c * sy, y], [0, 0, 1]])


def world_matrices(skel, animation=None, t=0.0):
    timelines = skel["animations"][animation]["bones"] if animation else {}
    world = {}
    for b in skel["bones"]:
        tl = timelines.get(b["name"], {})
        rot = _sample(tl["rotate"], "rotate", t)["value"] if "rotate" in tl else 0
        tr = _sample(tl["translate"], "translate", t) if "translate" in tl else {"x": 0, "y": 0}
        sc = _sample(tl["scale"], "scale", t) if "scale" in tl else {"x": 1, "y": 1}
        local = _matrix(b.get("x", 0) + tr["x"], b.get("y", 0) + tr["y"], b.get("rotation", 0) + rot,
                        b.get("scaleX", 1) * sc["x"], b.get("scaleY", 1) * sc["y"])
        world[b["name"]] = world[b["parent"]] @ local if "parent" in b else local
    return world


def render(skel, images_dir, canvas, origin, animation=None, t=0.0, scale=1.0):
    """回傳 (疊在白底上的 HxWx3 float, alpha 0~1)。canvas=(w, h)，origin=骨架原點在畫布上的像素位置（已含 scale）。"""
    w, h = canvas
    out, alpha = np.full((h, w, 3), 255.0), np.zeros((h, w))
    world = world_matrices(skel, animation, t)
    to_canvas = np.array([[scale, 0, origin[0]], [0, -scale, origin[1]], [0, 0, 1]])  # Spine y 向上 → 影像 y 向下
    skin = skel["skins"][0]["attachments"]
    for slot in skel["slots"]:
        att = skin[slot["name"]][slot["attachment"]]
        img = np.array(Image.open(Path(images_dir) / f"{slot['attachment']}.png").convert("RGBA")).astype(np.float32)
        ih, iw = img.shape[:2]
        # 圖片像素（左上原點、y 向下）→ 附件本地座標（中心原點、y 向上）
        to_local = np.array([[1, 0, -iw / 2], [0, -1, ih / 2], [0, 0, 1]])
        m = to_canvas @ world[slot["bone"]] @ _matrix(att.get("x", 0), att.get("y", 0), att.get("rotation", 0),
                                                        att.get("scaleX", 1), att.get("scaleY", 1)) @ to_local
        img[..., :3] *= img[..., 3:4] / 255  # 先乘 alpha 再變形，邊緣才不會出現黑邊
        warped = cv2.warpAffine(img, m[:2].astype(np.float64), (w, h), flags=cv2.INTER_LINEAR)
        a = warped[..., 3] / 255
        out = warped[..., :3] + out * (1 - a[..., None])
        alpha = a + alpha * (1 - a)
    return out, alpha


def render_setup_pose(workdir):
    wd = Path(workdir)
    meta = load_json(wd / "metadata.json")
    skel = load_json(wd / "spine" / "character.json")
    return render(skel, wd / "spine" / "images", meta["canvas"], meta["origin"])


LABEL = "Python Simulation Preview - not a Spine render"
PREVIEW_MAX_SIDE = 480  # ponytail: 預覽只用來看動作，縮小可把大圖角色的記憶體用量壓在數十 MB


def write_previews(workdir, fps=20):
    """每個動畫輸出一個 GIF 到 <workdir>/preview/<動畫>_python_simulation_preview.gif。
    畫面以角色外框為中心、四周留邊，跳躍與舉手才不會被裁掉。"""
    wd = Path(workdir)
    meta = load_json(wd / "metadata.json")
    skel = load_json(wd / "spine" / "character.json")
    bx, by, bw, bh = meta["bbox"]
    pad = int(bh * 0.3)
    scale = min(1.0, PREVIEW_MAX_SIDE / (max(bw, bh) + pad * 2))
    canvas = (round((bw + pad * 2) * scale), round((bh + pad * 2) * scale))
    origin = ((meta["origin"][0] - bx + pad) * scale, (meta["origin"][1] - by + pad) * scale)
    out = wd / "preview"
    out.mkdir(exist_ok=True)
    paths = []
    for name, anim in skel["animations"].items():
        frames = []
        for i in range(max(2, round(duration(anim) * fps))):
            frame = Image.fromarray(render(skel, wd / "spine" / "images", canvas, origin, name, i / fps, scale)[0].clip(0, 255).astype(np.uint8))
            ImageDraw.Draw(frame).text((4, 3), f"{LABEL} | {name} t={i / fps:.2f}s", fill=(70, 70, 70))
            frames.append(frame)
        path = out / f"{name}_python_simulation_preview.gif"
        frames[0].save(path, save_all=True, append_images=frames[1:], duration=round(1000 / fps), loop=0)
        paths.append(str(path))
    return paths
