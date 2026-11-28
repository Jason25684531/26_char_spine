"""生成式補圖：對齊、原始可見像素不變、拒絕重繪與只複製遮擋者、許可、來源紀錄、重做上限。"""
import json

import numpy as np
import pytest
from PIL import Image

from character_to_spine import C2SError, NeedsInput, load_json
from character_to_spine.fusion import fuse, judge
from character_to_spine.image_processor import grant_consent, overrides_dir, prepare


def textured(h, w, seed=0):
    """平滑但有特徵的紋理：漸層加幾個色塊，讓對齊有唯一解。"""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w]
    img = np.stack([120 + 60 * np.sin(xx / 9.0), 80 + 50 * np.cos(yy / 7.0), 140 + 40 * np.sin((xx + yy) / 11.0)], -1)
    for _ in range(12):
        x, y, r = rng.integers(0, w), rng.integers(0, h), rng.integers(4, 10)
        img[max(0, y - r):y + r, max(0, x - r):x + r] = rng.integers(0, 255, 3)
    return img.clip(0, 255).astype(np.uint8)


def scene():
    """200x200：身體（紋理）z 低、吉他（單色）蓋在中央。回傳 (原圖 RGBA, 身體真值 RGBA, 身體範圍, 遮擋者範圍)。"""
    h = w = 200
    body = np.zeros((h, w), bool)
    body[40:180, 50:150] = True
    guitar = np.zeros((h, w), bool)
    guitar[80:140, 70:170] = True
    tex = textured(h, w)
    truth = np.zeros((h, w, 4), np.uint8)
    truth[body] = np.concatenate([tex[body], np.full((body.sum(), 1), 255, np.uint8)], 1)
    src = truth.copy()
    src[guitar] = (200, 160, 90, 255)
    return src, truth, body, guitar


def place(rgba, scale, dx, dy, canvas):
    """模擬 ImageGen：同一個畫面放大 scale 倍、偏移 (dx, dy) 原圖像素。"""
    big = np.array(Image.fromarray(rgba).resize((round(rgba.shape[1] * scale), round(rgba.shape[0] * scale)), Image.BICUBIC))
    out = np.zeros((round(canvas[0] * scale), round(canvas[1] * scale), 4), np.uint8)
    ox, oy = round(dx * scale), round(dy * scale)
    ys, xs = slice(max(0, oy), min(out.shape[0], oy + big.shape[0])), slice(max(0, ox), min(out.shape[1], ox + big.shape[1]))
    out[ys, xs] = big[ys.start - oy:ys.stop - oy, xs.start - ox:xs.stop - ox]
    return out


def test_fuse_keeps_visible_and_fills_hidden():
    src, truth, body, guitar = scene()
    gen = place(truth, 2.6, 6, -4, (200, 200))
    gen[..., :3] = np.clip(gen[..., :3].astype(int) + 8, 0, 255)  # 生成圖整體偏亮一點
    out, m = fuse(src, body, guitar, gen)
    visible = body & ~guitar
    assert np.array_equal(out[visible], src[visible])  # 原始可見像素逐像素相同
    hidden = body & guitar
    err = np.abs(out[hidden][:, :3].astype(int) - truth[hidden][:, :3]).mean() / 255
    assert err < 0.05, (err, m)
    assert judge(m) == []
    assert not out[~body][..., 3].any()  # 部件範圍外不留任何生成像素


def test_fuse_rejects_redraw():
    src, truth, body, guitar = scene()
    other = truth.copy()
    redrawn = textured(200, 200, seed=7).transpose(1, 0, 2)  # 花紋方向與位置都不同：服裝被改畫
    other[body] = np.concatenate([redrawn[body], np.full((body.sum(), 1), 255, np.uint8)], 1)
    _, m = fuse(src, body, guitar, place(other, 2.0, 0, 0, (200, 200)))
    assert any("可見區域" in r for r in judge(m)), m


def test_fuse_rejects_occluder_copy():
    src, truth, body, guitar = scene()
    _, m = fuse(src, body, guitar, place(src, 2.0, 0, 0, (200, 200)))  # 原圖照抄：被擋住的地方還是吉他
    assert any("遮擋者" in r for r in judge(m)), m


# --- prepare --generated（流程層） ---

def meta_parts(wd):
    return {e["name"]: e for e in load_json(wd / "metadata.json")["parts"]}


def body_truth(tmp_path):
    """synth_a 的身體完整樣貌（整張畫布、透明背景），放大 3 倍模擬 ImageGen 的解析度。"""
    canvas = Image.new("RGBA", (300, 420), (0, 0, 0, 0))
    canvas.paste((220, 80, 80, 255), (105, 175, 196, 301))
    path = tmp_path / "gen_body.png"
    canvas.resize((900, 1260), Image.NEAREST).save(path)
    return path


