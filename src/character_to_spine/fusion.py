"""生成式補圖的融合：把任意大小的生成圖對齊回原圖座標，只取被遮住的像素，原始可見像素原樣保留。

圖像生成工具（例如 Codex 內建 image_gen）沒有遮罩與輸出座標控制，所以對齊、裁切、接縫都在這裡做。
"""
import cv2
import numpy as np

# 門檻在面試角色三項實驗後校準並凍結，依據見 docs/DECISIONS.md D-60。不得為個別角色調整。
VISIBLE_MAE_MAX = 0.10   # 對齊後，部件看得見的像素與原圖的平均誤差（0~1）：超過代表沒對齊或被改畫
OCCLUDER_COPY_MAX = 0.60  # 被遮住的區域裡，生成圖與原圖（也就是遮擋者）幾乎相同的比例：超過代表只是照抄
SEAM_DELTA_MAX = 0.12    # 緊貼被遮區的可見帶上，生成圖與原圖的誤差（0~1）：接縫旁對不上，補上的像素接過去就會斷
COVERAGE_MIN = 0.30      # 被遮住的區域裡，生成圖不透明的比例：太低代表生成圖在那裡沒有內容
MIN_VISIBLE = 200        # 看得見的像素少於這個數，無法可靠地對齊
MARKER = (255, 0, 255)   # 交給 image_gen 前把要補的區域塗成這個顏色；生成圖裡沒被填掉的標記色不算生成內容
SEAM_BAND = 6            # 接縫帶寬（px）
ALIGN_BAND = 40          # 對齊優先使用被遮區周圍這個範圍內的可見像素：生成圖常局部重畫，遠處的偏移和接縫處不同
PRECOMPOSITED_MAE = 0.002  # 與畫布同尺寸、可見區誤差低於這個值：檔案已經貼回原圖，量測失效

SEARCH_SIDE = 360  # 粗搜尋時把畫布縮到這個長邊


def _over_gray(rgba):
    a = rgba[..., 3:4].astype(np.float32) / 255
    return rgba[..., :3].astype(np.float32) * a + 128 * (1 - a)


def _resize(img, s):
    h, w = img.shape[:2]
    size = (max(1, round(w * s)), max(1, round(h * s)))
    return cv2.resize(img, size, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)


def _match(gen_rgb, templ, mask, prior):
    """在 gen_rgb 裡找 templ（只比 mask 的像素）。回傳 (平均平方誤差 0~1, 模板左上角在 gen_rgb 的位置)。
    prior：預期位置；分數幾乎相同（單色區塊）時選最接近預期的。"""
    th, tw = templ.shape[:2]
    pad = ((th, th), (tw, tw), (0, 0))
    img = np.pad(gen_rgb, pad, constant_values=128)
    res = cv2.matchTemplate(img, templ, cv2.TM_SQDIFF, mask=np.repeat(mask[..., None], 3, 2).astype(np.float32))
    res = res / (mask.sum() * 3 * 255.0 ** 2)
    yy, xx = np.mgrid[0:res.shape[0], 0:res.shape[1]]
    res = res + 1e-5 * np.hypot(xx - (prior[0] + tw), yy - (prior[1] + th))
    _, _, loc, _ = cv2.minMaxLoc(res)
    return float(res[loc[1], loc[0]]), (loc[0] - tw, loc[1] - th)


