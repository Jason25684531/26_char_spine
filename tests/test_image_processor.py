"""spec: image-processor"""
import hashlib
import json

import numpy as np
import pytest
from PIL import Image, ImageDraw

from character_to_spine import C2SError, load_json
from character_to_spine.analyzer import analyze
from character_to_spine.image_processor import MAX_AUTO_HIDDEN_RATIO, prepare


def meta_parts(wd):
    return {e["name"]: e for e in load_json(wd / "metadata.json")["parts"]}


@pytest.mark.parametrize("name", ["synth_a", "synth_b"])
def test_layer_positions_match_truth(built, synth, name):
    _, truth = synth(name)
    parts = meta_parts(built(name))
    for part, (x, y, w, h) in truth.items():
        e = parts[part]
        assert max(abs(e["x"] - x), abs(e["y"] - y), abs(e["w"] - w), abs(e["h"] - h)) <= 2, (part, e, truth[part])


@pytest.mark.parametrize("name", ["synth_a", "synth_b"])
def test_recompose_matches_source(built, name):
    assert load_json(built(name) / "metadata.json")["recompose_mae"] < 0.02


def test_stray_pixels_do_not_move_origin(synth, built, tmp_path):
    img, _ = synth("synth_a")
    noisy = tmp_path / "synth_a.png"
    im = Image.open(img)
    ImageDraw.Draw(im).ellipse([5, 5, 40, 40], fill=(255, 200, 0, 255))  # 散落的特效
    im.save(noisy)
    (tmp_path / "synth_a.parts.json").write_text(
        img.with_suffix(".parts.json").read_text(encoding="utf-8").replace('"synth_a_masks/', f'"{(img.parent / "synth_a_masks").as_posix()}/'),
        encoding="utf-8")
    analyze(noisy, tmp_path / "w")
    prepare(tmp_path / "w")
    clean, dirty = load_json(built("synth_a") / "metadata.json"), load_json(tmp_path / "w" / "metadata.json")
    assert dirty["origin"] == clean["origin"] and dirty["bbox"] == clean["bbox"]
    assert dirty["unassigned_ratio"] > 0
    for e in dirty["parts"]:
        layer = np.array(Image.open(tmp_path / "w" / e["file"]))
        assert e["x"] > 40 or e["y"] > 40 or layer[..., 3].max() == 0


def test_small_occlusion_auto_repaired(built, synth):
    wd = built("synth_b")
    body = meta_parts(wd)["body"]
    assert body["status"] == "auto_repaired" and 0 < body["hidden_ratio"] <= MAX_AUTO_HIDDEN_RATIO
    ax, ay, aw, ah = synth("synth_b")[1]["arm_l"]
    # arm_l 蓋住 body 左緣：那裡的 body 圖層要有不透明的填補像素
    layer = np.array(Image.open(wd / body["file"]))
    assert layer[ay + ah // 2 - body["y"], ax + aw - 1 - body["x"], 3] == 255


def test_large_occlusion_needs_manual(built):
    wd = built("synth_b")
    hair = meta_parts(wd)["hair_back"]
    assert hair["status"] == "needs_manual" and hair["hidden_ratio"] > MAX_AUTO_HIDDEN_RATIO
    assert (wd / hair["file"]).exists()  # 仍有草稿圖層
    assert [m["name"] for m in load_json(wd / "missing_parts.json")["needs_manual"]] == ["hair_back"]
    tasks = (wd / "repair_tasks.md").read_text(encoding="utf-8")
    assert "hair_back" in tasks and "c2s prepare --replace hair_back=" in tasks and "layers/hair_back.png" in tasks
    assert "420x360" in tasks


def test_fully_hidden_part(synth, tmp_path):
    img, _ = synth("synth_a")
    doc = json.loads(img.with_suffix(".parts.json").read_text(encoding="utf-8"))
    for p in doc["parts"]:
        p["mask"] = str(img.parent / p["mask"])
    doc["parts"].append({"name": "badge", "polygon": [[130, 220], [170, 220], [170, 260], [130, 260]], "z": 2.5})
    path = tmp_path / "p.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    analyze(img, tmp_path / "w", parts_path=path)
    r = prepare(tmp_path / "w")
    badge = meta_parts(tmp_path / "w")["badge"]
    assert badge["status"] == "needs_manual" and "file" not in badge and "badge" in r["needs_manual"]
    assert not (tmp_path / "w" / "layers" / "badge.png").exists()
    assert "整張重畫" in (tmp_path / "w" / "repair_tasks.md").read_text(encoding="utf-8")


def test_layer_preview(built):
    wd = built("synth_b")
    assert Image.open(wd / "layer_preview.png").size == (420 * 3 + 20, 360)


def _hashes(wd):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (wd / "layers").glob("*.png")}


def test_only_one_part(workcopy):
    wd = workcopy("synth_b")
    before = _hashes(wd)
    mtimes = {p.name: p.stat().st_mtime_ns for p in (wd / "layers").glob("*.png")}
    r = prepare(wd, only="head")
    assert r["written"] == ["head"]
    assert _hashes(wd) == before
    assert all(p.stat().st_mtime_ns == mtimes[p.name] for p in (wd / "layers").glob("*.png") if p.name != "head.png")
    assert len(meta_parts(wd)) == 8


