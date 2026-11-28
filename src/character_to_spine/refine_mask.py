"""部件邊界貼齊：多邊形只是 Agent 目測的範圍，這裡把「看得見的邊界」貼到影像中實際的輪廓。

每個部件各自驗證：邊界上的影像邊緣強度有提高才採用，否則還原成原多邊形（觀察 → 修正 → 驗證 → 回退）。
被其他部件遮住的邊界是用猜的，不處理；以遮罩描述的部件已經是像素級，也不處理。
"""
import cv2
import numpy as np

from .analyzer import ALPHA_MIN

BAND = 0.012        # 窄帶寬度：角色高度的比例（下限 4px）。每一輪邊界最多移動這麼多
MAX_ITERS = 3       # 最多連續貼齊幾輪（多邊形常常差 20px 以上，一輪不夠）
MIN_GAIN = 1.02     # 邊界邊緣強度至少提高這個倍數才採用
MAX_CHANGE = 0.25   # 單輪面積變化超過部件面積的這個比例就不採用（GrabCut 把多色部件切碎了）
MIN_CHANGE = 0.002  # 變化小於這個比例視為已經準確，不動
GAP_REACH = 0.03     # 下層部件之間的縫寬在角色高度的 2×這個比例以內，才算「夾在中間」
GAP_MIN_AREA = 0.001  # 小於角色面積這個比例的縫不處理（多邊形轉角的幾個像素）


def _disk(r):
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


def _grabcut(rgb, mask, fg, locked, band):
    """窄帶 GrabCut：遮罩內縮 band 為確定前景、外擴 band 以外為確定背景，中間交給顏色模型。locked 的像素維持原歸屬。"""
    m8 = mask.astype(np.uint8)
    inner, outer = cv2.erode(m8, _disk(band)).astype(bool), cv2.dilate(m8, _disk(band)).astype(bool)
    tri = np.full(mask.shape, cv2.GC_BGD, np.uint8)
    tri[outer] = cv2.GC_PR_BGD
    tri[mask] = cv2.GC_PR_FGD
    tri[inner] = cv2.GC_FGD
    tri[~fg] = cv2.GC_BGD
    tri[locked & mask] = cv2.GC_FGD
    tri[locked & ~mask] = cv2.GC_BGD
    ys, xs = np.nonzero(outer)
    y0, y1, x0, x1 = max(0, ys.min() - 4), ys.max() + 5, max(0, xs.min() - 4), xs.max() + 5
    t = tri[y0:y1, x0:x1].copy()
    sure_bg = (t == cv2.GC_BGD) | (t == cv2.GC_PR_BGD)
    if not (t == cv2.GC_FGD).any() or not sure_bg.any() or not (t == cv2.GC_PR_FGD).any():
        return mask
    cv2.setRNGSeed(0)  # GrabCut 內部的 k-means 用亂數：固定種子，重跑結果才相同
    cv2.grabCut(np.ascontiguousarray(rgb[y0:y1, x0:x1]), t, None, np.zeros((1, 65)), np.zeros((1, 65)), 3, cv2.GC_INIT_WITH_MASK)
    out = mask.copy()
    out[y0:y1, x0:x1] = (t == cv2.GC_FGD) | (t == cv2.GC_PR_FGD)
    return out


def _edge_strength(mask, grad, zone):
    edge = mask & ~cv2.erode(mask.astype(np.uint8), _disk(1)).astype(bool) & zone
    return float(grad[edge].mean()) if edge.sum() >= 20 else 0.0


def refine_masks(rgba, parts, masks):
    """就地修改 masks。回傳 {部件: {applied, edge_before, edge_after, area_change, iterations, grown_px}}。"""
    fg = rgba[..., 3] > ALPHA_MIN
    if not fg.any():
        return {}
    ys = np.nonzero(fg.any(axis=1))[0]
    height = int(ys.max() - ys.min() + 1)
    band = max(4, round(BAND * height))
    rgb = np.where(fg[..., None], rgba[..., :3], 255).astype(np.uint8)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    grad = cv2.magnitude(cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3))
    report = {}
    above = np.zeros(fg.shape, bool)
    for p in sorted(parts, key=lambda p: -p["z"]):  # 由前到後：下層看得見的範圍取決於上層貼齊後的結果
        name = p["name"]
        if "polygon" in p and "mask" not in p and p.get("role") != "ground" and (masks[name] & fg & ~above).any():
            report[name] = _refine_one(rgb, grad, fg, masks, name, above, band)
        above |= masks[name]
    return report


def _refine_one(rgb, grad, fg, masks, name, above, band):
    original = masks[name].copy()
    current = original & fg
    zone = fg & ~above  # 這個部件看得見的範圍；以外的邊界不量、不動
    rec = {"applied": False, "edge_before": round(_edge_strength(current, grad, zone), 2), "iterations": 0}
    for _ in range(MAX_ITERS):
        new = _grabcut(rgb, current, fg, above, band)
        new = (new & zone) | (current & above)
        change = float((new ^ current).sum() / max(1, current.sum()))
        before, after = _edge_strength(current, grad, zone), _edge_strength(new, grad, zone)
        if change < MIN_CHANGE or change > MAX_CHANGE or after < before * MIN_GAIN:
            break  # 已經準確、切碎了、或沒有更貼近邊緣：保留目前的結果（第一輪就是原多邊形）
        current, rec["iterations"] = new, rec["iterations"] + 1
    rec["edge_after"] = round(_edge_strength(current, grad, zone), 2)
    if rec["iterations"]:
        rec.update(applied=True, area_change=round(float((current ^ (original & fg)).sum() / max(1, (original & fg).sum())), 4))
        masks[name] = current | (original & ~zone)
    return rec


def find_underlay_gaps(parts, masks, fg):
    """只被上層部件蓋住、底下沒有任何部件，而且夾在下層部件之間的區域（例如後髮與身體之間、被上臂蓋住的那一條）：
    上層一轉開就可能是透明的洞。只回報、不改遮罩：背後到底有沒有東西要看圖才知道（兩腿之間就是空的），
    由 Agent 決定要不要把下層部件的範圍延伸過去。回傳 [{covered_by, bbox, area, nearest_lower}]，大的在前。"""
    ys = np.nonzero(fg.any(axis=1))[0]
    if not len(ys):
        return []
    reach = max(3, round(GAP_REACH * (ys.max() - ys.min() + 1)))
    min_area = GAP_MIN_AREA * fg.sum()
    body = sorted((p for p in parts if p.get("role") not in ("ground", "effect")), key=lambda p: p["z"])
    found = []
    for i, p in enumerate(body[1:], 1):
        lower_names = [q["name"] for q in body[:i]]
        lower = np.any([masks[n] for n in lower_names], axis=0)
        closed = cv2.morphologyEx(np.pad(lower, reach).astype(np.uint8), cv2.MORPH_CLOSE, _disk(reach))[reach:-reach, reach:-reach].astype(bool)
        gap = masks[p["name"]] & fg & ~lower & closed
        n, labels, stats, _ = cv2.connectedComponentsWithStats(gap.astype(np.uint8), connectivity=8)
        for k in range(1, n):
            x, y, w, h, area = (int(v) for v in stats[k])
            if area < min_area:
                continue
            touch = cv2.dilate((labels == k).astype(np.uint8), _disk(2)).astype(bool)
            found.append({"covered_by": p["name"], "bbox": [x, y, w, h], "area": area,
                          "nearest_lower": [n for n in lower_names if (masks[n] & touch).any()]})
    return sorted(found, key=lambda g: -g["area"])