def align(src_rgba, visible, gen_rgba):
    """估計縮放與位移，回傳 (s, ox, oy)：畫布像素 (x, y) 對應生成圖 ((x-ox)/s, (y-oy)/s)。
    shortcut: 只估縮放＋位移，不含旋轉；生成圖若把部件轉了角度會對不齊而被拒絕，需要時再加旋轉搜尋。"""
    H, W = visible.shape
    gh, gw = gen_rgba.shape[:2]
    s0 = min(W / gw, H / gh)
    fit = ((W - gw * s0) / 2, (H - gh * s0) / 2)
    ys, xs = np.nonzero(visible)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    src_rgb = _over_gray(src_rgba)

    def search(f, scales, prior_shift, around=None):
        templ = cv2.resize(src_rgb[y0:y1, x0:x1], None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
        mask = cv2.resize(visible[y0:y1, x0:x1].astype(np.float32), (templ.shape[1], templ.shape[0]), interpolation=cv2.INTER_AREA) > 0.99
        best = None
        for s in scales:
            g = _over_gray(_resize(gen_rgba, s * f))
            ox, oy = prior_shift(s)
            prior = (x0 * f - ox * f, y0 * f - oy * f)  # 模板左上角在縮放後生成圖的預期位置
            if around is not None:  # 只在預期位置附近搜尋
                r = around
                gx0, gy0 = max(0, int(prior[0]) - r), max(0, int(prior[1]) - r)
                g = g[gy0:int(prior[1]) + templ.shape[0] + r, gx0:int(prior[0]) + templ.shape[1] + r]
                score, (lx, ly) = _match(g, templ, mask, (prior[0] - gx0, prior[1] - gy0))
                lx, ly = lx + gx0, ly + gy0
            else:
                score, (lx, ly) = _match(g, templ, mask, prior)
            score += 1e-3 * abs(np.log(s / s0))  # 單色部件在任何縮放下都對得上：偏好與原圖同構圖
            cand = (score, s, (x0 * f - lx) / f, (y0 * f - ly) / f)
            best = cand if best is None or cand[0] < best[0] else best
        return best

    f = min(1.0, SEARCH_SIDE / max(H, W))
    coarse = search(f, s0 * np.linspace(0.7, 1.3, 25), lambda s: (fit[0] + gw * (s0 - s) / 2, fit[1] + gh * (s0 - s) / 2))
    _, s1, ox1, oy1 = coarse
    fine = search(1.0, s1 * np.linspace(0.98, 1.02, 5),
                  lambda s: (ox1 + (x0 - ox1) * (1 - s / s1), oy1 + (y0 - oy1) * (1 - s / s1)), around=int(3 / f) + 3)
    return fine[1], fine[2], fine[3]


def _warp(gen_rgba, s, ox, oy, size):
    g = _resize(gen_rgba, s)
    return cv2.warpAffine(g, np.float32([[1, 0, ox], [0, 1, oy]]), size, flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


def _visible_error(gen, src, check):
    """對齊後的生成圖在 check 像素上與原圖的誤差（整體色偏校正後）。回傳 (誤差圖, 校正後的 RGB, 色偏)。"""
    opaque = gen[..., 3] > 128
    rgb = gen[..., :3].astype(np.float32)
    both = check & opaque
    shift = (src[both] - rgb[both]).mean(0) if both.any() else np.zeros(3, np.float32)
    rgb = np.clip(rgb + shift, 0, 255)  # 整體色偏校正：生成圖的亮度、色溫常和原圖差一點
    err = np.ones(check.shape, np.float32)
    err[both] = np.abs(rgb[both] - src[both]).mean(-1) / 255
    return err, rgb, shift


def fuse(src_rgba, part, above, gen_rgba):
    """src_rgba：原圖（HxWx4）；part：部件範圍（HxW bool）；above：前後順序較高的部件範圍；gen_rgba：生成圖（任意大小）。
    回傳 (整張畫布大小的部件圖層 RGBA, 量測值)。量測值用 judge() 判定。"""
    H, W = part.shape
    fg = src_rgba[..., 3] > 0
    mine = part & fg
    visible, hidden = mine & ~above, mine & above
    solid = visible & (src_rgba[..., 3] > 200)
    m = {"visible_px": int(solid.sum()), "hidden_px": int(hidden.sum())}
    out = np.zeros((H, W, 4), np.uint8)
    out[visible] = src_rgba[visible]
    if not hidden.any():
        return out, m
    k = 2 * ALIGN_BAND + 1
    around = cv2.dilate(hidden.astype(np.uint8), np.ones((k, k), np.uint8)).astype(bool)
    # 生成工具被要求只改被遮區（洋紅色），其餘畫面不動：部件自己看得見的像素太少時，用被遮區周圍的整個畫面來對齊與查核
    context = (src_rgba[..., 3] > 200) & ~hidden & around
    near = solid & around
    anchors = [("part", near if near.sum() >= MIN_VISIBLE else solid), ("context", context)]
    check = solid if solid.sum() >= MIN_VISIBLE else context
    m["checked_on"] = "part" if check is solid else "context"
    if check.sum() < MIN_VISIBLE:
        return out, m
    src = src_rgba[..., :3].astype(np.float32)
    best = None
    for label, anchor in anchors:
        if anchor.sum() < MIN_VISIBLE:
            continue
        s, ox, oy = align(src_rgba, anchor, gen_rgba)
        gen = _warp(gen_rgba, s, ox, oy, (W, H))
        err, rgb, shift = _visible_error(gen, src, check)
        cand = (float(err[check].mean()), label, s, ox, oy, gen, err, rgb, shift)
        best = cand if best is None or cand[0] < best[0] else best
    _, label, s, ox, oy, gen, err, rgb, shift = best
    opaque = gen[..., 3] > 128
    m["same_canvas"] = gen_rgba.shape[:2] == (H, W)
    m.update(aligned_by=label, scale=round(float(s), 4), offset=[round(float(ox), 1), round(float(oy), 1)],
             color_shift=round(float(np.abs(shift).mean() / 255), 4), visible_mae=round(float(err[check].mean()), 4))
    same = np.abs(rgb - src).mean(-1) / 255 < 0.06
    m["occluder_copy"] = round(float(same[hidden & opaque].mean()), 4) if (hidden & opaque).any() else 0.0
    marker = np.abs(gen[..., :3].astype(np.float32) - MARKER).max(-1) < 40
    # 生成圖在這裡和原圖的遮擋者幾乎一樣（沒有移除那個遮擋者）：這些像素不能進圖層，否則遮擋者移開後留下殘影
    copied = hidden & opaque & same
    fill = hidden & opaque & ~same & ~marker
    m["coverage"] = round(float(fill.sum() / hidden.sum()), 4)
    # 接縫：緊貼被遮區的可見帶上，生成圖對原圖的誤差。只比較同一位置的像素，不受材質交界（皮膚接花環）影響
    kb = 2 * SEAM_BAND + 1
    band = check & cv2.dilate(hidden.astype(np.uint8), np.ones((kb, kb), np.uint8)).astype(bool)
    m["seam_delta"] = round(float(err[band].mean()), 4) if band.any() else 0.0
    out[fill, :3] = rgb[fill].round().astype(np.uint8)
    out[fill, 3] = gen[fill, 3]
    if copied.any():  # 用周圍已確定的像素（原圖可見＋生成）邊緣延伸
        known = (visible | fill) & ~copied
        out[copied, :3] = cv2.inpaint(np.ascontiguousarray(out[..., :3]), (~known).astype(np.uint8) * 255, 3, cv2.INPAINT_TELEA)[copied]
        out[copied, 3] = 255
    m["copied_px"] = int(copied.sum())
    return out, m


def judge(m):
    """回傳不通過的原因（空清單＝通過）。"""
    if m.get("hidden_px", 0) == 0:
        return ["這個部件沒有被遮住的區域，不需要補圖"]
    if "visible_mae" not in m:
        return [f"部件看得見的像素只有 {m['visible_px']}，被遮區周圍也沒有足夠的畫面可以對齊"]
    reasons = []
    if m.get("same_canvas") and m["visible_mae"] < PRECOMPOSITED_MAE:
        reasons.append("檔案與原圖同尺寸、看得見的像素完全相同：已經貼回原圖，無法量測。請改用 image_gen 的原始輸出檔，不要先自行合成")
    if m["visible_mae"] > VISIBLE_MAE_MAX:
        reasons.append(f"可見區域對齊後誤差 {m['visible_mae']} > {VISIBLE_MAE_MAX}（沒對齊，或比例、五官、服裝被改畫）")
    if m["occluder_copy"] > OCCLUDER_COPY_MAX:
        reasons.append(f"被遮住的區域有 {m['occluder_copy']:.0%} 和原圖的遮擋者相同（> {OCCLUDER_COPY_MAX:.0%}），生成圖沒有移除遮擋者")
    if m["coverage"] < COVERAGE_MIN:
        reasons.append(f"被遮住的區域只有 {m['coverage']:.0%} 有生成內容（< {COVERAGE_MIN:.0%}）")
    if m["seam_delta"] > SEAM_DELTA_MAX:
        reasons.append(f"接縫色差 {m['seam_delta']} > {SEAM_DELTA_MAX}（畫風或光影不一致）")
    return reasons