def test_partial_rerun_equals_full(workcopy):
    """改了一個部件，被它遮住的其他部件也要跟著重算（審查發現：舊版會沿用過期的結果）。"""
    wd = workcopy("synth_b")
    doc = load_json(wd / "parts.json")
    for p in doc["parts"]:
        if p["name"] == "arm_l":
            p["polygon"] = [[110, 195], [130, 195], [130, 265], [110, 265]]  # 手臂縮小，不再蓋住身體
    (wd / "parts.json").write_text(json.dumps(doc), encoding="utf-8")
    r = prepare(wd, only="arm_l")
    assert "body" in r["written"] and meta_parts(wd)["body"]["hidden_ratio"] < 0.1


def test_replace_canvas_size_and_persist(workcopy, tmp_path):
    wd = workcopy("synth_a")
    fixed = tmp_path / "fixed.png"
    canvas = Image.new("RGBA", (300, 420), (0, 0, 0, 0))
    ImageDraw.Draw(canvas).rectangle([60, 170, 112, 290], fill=(0, 255, 0, 255))
    canvas.save(fixed)
    prepare(wd, replace={"arm_l": fixed})
    e = meta_parts(wd)["arm_l"]
    assert e["status"] == "replaced" and (e["x"], e["y"], e["w"], e["h"]) == (60, 170, 53, 121)
    prepare(wd)  # 重跑仍保留
    e = meta_parts(wd)["arm_l"]
    assert e["status"] == "replaced"
    assert tuple(np.array(Image.open(wd / e["file"]))[5, 5]) == (0, 255, 0, 255)


def test_replace_layer_size(workcopy, tmp_path):
    wd = workcopy("synth_a")
    e = meta_parts(wd)["head"]
    fixed = tmp_path / "head.png"
    Image.new("RGBA", (e["w"], e["h"]), (9, 9, 9, 255)).save(fixed)
    prepare(wd, replace={"head": fixed})
    e2 = meta_parts(wd)["head"]
    assert e2["status"] == "replaced" and (e2["x"], e2["y"]) == (e["x"], e["y"])


def test_replace_wrong_size(workcopy, tmp_path):
    wd = workcopy("synth_a")
    before = (wd / "layers" / "head.png").read_bytes()
    bad = tmp_path / "bad.png"
    Image.new("RGBA", (7, 7), (9, 9, 9, 255)).save(bad)
    with pytest.raises(C2SError, match="300x420"):
        prepare(wd, replace={"head": bad})
    assert (wd / "layers" / "head.png").read_bytes() == before
    prepare(wd)  # 錯誤的替換圖不能殘留下來害之後每次都失敗
    assert meta_parts(wd)["head"]["status"] == "ok"


def test_removed_part_leaves_no_stale_layer(workcopy):
    wd = workcopy("synth_b")
    doc = load_json(wd / "parts.json")
    doc["parts"] = [p for p in doc["parts"] if p["name"] != "flag"]
    (wd / "parts.json").write_text(json.dumps(doc), encoding="utf-8")
    prepare(wd)
    assert not (wd / "layers" / "flag.png").exists()


def test_replace_with_non_image(workcopy, tmp_path):
    wd = workcopy("synth_a")
    bad = tmp_path / "notes.png"
    bad.write_text("not an image", encoding="utf-8")
    with pytest.raises(C2SError, match="不是可讀取的圖片"):
        prepare(wd, replace={"head": bad})
    assert not (wd / "overrides" / "head.png").exists()


def test_ground_shadow_keeps_only_shadow_pixels(tmp_path):
    """影子多邊形多畫到腳尖（腿的多邊形沒畫到）：那些不像影子的像素要歸給腿，否則跳起時腳尖會留在地上。"""
    from synthetic import make_custom, rect
    leg = (60, 80, 160)
    img = make_custom(tmp_path, "g", (300, 420), [
        ("shadow", [[80, 378], [220, 378], [220, 402], [80, 402]], (110, 110, 110), 0, {"role": "ground"}),
        ("leg_l", rect(115, 280, 143, 390), leg, 1, {}), ("leg_r", rect(157, 280, 185, 390), leg, 2, {}),
        ("body", rect(105, 175, 195, 300), (220, 80, 80), 3, {}), ("head", rect(100, 60, 200, 180), (250, 220, 190), 4, {}),
        ("arm_l", rect(72, 180, 110, 280), (235, 185, 145), 5, {}), ("arm_r", rect(190, 180, 228, 280), (240, 195, 155), 6, {})])
    doc = json.loads(img.with_suffix(".parts.json").read_text(encoding="utf-8"))
    for p in doc["parts"]:
        if p["name"].startswith("leg_"):
            p["polygon"] = [[x, min(y, 375)] for x, y in p["polygon"]]  # 腳尖 376–390 只落在影子的多邊形裡
    img.with_suffix(".parts.json").write_text(json.dumps(doc), encoding="utf-8")
    wd = tmp_path / "w"
    analyze(img, wd)
    prepare(wd)
    meta = {e["name"]: e for e in load_json(wd / "metadata.json")["parts"]}
    shadow = np.array(Image.open(wd / "layers" / "shadow.png").convert("RGBA")).astype(int)
    leg_like = (shadow[..., 3] > 0) & (np.abs(shadow[..., :3] - leg).sum(axis=2) < 30)
    assert leg_like.sum() == 0
    assert meta["leg_l"]["y"] + meta["leg_l"]["h"] >= 390  # 腳尖回到腿的圖層