def test_generated_requires_consent(workcopy, tmp_path):
    wd = workcopy("synth_a")
    before = {p.name: p.read_bytes() for p in (wd / "layers").glob("*.png")}
    with pytest.raises(C2SError, match="許可"):
        prepare(wd, generated=("body", body_truth(tmp_path), "prompt"))
    assert {p.name: p.read_bytes() for p in (wd / "layers").glob("*.png")} == before
    assert not overrides_dir(wd, load_json(wd / "parts.json")).exists()


def test_generated_accepted_only_changes_that_part(workcopy, tmp_path):
    wd = workcopy("synth_a")
    before = {p.name: p.read_bytes() for p in (wd / "layers").glob("*.png")}
    grant_consent(wd)
    prepare(wd, generated=("body", body_truth(tmp_path), "synth body, transparent background"))
    e = meta_parts(wd)["body"]
    assert e["status"] == "ai_repaired"
    after = {p.name: p.read_bytes() for p in (wd / "layers").glob("*.png")}
    assert {n for n in after if after[n] != before.get(n)} == {"body.png"}
    prov = load_json(overrides_dir(wd, load_json(wd / "parts.json")) / "provenance.json")
    att = prov["parts"]["body"]["attempts"]
    assert len(att) == 1 and att[0]["verdict"] == "pass" and att[0]["prompt"].startswith("synth body")
    assert att[0]["tool"] and att[0]["source"] == "generated"
    # 刪掉圖層重跑：不帶生成圖也得到相同結果
    layer = after["body.png"]
    for p in (wd / "layers").glob("*.png"):
        p.unlink()
    prepare(wd)
    assert (wd / "layers" / "body.png").read_bytes() == layer
    assert meta_parts(wd)["body"]["status"] == "ai_repaired"
    assert "ai_repaired" in (wd / "repair_tasks.md").read_text(encoding="utf-8")


def test_reference_source_needs_no_consent(workcopy, tmp_path):
    wd = workcopy("synth_a")
    prepare(wd, generated=("body", body_truth(tmp_path), None), reference="other_pose.png")
    assert meta_parts(wd)["body"]["status"] == "ref_repaired"


def test_three_rejects_become_needs_manual(workcopy, synth, tmp_path):
    wd = workcopy("synth_a")
    grant_consent(wd)

    def copy(n):  # 原圖照抄：每次都會因為複製遮擋者被拒絕。每次是不同的檔案（v1.2.1：同一個檔案重複匯入只算一次）
        img = Image.open(synth("synth_a")[0]).convert("RGBA")
        img.putpixel((0, 0), (n, n, n, 0))
        img.save(tmp_path / f"copy{n}.png")
        return tmp_path / f"copy{n}.png"
    for i in range(2):
        with pytest.raises(NeedsInput, match=f"還可重試 {2 - i} 次"):
            prepare(wd, generated=("body", copy(i), "p"))
    prepare(wd, generated=("body", copy(2), "p"))  # 第 3 次：不再要求重試，改列人工
    e = meta_parts(wd)["body"]
    assert e["status"] == "needs_manual" and "3 次" in e["reason"]
    assert "body" in (wd / "repair_tasks.md").read_text(encoding="utf-8")
    with pytest.raises(C2SError, match="上限"):
        prepare(wd, generated=("body", copy(3), "p"))
    prov = load_json(overrides_dir(wd, load_json(wd / "parts.json")) / "provenance.json")
    assert [a["verdict"] for a in prov["parts"]["body"]["attempts"]] == ["reject"] * 3
    odir = overrides_dir(wd, load_json(wd / "parts.json"))
    assert all((odir / a["fused_candidate"]).exists() for a in prov["parts"]["body"]["attempts"])  # 留給人工判斷
    assert json.dumps(prov, ensure_ascii=False).count("遮擋者") >= 3


def test_fuse_rejects_precomposited_file():
    """交來的檔案已經把原圖貼回去（與畫布同尺寸、可見像素完全相同）：量測全部失效，必須拒絕並要求原始生成檔。"""
    src, truth, body, guitar = scene()
    composited = src.copy()
    composited[body & guitar] = truth[body & guitar]
    _, m = fuse(src, body, guitar, composited)
    assert any("原始輸出" in r for r in judge(m)), m



def test_prepare_writes_marked_inputs_for_image_gen(workcopy):
    """需要補圖的部件：prepare 輸出 gen_inputs/<部件>.png，被遮住的區域塗成標記色，其他像素與原圖相同。
    Agent 直接把這張圖交給 image_gen，不需要自己寫程式處理圖片。"""
    from character_to_spine.fusion import MARKER
    wd = workcopy("synth_b")
    prepare(wd)
    meta = meta_parts(wd)
    assert meta["hair_back"]["status"] == "needs_manual"
    marked = np.array(Image.open(wd / "gen_inputs" / "hair_back.png").convert("RGBA"))
    src = np.array(Image.open(wd / "source_rgba.png"))
    is_marker = (marked[..., :3] == MARKER).all(-1)
    assert is_marker.sum() > 1000
    assert np.array_equal(marked[~is_marker], src[~is_marker])
    assert not (wd / "gen_inputs" / "head.png").exists()  # 沒被遮住的部件不需要
