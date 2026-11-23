"""補畫優先順序與目視驗收圖（Python Simulation Preview，不是 Spine 算圖）。

python scripts/visual_report.py <工作目錄> [--out <輸出目錄>]（預設 <工作目錄>/report）

輸出 repair_priority.md、每個列出部件的 repair_<部件>.png、visual_check.png。
露出量：補上的像素在動畫中實際被看見的量，扣掉初始姿勢的值，除以部件在初始姿勢的面積；
取樣與 quality.assess 相同（每 1/FPS 秒加上每個關鍵影格），idle 與 happy 都量。
"""
import argparse
import math
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from character_to_spine import load_json, quality  # noqa: E402
from character_to_spine.animation_builder import duration  # noqa: E402
from character_to_spine.image_processor import CONTOUR_HIDDEN_MAX, HOLDOUT_MAX, part_mask  # noqa: E402
from character_to_spine.preview import render, world_matrices  # noqa: E402

FONT = "C:/Windows/Fonts/msjh.ttc"
HIGH, MID = 0.02, 0.005
PANEL_H, PANEL_MIN_W = 360, 360
TILE_W = 400
CHECK_TIMES = (("happy", (0, 0.2, 0.5, 0.9, 1.4)), ("idle", (0, 0.5, 1.0, 1.5)))
CONTACT_COLORS = ((230, 30, 30), (20, 110, 230), (20, 160, 60), (220, 130, 0), (150, 40, 200))


def font(size):
    return ImageFont.truetype(FONT, size)


def sample_times(data):
    keys = {k.get("time", 0) for tls in data["bones"].values() for ks in tls.values() for k in ks}
    return sorted({round(i / quality.FPS, 4) for i in range(round(duration(data) * quality.FPS) + 1)} | keys)


def fill_seen(f, p):
    m = f["masks"].get(p)
    return float((m * f["vis"][p]).sum()) if m is not None else 0.0


def measure(ctx, skel):
    """{部件: 最大露出}，只含有圖層的部件。px 是預覽畫布像素。"""
    setup = quality._frame(ctx, skel, None, 0.0)
    out = {p: {"ratio": 0.0, "px": 0.0, "anim": None, "t": 0.0, "base": fill_seen(setup, p),
               "area": max(1.0, float((a > 0.5).sum()))} for p, a in setup["alphas"].items()}
    for anim, data in skel["animations"].items():
        for t in sample_times(data):
            f = quality._frame(ctx, skel, anim, t)
            for p, m in out.items():
                px = fill_seen(f, p) - m["base"]
                if px > m["px"]:
                    m.update(px=px, ratio=px / m["area"], anim=anim, t=t)
    return out


def priority(m):
    if m is None:
        return "高"
    if m["ratio"] >= HIGH:
        return "高"
    if m["ratio"] >= MID:
        return "中"
    return "低" if m["px"] > 0 else "無露出"


def suggestion(e, m):
    occ = "、".join(e.get("occluders") or []) or "其他部件"
    hidden = f"（約 {e['hidden_ratio']:.0%} 面積）" if "hidden_ratio" in e else ""
    s = f"補畫被 {occ} 遮住的區域{hidden}"
    if m is None:
        return s + "；這個部件目前沒有圖層，動畫與 Spine 裡都不會出現，必須補畫。"
    if m["px"] <= 0:
        return s + "；動畫中不會露出，可保留草稿。"
    s += f"；動畫中最多露出 {m['ratio']:.2%}（{m['anim']} t={m['t']}s）"
    if m["ratio"] >= MID:
        s += f"。若暫不補，可降低 {occ} 的 motion（parts.json），讓遮擋者別移開那麼多"
    else:
        s += "。可保留草稿，目視確認即可"
    notes = []
    if e.get("contour_hidden", 0) > CONTOUR_HIDDEN_MAX:
        notes.append(f"被遮住的輪廓佔 {e['contour_hidden']:.0%}，那段外形要看原圖重畫，自動補圖補不出來")
    if e.get("holdout_error", 0) > HOLDOUT_MAX:
        notes.append(f"紋理延伸誤差 {e['holdout_error']}，自動填色會糊，要手繪紋理")
    return s + "。" + (f"補畫時注意：{'；'.join(notes)}。" if notes else "")


