"""部件邊界貼齊：看得見的邊界貼到影像邊緣、被遮住的邊界不動、沒有改善就還原、後髮往上層底下延伸。"""
import numpy as np

from character_to_spine import refine_mask
from character_to_spine.refine_mask import refine_masks

RED, SKIN, BROWN = (200, 40, 40), (240, 190, 150), (90, 50, 30)


def scene():
    """200x260：後髮（棕）在最後、身體（紅）、手臂（膚色）在最前並蓋住身體左側。回傳 (rgba, 真實範圍)。"""
    h, w = 260, 200
    truth = {n: np.zeros((h, w), bool) for n in ("hair", "body", "arm")}
    truth["hair"][20:120, 40:160] = True
    truth["body"][100:240, 70:150] = True
    truth["arm"][110:210, 50:90] = True
    rgba = np.zeros((h, w, 4), np.uint8)
    for name, color in (("hair", BROWN), ("body", RED), ("arm", SKIN)):  # 由後到前畫
        rgba[truth[name]] = (*color, 255)
    return rgba, truth


def parts_and_masks(truth, arm_extra=0):
    arm = truth["arm"].copy()
    if arm_extra:  # 多邊形畫得比實際寬：右側多框進 arm_extra 像素的身體
        arm[110:210, 90:90 + arm_extra] = True
    parts = [{"name": "hair", "z": 0, "role": "hair", "polygon": []}, {"name": "body", "z": 1, "polygon": []},
             {"name": "arm", "z": 2, "polygon": []}]
    return parts, {"hair": truth["hair"].copy(), "body": truth["body"].copy(), "arm": arm}


def test_polygon_drawn_too_wide_is_pulled_back():
    rgba, truth = scene()
    parts, masks = parts_and_masks(truth, arm_extra=4)
    report = refine_masks(rgba, parts, masks)
    extra = masks["arm"] & ~truth["arm"]
    assert extra.sum() <= 20, extra.sum()  # 多框的 400 個紅色像素歸還給身體
    assert (masks["arm"] & truth["arm"]).sum() >= 0.98 * truth["arm"].sum()
    assert report["arm"]["applied"] and report["arm"]["edge_after"] > report["arm"]["edge_before"]


def test_accurate_boundary_is_left_alone():
    rgba, truth = scene()
    parts, masks = parts_and_masks(truth)
    before = {n: m.copy() for n, m in masks.items()}
    refine_masks(rgba, parts, masks)
    assert np.array_equal(masks["arm"], before["arm"]) and np.array_equal(masks["body"] & ~before["arm"], before["body"] & ~before["arm"])


def test_hidden_boundary_is_not_touched():
    """身體被手臂蓋住的那一段範圍是用猜的：貼齊不能依手臂的影像去改它。"""
    rgba, truth = scene()
    parts, masks = parts_and_masks(truth)
    under_arm = masks["body"] & masks["arm"]
    refine_masks(rgba, parts, masks)
    assert np.array_equal(masks["body"] & masks["arm"], under_arm)


def test_worse_result_is_rolled_back(monkeypatch):
    rgba, truth = scene()
    parts, masks = parts_and_masks(truth, arm_extra=4)
    before = masks["arm"].copy()
    monkeypatch.setattr(refine_mask, "_grabcut", lambda rgb, mask, fg, locked, band: np.roll(mask, 9, axis=1))  # 整塊偏掉
    report = refine_masks(rgba, parts, masks)
    assert np.array_equal(masks["arm"], before) and not report["arm"]["applied"]


def test_mask_parts_and_ground_are_skipped():
    rgba, truth = scene()
    parts, masks = parts_and_masks(truth, arm_extra=4)
    parts[2] = {"name": "arm", "z": 2, "mask": "arm.png"}  # 以遮罩描述的部件已經是像素級，不處理
    before = masks["arm"].copy()
    report = refine_masks(rgba, parts, masks)
    assert np.array_equal(masks["arm"], before) and "arm" not in report


def gap_scene():
    """後髮一束垂在左邊、身體在右邊，中間 12px 的縫被手臂蓋住；手臂另有一段伸到身體外側的空白處。"""
    h, w = 260, 200
    masks = {"hair": np.zeros((h, w), bool), "body": np.zeros((h, w), bool), "arm": np.zeros((h, w), bool)}
    masks["hair"][20:200, 30:68] = True      # 垂下來的髮束
    masks["hair"][20:100, 30:160] = True     # 頭後方的大片頭髮
    masks["body"][100:240, 80:150] = True
    masks["arm"][110:190, 55:95] = True      # 蓋住髮束與身體之間的縫（x 68~80）
    masks["arm"][200:250, 150:190] = True    # 伸到身體右側外面：旁邊是空的
    fg = masks["hair"] | masks["body"] | masks["arm"]
    parts = [{"name": "hair", "z": 0, "role": "hair"}, {"name": "body", "z": 1}, {"name": "arm", "z": 2}]
    return parts, masks, fg


def test_gap_between_lower_parts_under_the_arm_is_reported():
    """夾在後髮與身體之間、只有手臂蓋著的那一條：回報位置與相鄰的下層部件，遮罩本身不改（背後有沒有東西要看圖）。"""
    from character_to_spine.refine_mask import find_underlay_gaps
    parts, masks, fg = gap_scene()
    before = {n: m.copy() for n, m in masks.items()}
    gaps = find_underlay_gaps(parts, masks, fg)
    assert len(gaps) == 1, gaps  # 身體外側、旁邊是空的那一段不算
    g = gaps[0]
    x, y, w, h = g["bbox"]
    assert g["covered_by"] == "arm" and set(g["nearest_lower"]) == {"hair", "body"}
    assert 66 <= x <= 70 and x + w <= 82 and 108 <= y and y + h <= 192
    assert all(np.array_equal(masks[n], before[n]) for n in masks)


def test_no_gap_nothing_reported():
    from character_to_spine.refine_mask import find_underlay_gaps
    rgba, truth = scene()
    parts, masks = parts_and_masks(truth)
    assert find_underlay_gaps(parts, masks, rgba[..., 3] > 0) == []
