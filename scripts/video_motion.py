"""參考影片動作分析（只讀本機影片）：時長／fps／影格數、動作分段、各段循環週期、部位振幅與延遲。
輸出到 docs/motion/frames/<ascii 代號>/：overview／seg<k>／loop<k>.png 取樣影格（標 t 秒與影格號，青色刻度＝畫面高 10%）、
energy.png（逐格差能量＋新奇度＋分段線）、recurrence.png（自相似圖，平行對角線間距＝週期）、motion_map.png（亮＝會動）、
track_<段名>.png（TRACK 部位的垂直位移，角色高 %）。分段＝自相似矩陣 checkerboard 新奇度峰值（Foote 2000）＋能量穿越門檻。
python scripts/video_motion.py [影片資料夾，預設 Ref_pic/ref_video] [輸出資料夾，預設 docs/motion/frames]
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CELL_H, SMALL = 240, 96  # 取樣格高度；算畫面差用的縮圖邊長
NOV_S = 1.0              # 新奇度半寬（秒），要大於循環週期一半，否則每個來回都被切開
MIN_SEG_S = 0.5          # 切點最短間隔（秒）
MIN_LAG_S = 0.3          # 週期搜尋下限（秒）
COLORS = [(30, 60, 200), (230, 120, 0), (0, 150, 0), (200, 0, 0), (140, 0, 160), (0, 150, 160), (90, 90, 90)]
# 追蹤區塊（格式見檔內 _說明）。shortcut: 座標人工量，換影片要重量。
TRACK = json.loads((ROOT / "docs" / "motion" / "track_boxes.json").read_text(encoding="utf-8"))


def slug(stem):
    s = re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_")
    return s if re.search(r"[a-z]", s) or len(s) > 8 else "v_" + hashlib.sha1(stem.encode()).hexdigest()[:8]


def read(path):
    cap = cv2.VideoCapture(str(path))
    fps, frames = cap.get(cv2.CAP_PROP_FPS), []
    while (f := cap.read())[0]:
        frames.append(f[1])
    assert frames, f"讀不到影格：{path}"
    return fps, frames


def distances(small):
    """D[i, j]＝影格 i 與 j 縮圖的 RMS 灰階差（0–255）。"""
    x = small.reshape(len(small), -1).astype(np.float64)
    sq = (x * x).sum(1)  # |a-b|² = |a|² + |b|² − 2a·b
    return np.sqrt(np.maximum(sq[:, None] + sq[None, :] - 2 * x @ x.T, 0) / x.shape[1])


def segments(D, e, fps):
    """切點＝新奇度峰值＋平滑能量穿越門檻處。回傳 [(起, 迄, 是否動作)]（影格號，含迄）、新奇度、能量門檻。"""
    w, gap = int(NOV_S * fps), int(MIN_SEG_S * fps)
    nov = np.zeros(len(D))
    for i in range(w, len(D) - w):  # 前後各 w 格：跨界距離平均 − 同側距離平均
        p, f = slice(i - w, i), slice(i, i + w)
        nov[i] = D[p, f].mean() - (D[p, p].mean() + D[f, f].mean()) / 2
    floor = max(nov.mean() + nov.std(), 0.1 * np.median(D))  # 第二項濾掉單一循環影片（整片同一動作）的雜訊峰
    peaks = sorted((i for i in range(1, len(nov) - 1) if nov[i] >= nov[i - 1] and nov[i] > nov[i + 1] and nov[i] > floor),
                   key=lambda i: -nov[i])
    s = np.convolve(e, np.ones(gap) / gap, mode="same")
    lo, hi = np.percentile(s, [10, 95])
    thr = lo + 0.3 * (hi - lo) if hi >= 2 * lo + 0.5 else lo / 2  # 沒有明顯靜止期＝整片都在動
    cuts = []
    for i in peaks + [i for i in range(1, len(s)) if (s[i] > thr) != (s[i - 1] > thr)]:
        if all(abs(i - c) >= gap for c in cuts + [0, len(D)]):
            cuts.append(i)
    edges = [0] + sorted(cuts) + [len(D)]
    return [(a, b - 1, bool(e[a:b].mean() > thr)) for a, b in zip(edges, edges[1:])], nov, thr


def period(D, a, b, fps):
    """使對角線 D[i, i+L] 平均最小的 L。回傳 (L, 差值, 最大差值, 是否循環：差值 < 最大差值一半且 L 不貼搜尋下限)。"""
    lags = range(max(2, int(MIN_LAG_S * fps)), (b - a + 1) // 2 + 1)
    if len(lags) < 3:
        return None  # 段太短，找不了週期
    d = {L: float(np.diagonal(D[a:b + 1, a:b + 1], L).mean()) for L in lags}
    best = min(d, key=d.get)  # 再取 1.15 倍內最短的局部極小，避免挑到 2 倍週期
    best = next(L for L in lags if d[L] <= d[best] * 1.15 and d[L] <= d.get(L - 1, np.inf) and d[L] <= d.get(L + 1, np.inf))
    return best, d[best], max(d.values()), d[best] < 0.5 * max(d.values()) and best > lags[0]


def track(gray, f0, f1, box, R=40, angles=range(-15, 16)):
    """區塊匹配＋旋轉搜尋（旋轉搜尋窗、比對 f0 樣板）。回傳每格 (中心 x, 中心 y, 轉角, 相似度)，轉角 + ＝畫面上順時針。"""
    x, y, w, h = box
    tpl, out = gray[f0, y:y + h, x:x + w], []
    for f in range(f0, f1 + 1):
        x0, y0 = max(0, x - R), max(0, y - R)
        win, best = gray[f, y0:y + h + R, x0:x + w + R], None
        for a in angles:
            M = cv2.getRotationMatrix2D(((win.shape[1] - 1) / 2, (win.shape[0] - 1) / 2), a, 1)
            _, s, _, (lx, ly) = cv2.minMaxLoc(cv2.matchTemplate(cv2.warpAffine(win, M, win.shape[::-1]), tpl, cv2.TM_CCOEFF_NORMED))
            if best is None or s > best[3]:
                cx, cy = cv2.invertAffineTransform(M) @ [lx + w / 2, ly + h / 2, 1]
                best = (cx + x0, cy + y0, a, s)
        out.append(best)
    return np.array(out)


def report_track(gray, spec, fps, out):
    char_h, ranges, parts = spec  # [角色高, [[段名, 起, 迄]], {部位: [x, y, w, h]}]
    ref_name = next(iter(parts))
    amp = lambda z: np.percentile(z, 95) - np.percentile(z, 5)
    for label, f0, f1 in ranges:
        tr = {k: track(gray, f0, f1, b) for k, b in parts.items()}
        print(f"   track {label} f{f0}-f{f1}  (char {char_h}px; amplitude = p95-p5; lag vs {ref_name}, + = later)")
        for k, v in tr.items():
            x, y, a, s = v.T
            ax = 0 if amp(x) > amp(y) else 1
            r, q = tr[ref_name][:, ax] - tr[ref_name][:, ax].mean(), v[:, ax] - v[:, ax].mean()
            cc = {L: np.dot(r[max(0, -L):len(r) - max(0, L)], q[max(0, L):len(q) - max(0, -L)]) for L in range(-12, 13)}
            lag = max(cc, key=cc.get)
            corr = cc[lag] / max(np.linalg.norm(r) * np.linalg.norm(q), 1e-9)
            print(f"     {k:<8} dy {amp(y):5.1f}px={100 * amp(y) / char_h:4.1f}% (top f{f0 + y.argmin()}, low f{f0 + y.argmax()})"
                  f"  dx {amp(x):5.1f}px  rot p5..p95 {np.percentile(a, 5):+.0f}..{np.percentile(a, 95):+.0f}deg"
                  f"  lag {lag:+d}f={lag / fps:+.2f}s on {'xy'[ax]} (r={corr:.2f})  match median {np.median(s):.2f}")
        chart([(k, 100 * (v[0, 1] - v[:, 1]) / char_h) for k, v in tr.items()], fps, f0, [], out / f"track_{label}.png",
              f"{label}: vertical offset vs f{f0} (% of char height, up = +)", shared=True)


def cell(frame, idx, fps):
    h, w = frame.shape[:2]
    im = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize((round(w * CELL_H / h), CELL_H), Image.LANCZOS)
    dr = ImageDraw.Draw(im)
    for y in (round(CELL_H * k / 10) for k in range(1, 10)):
        dr.line([(0, y), (12, y)], fill=(0, 255, 255)), dr.line([(im.width - 12, y), (im.width, y)], fill=(0, 255, 255))
    dr.rectangle([0, 0, im.width, 14], fill=(0, 0, 0))
    dr.text((3, 2), f"t={idx / fps:.2f}s f={idx}", fill=(255, 255, 0))
    return im


def sheet(frames, idxs, fps, out, cols=8):
    cells = [cell(frames[i], i, fps) for i in idxs]
    img = Image.new("RGB", ((cw := cells[0].width) * min(cols, len(cells)), CELL_H * -(-len(cells) // cols)), "white")
    for k, c in enumerate(cells):
        img.paste(c, ((k % cols) * cw, (k // cols) * CELL_H))
    img.save(out)


def chart(curves, fps, f0, cuts, out, title, shared=False, W=1000, H=280, PAD=30):
    """折線圖：x＝影格（下方標秒）。shared＝共用縱軸，否則每條各自縮放到滿版。"""
    img = Image.new("RGB", (W, H), "white")
    dr = ImageDraw.Draw(img)
    n, short = len(curves[0][1]), len(curves[0][1]) < 4 * fps
    X = lambda i: PAD + (W - 2 * PAD) * i / max(1, n - 1)
    lo, hi = min(c.min() for _, c in curves), max(c.max() for _, c in curves)
    for i in cuts:
        dr.line([(X(i), PAD), (X(i), H - PAD)], fill=(0, 0, 0))
    for k, (name, c) in enumerate(curves):
        a, b = (lo, hi) if shared else (c.min(), c.max())
        dr.line([(X(i), H - PAD - (H - 2 * PAD) * (v - a) / max(b - a, 1e-9)) for i, v in enumerate(c)], fill=COLORS[k % 7], width=2)
        dr.text((PAD + 70 * k, 16), name, fill=COLORS[k % 7])
    for i in range(0, n, max(1, round(fps / 4 if short else fps))):
        dr.line([(X(i), H - PAD), (X(i), H - PAD + 4)], fill=(0, 0, 0))
        dr.text((X(i) - 8, H - PAD + 6), f"{(f0 + i) / fps:.2f}s" if short else f"{(f0 + i) / fps:.0f}s", fill=(0, 0, 0))
    dr.text((PAD, 3), title + (f"  [axis {lo:.1f} .. {hi:.1f}]" if shared else ""), fill=(0, 0, 0))
    img.save(out)


def analyze(path, out_root):
    fps, frames = read(path)
    gray = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]).astype(np.float32)
    small = np.stack([cv2.resize(g, (SMALL, SMALL), interpolation=cv2.INTER_AREA) for g in gray])
    e = np.concatenate([[0.0], np.abs(np.diff(small, axis=0)).mean(axis=(1, 2))])  # e[i]＝影格 i 與 i−1 平均灰階差
    segs, nov, thr = segments(D := distances(small), e, fps)
    n, out = len(frames), out_root / slug(path.stem)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.png"):  # 分段可能改變，先清掉舊圖
        old.unlink()
    print(f"\n== {path.name} -> {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    print(f"   {fps:.3f} fps, {n} frames, {n / fps:.2f} s, {frames[0].shape[1]}x{frames[0].shape[0]}, energy thr {thr:.2f}")
    for k, (a, b, on) in enumerate(segs):
        p = period(D, a, b, fps)
        extra = f"  best lag {p[0]}f={p[0] / fps:.2f}s rms {p[1]:.2f}/worst {p[2]:.2f} -> {'LOOP' if p[3] else 'no loop'}" if p else ""
        print(f"   seg{k} {'motion' if on else 'still '} f{a}-f{b}  {a / fps:.2f}-{(b + 1) / fps:.2f}s  energy {e[a:b + 1].mean():.2f}{extra}")
        sheet(frames, list(range(a, b + 1, max(1, -(-(b - a + 1) // 32)))), fps, out / f"seg{k}_f{a}-f{b}.png")
        if p and p[3]:
            sheet(frames, list(range(a, min(n, a + p[0] + 1), max(1, -(-p[0] // 32)))), fps, out / f"loop{k}.png")
    sheet(frames, list(range(0, n, max(1, n // 32)))[:32], fps, out / "overview.png")
    chart([("energy", e), ("novelty", nov)], fps, 0, [a for a, _, _ in segs[1:]], out / "energy.png",
          f"frame-diff energy (max {e.max():.1f}/255), novelty; black = segment cuts")
    img = Image.fromarray((255 * D / max(D.max(), 1e-6)).astype(np.uint8)).resize((600, 600), Image.NEAREST).convert("RGB")
    [ImageDraw.Draw(img).text((round(t * fps * 600 / n) + 1, 2), f"{t}", fill=(255, 0, 0)) for t in range(int(n / fps) + 1)]
    img.save(out / "recurrence.png")
    mm = np.abs(np.diff(gray, axis=0)).mean(axis=0)
    Image.fromarray((255 * mm / max(mm.max(), 1e-6)).astype(np.uint8)).save(out / "motion_map.png")
    if slug(path.stem) in TRACK:
        report_track(gray, TRACK[slug(path.stem)], fps, out)


def main(src=ROOT / "Ref_pic" / "ref_video", out=ROOT / "docs" / "motion" / "frames"):
    assert slug("亡灵角色").startswith("v_") and slug("錄製_2026_11_19") == "2026_11_19"  # 非 ASCII 檔名也有穩定代號
    tex = cv2.GaussianBlur(np.random.default_rng(0).uniform(0, 255, (200, 200)).astype(np.float32), (0, 0), 3)
    moved = cv2.warpAffine(tex, cv2.getRotationMatrix2D((99.5, 99.5), -5, 1), (200, 200))  # 畫面上順時針 5°
    x, y, a, _ = track(np.stack([tex, moved]), 0, 1, (70, 70, 60, 60))[1]
    assert a == 5 and abs(x - 100) < 1.5 and abs(y - 100) < 1.5, (x, y, a)  # 追蹤器自我檢查
    for p in sorted(Path(src).glob("*.mp4")):
        analyze(p, Path(out))


if __name__ == "__main__":
    main(*sys.argv[1:3])