def fit(img):
    img = img.resize((max(1, round(img.width * PANEL_H / img.height)), PANEL_H), Image.LANCZOS)
    if img.width >= PANEL_MIN_W:
        return img
    padded = Image.new("RGB", (PANEL_MIN_W, PANEL_H), "white")
    padded.paste(img, ((PANEL_MIN_W - img.width) // 2, 0))
    return padded


def placeholder(text):
    img = Image.new("RGB", (PANEL_MIN_W, PANEL_H), (235, 235, 235))
    ImageDraw.Draw(img).text((20, PANEL_H // 2 - 14), text, fill=(90, 90, 90), font=font(24))
    return img


def crop(rgb, mask, margin):
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return rgb
    pad = round(margin * max(np.ptp(xs), np.ptp(ys), 1))
    h, w = mask.shape
    return rgb[max(0, ys.min() - pad):min(h, ys.max() + pad + 1), max(0, xs.min() - pad):min(w, xs.max() + pad + 1)]


def outline(rgb, mask, color, thickness):
    cnts = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    cv2.drawContours(rgb, cnts, -1, color, thickness)


def repair_png(ctx, skel, source, part, e, m, path):
    name = e["name"]
    mask = part_mask(part, source.shape[:2])
    a = source.copy()
    outline(a, mask, (0, 150, 255), max(2, round(max(source.shape) / 300)))
    panels = [(("(a) 原圖", "藍線＝這個部件的範圍"), Image.fromarray(crop(a, mask, 0.15)))]
    if m is None:
        panels += [(("(b) 目前圖層", ""), placeholder("沒有圖層")), (("(c) 動畫中露出最多", ""), placeholder("沒有圖層"))]
    else:
        layer = np.array(Image.open(ctx["images"] / f"{name}.png").convert("RGBA")).astype(float)
        yy, xx = np.indices(layer.shape[:2])
        cell = max(4, max(layer.shape[:2]) // 40)
        bg = np.where(((yy // cell + xx // cell) % 2 == 0)[..., None], 255.0, 205.0)
        al = layer[..., 3:4] / 255
        b = layer[..., :3] * al + bg * (1 - al)
        mp = ctx["masks"] / f"{name}.png"
        if mp.exists():
            fill = np.array(Image.open(mp).convert("L")) > 127
            b[fill] = b[fill] * 0.6 + np.array([255, 0, 255]) * 0.4
        panels.append((("(b) 目前圖層", "洋紅＝自動補上的區域"), Image.fromarray(b.astype(np.uint8))))
        anim, t = (m["anim"], m["t"]) if m["px"] > 0 else (None, 0.0)
        f = quality._frame(ctx, skel, anim, t)
        c = render(skel, ctx["images"], ctx["canvas"], ctx["origin"], anim, t, ctx["scale"], ctx["cache"])[0]
        if m["px"] > 0:
            seen = f["masks"][name] * f["vis"][name] > 0.3
            c[seen] = c[seen] * 0.4 + np.array([255, 0, 0]) * 0.6
            c = c.clip(0, 255).astype(np.uint8)
            outline(c, seen, (200, 0, 0), 1)
            title = ("(c) 動畫中露出最多", f"{anim} t={t}s，露出 {m['ratio']:.2%}（紅色）")
        else:
            c = c.clip(0, 255).astype(np.uint8)
            title = ("(c) 動畫中露出最多", "無露出（顯示初始姿勢）")
        panels.append((title, Image.fromarray(crop(c, f["alphas"][name] > 0.5, 0.25))))
    imgs = [fit(im) for _, im in panels]
    sheet = Image.new("RGB", (sum(i.width for i in imgs) + 20 * (len(imgs) + 1), PANEL_H + 100), "white")
    d = ImageDraw.Draw(sheet)
    x = 20
    for ((t1, t2), _), im in zip(panels, imgs):
        d.text((x, 10), t1, fill=(0, 0, 0), font=font(24))
        d.text((x, 44), t2, fill=(90, 90, 90), font=font(18))
        sheet.paste(im, (x, 80))
        x += im.width + 20
    sheet.save(path)


def visual_check(wd, ctx, skel, path):
    contacts = ctx["rig"].get("contacts", [])
    setup = world_matrices(skel)
    s, (ox, oy) = ctx["scale"], ctx["origin"]
    frames = []
    for anim, times in CHECK_TIMES:
        if anim not in skel["animations"]:
            continue
        row = []
        for t in times:
            rgb, alpha = render(skel, ctx["images"], ctx["canvas"], ctx["origin"], anim, t, s, ctx["cache"])
            world = world_matrices(skel, anim, t)
            pts = [[(s * x + ox, -s * y + oy) for x, y in
                    ((world[bone] @ np.linalg.inv(setup[bone]) @ np.array([*c["point"], 1.0]))[:2] for bone in (c["a"], c["b"]))]
                   for c in contacts]
            row.append((f"{anim} t={t}s", rgb, alpha, pts))
        frames.append(row)
    # 預覽畫布四周留了大片空白（給跳躍用）：所有影格共用同一個裁切框再放大，動作差異才看得清楚
    ys, xs = np.nonzero(np.any([a > 0.02 for row in frames for _, _, a, _ in row], axis=0))
    x0, y0 = max(0, xs.min() - 30), max(0, ys.min() - 30)
    x1, y1 = xs.max() + 30, ys.max() + 30
    k = TILE_W / (x1 - x0)
    tw, th = TILE_W, round((y1 - y0) * k)
    rows = []
    for row in frames:
        tiles = []
        for label, rgb, _, pts in row:
            img = Image.fromarray(rgb[y0:y1, x0:x1].clip(0, 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
            d = ImageDraw.Draw(img)
            for i, pair in enumerate(pts):
                col = CONTACT_COLORS[i % len(CONTACT_COLORS)]
                for (cx, cy), r, filled in zip(pair, (6, 12), (True, False)):
                    cx, cy = (cx - x0) * k, (cy - y0) * k
                    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col if filled else None, outline=col, width=3)
            d.text((8, 6), label, fill=(30, 30, 30), font=font(22))
            tiles.append(img)
        rows.append(tiles)
    width = tw * max(len(r) for r in rows)
    preview = Image.open(wd / "layer_preview.png").convert("RGB")
    preview = preview.resize((width, max(1, round(preview.height * width / preview.width))), Image.LANCZOS)
    legend = ["Python Simulation Preview — 非 Spine 算圖"]
    if contacts:
        legend.append("接觸點：實心點跟著 a 骨頭、空心圈跟著 b 骨頭；點在圈中央＝接觸沒有分開。")
        legend += [f"  色 {i + 1}：{c['a']}（實心）+ {c['b']}（空心）" for i, c in enumerate(contacts)]
    head = 16 + 30 * len(legend)
    sheet = Image.new("RGB", (width, head + th * len(rows) + preview.height), "white")
    d = ImageDraw.Draw(sheet)
    for i, line in enumerate(legend):
        col = CONTACT_COLORS[(i - 2) % len(CONTACT_COLORS)] if i >= 2 else (0, 0, 0)
        d.text((10, 8 + 30 * i), line, fill=col, font=font(24 if i == 0 else 20))
    for r, tiles in enumerate(rows):
        for i, tile in enumerate(tiles):
            sheet.paste(tile, (i * tw, head + r * th))
    sheet.paste(preview, (0, head + th * len(rows)))
    sheet.save(path)


def fmt(v):
    return "—" if v is None else str(v)


def write_markdown(wd, ctx, sections, meas, path):
    lines = [f"# 補畫優先順序：{wd.name}", "",
             "露出量是 Python Simulation Preview 的量測（非 Spine 算圖）：自動補上的像素在 idle／happy 中實際被看見的量，"
             f"扣掉初始姿勢的值，除以部件在初始姿勢的面積。取樣：每 {1 / quality.FPS:g} 秒加上每個關鍵影格。",
             f"優先：高 ≥ {HIGH:.0%}；中 {MID:.1%}–{HIGH:.0%}；低 > 0 且 < {MID:.1%}（可保留草稿，目視確認即可）；無露出 = 0（動畫中不會露出，可保留草稿）。",
             f"像素是預覽畫布像素（縮放 {ctx['scale']:.3f}），括號內換算成原圖像素。", ""]
    for title, entries in sections:
        lines += [f"## {title}", ""]
        if not entries:
            lines += ["（無）", ""]
            continue
        lines += ["| 順位 | 部件 | 優先 | 最大露出 | 露出像素 | 發生於 | hidden_ratio | holdout_error | contour_hidden | 遮擋者 |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for i, e in enumerate(entries, 1):
            m = meas.get(e["name"])
            if m is None:
                exp, px, at = "無圖層", "—", "—"
            else:
                exp = f"{m['ratio']:.2%}"
                px = f"{m['px']:.0f}（約 {m['px'] / ctx['scale'] ** 2:.0f}）"
                at = f"{m['anim']} t={m['t']}s" if m["px"] > 0 else "—"
            lines.append(f"| {i} | `{e['name']}` | {priority(m)} | {exp} | {px} | {at} | {fmt(e.get('hidden_ratio'))} | "
                         f"{fmt(e.get('holdout_error'))} | {fmt(e.get('contour_hidden'))} | {'、'.join(e.get('occluders') or []) or '—'} |")
        lines.append("")
        for e in entries:
            m = meas.get(e["name"])
            lines += [f"### {e['name']}（{priority(m)}）", "", suggestion(e, m), "", f"![{e['name']}](repair_{e['name']}.png)", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="補畫優先順序與目視驗收圖")
    ap.add_argument("workdir")
    ap.add_argument("--out")
    args = ap.parse_args()
    wd = Path(args.workdir)
    for need in ("metadata.json", "rig.json", "parts.json", "source_rgba.png", "layer_preview.png", "spine/character.json"):
        if not (wd / need).exists():
            sys.exit(f"{wd} 缺少 {need}，請先跑完 c2s run")
    out = Path(args.out) if args.out else wd / "report"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("repair_*.png"):
        old.unlink()

    ctx = quality._context(wd)
    skel = load_json(wd / "spine" / "character.json")
    meas = measure(ctx, skel)
    parts = ctx["meta"]["parts"]
    order = lambda e: -meas[e["name"]]["ratio"] if e["name"] in meas else -math.inf
    sections = [("需要人工補畫（needs_manual）", sorted((e for e in parts if e["status"] == "needs_manual"), key=order)),
                ("自動補但不可靠", sorted((e for e in parts if e["status"] == "auto_repaired" and e.get("repair_reliable") is False), key=order))]
    write_markdown(wd, ctx, sections, meas, out / "repair_priority.md")

    source = np.array(Image.alpha_composite(Image.new("RGBA", Image.open(wd / "source_rgba.png").size, "white"),
                                            Image.open(wd / "source_rgba.png").convert("RGBA")).convert("RGB"))
    by_name = {p["name"]: p for p in load_json(wd / "parts.json")["parts"]}
    for _, entries in sections:
        for e in entries:
            repair_png(ctx, skel, source, by_name[e["name"]], e, meas.get(e["name"]), out / f"repair_{e['name']}.png")
    visual_check(wd, ctx, skel, out / "visual_check.png")
    print(out)


if __name__ == "__main__":
    main()
