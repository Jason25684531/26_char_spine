"""生成式補圖的紀錄與狀態：生成前登記、中斷計次、重開、原始檔指紋、重複匯入、退步保護、還原、目視判定、下一個策略。"""
import hashlib
import shutil

import numpy as np
import pytest
from PIL import Image

from character_to_spine import C2SError, NeedsInput, load_json
from character_to_spine import gen_repair
from character_to_spine.gen_repair import begin, grant_consent, overrides_dir, reopen, review, rollback
from character_to_spine.image_processor import prepare
from character_to_spine.validator import validate


def meta_parts(wd):
    return {e["name"]: e for e in load_json(wd / "metadata.json")["parts"]}


def prov(wd, part="body"):
    return load_json(overrides_dir(wd, load_json(wd / "parts.json")) / "provenance.json")["parts"][part]


def good(tmp_path, name="gen.png", tint=0):
    """synth_a 的身體完整樣貌（整張畫布、透明背景），放大 3 倍模擬生成工具的解析度。tint 讓接縫略差。"""
    canvas = Image.new("RGBA", (300, 420), (0, 0, 0, 0))
    canvas.paste((220, 80, 80, 255), (105, 175, 196, 301))
    if tint:  # 緊貼被遮區的可見像素顏色偏掉一點：仍在門檻內，但接縫量測比沒偏的差
        canvas.paste((220 - tint, 80 + tint, 80, 255), (111, 180, 125, 281))
    path = tmp_path / name
    canvas.resize((900, 1260), Image.NEAREST).save(path)
    return path


def bad(synth, tmp_path, n=0):
    """原圖照抄：沒有移除遮擋者，一定被拒。n 不同就是不同的檔案（同一個檔案重複匯入只算一次）。"""
    img = Image.open(synth("synth_a")[0]).convert("RGBA")
    img.putpixel((0, 0), (n, n, n, 0))
    path = tmp_path / f"bad{n}.png"
    img.save(path)
    return path


@pytest.fixture
def wd(workcopy):
    w = workcopy("synth_a")
    grant_consent(w)
    return w


def test_begin_registers_before_generation_and_interruption_counts(wd, tmp_path):
    r = begin(wd, "body", "prompt 1")
    assert r["remaining"] == 2 and r["strategy"] == "mask" and r["input"].endswith("body.png")
    assert prov(wd)["attempts"][-1]["verdict"] == "pending"
    r = begin(wd, "body", "prompt 2")  # 上一次登記後沒有匯入：生成途中被中斷
    assert [a["verdict"] for a in prov(wd)["attempts"]] == ["interrupted", "pending"]
    assert r["remaining"] == 1 and r["strategy"] != "mask"
    # 第二次登記的策略是局部圖：生成工具只看到、也只回傳部件附近那一塊
    box = load_json(wd / "gen_inputs" / "body_local.json")["box"]
    local = tmp_path / "local.png"
    crop = Image.open(good(tmp_path)).resize((300, 420), Image.NEAREST).crop(box)
    crop.resize((crop.width * 3, crop.height * 3), Image.NEAREST).save(local)
    prepare(wd, generated=("body", local, None))  # 匯入填入登記的那一筆，不另外加一筆；策略沿用登記時的
    att = prov(wd)["attempts"]
    assert [a["verdict"] for a in att] == ["interrupted", "pass"] and att[1]["prompt"] == "prompt 2"
    assert att[1]["strategy"] == "mask-local" and meta_parts(wd)["body"]["status"] == "ai_repaired"


def test_begin_refused_when_exhausted_until_reopened_with_reason(wd, synth, tmp_path):
    for n in range(2):
        with pytest.raises(NeedsInput):
            prepare(wd, generated=("body", bad(synth, tmp_path, n), "p"))
    begin(wd, "body", "p3")
    with pytest.raises(C2SError, match="上限"):  # 兩次拒絕＋一次登記中＝3 次，再登記會讓它變成中斷，已無剩餘
        begin(wd, "body", "p4")
    assert prov(wd)["attempts"][-1]["verdict"] == "interrupted"
    with pytest.raises(C2SError, match="理由"):
        reopen(wd, "body", "  ")
    reopen(wd, "body", "使用者要求以新的局部策略重試")
    r = begin(wd, "body", "p5")
    assert r["remaining"] == 2
    rec = prov(wd)
    assert len(rec["attempts"]) == 4 and rec["reopened"][0]["reason"].startswith("使用者要求") and rec["reopened"][0]["after_attempt"] == 3


def test_rejection_names_a_different_next_strategy(wd, synth, tmp_path):
    seen = []
    for n in range(2):
        with pytest.raises(NeedsInput) as e:
            prepare(wd, generated=("body", bad(synth, tmp_path, n), "p", ))
        seen.append(prov(wd)["attempts"][-1]["next_strategy"])
        assert seen[-1] in str(e.value)
    assert seen[0] != seen[1] and "mask" not in seen[:1]  # 第一次用的是 mask，下一次不再建議它


def test_sha256_and_raw_source(wd, tmp_path, monkeypatch):
    g = good(tmp_path)
    codex_home = tmp_path / "codex"
    (codex_home / "generated_images" / "session").mkdir(parents=True)
    shutil.copyfile(g, codex_home / "generated_images" / "session" / "exec-1.png")
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    prepare(wd, generated=("body", g, "p"))
    a = prov(wd)["attempts"][0]
    assert a["sha256"] == hashlib.sha256(g.read_bytes()).hexdigest()
    assert a["raw_source"].endswith("exec-1.png")


def test_raw_source_unverified_when_file_was_edited(wd, tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "empty"))
    prepare(wd, generated=("body", good(tmp_path), "p"))
    assert prov(wd)["attempts"][0]["raw_source"] is None
    assert "來源未驗證" in (wd / "repair_tasks.md").read_text(encoding="utf-8")


def test_importing_the_same_file_twice_counts_once(wd, tmp_path):
    g = good(tmp_path)
    prepare(wd, generated=("body", g, "p"))
    layer = (wd / "layers" / "body.png").read_bytes()
    prepare(wd, generated=("body", g, "p"))
    assert len(prov(wd)["attempts"]) == 1 and (wd / "layers" / "body.png").read_bytes() == layer


def test_worse_pass_does_not_replace_current_result_and_rollback(wd, tmp_path):
    prepare(wd, generated=("body", good(tmp_path, "a.png", tint=12), "p"))
    first = (wd / "layers" / "body.png").read_bytes()
    prepare(wd, generated=("body", good(tmp_path, "b.png"), "p"))  # 比較好：取代
    better = (wd / "layers" / "body.png").read_bytes()
    assert better != first and prov(wd)["accepted"] == 1
    prepare(wd, generated=("body", good(tmp_path, "c.png", tint=20), "p"))  # 通過但比現有的差：不取代
    rec = prov(wd)
    assert rec["attempts"][2]["verdict"] == "pass" and rec["attempts"][2]["adopted"] is False and rec["accepted"] == 1
    assert (wd / "layers" / "body.png").read_bytes() == better
    rollback(wd, "body")
    prepare(wd)
    assert (wd / "layers" / "body.png").read_bytes() == first and prov(wd)["accepted"] == 0
    with pytest.raises(C2SError, match="沒有更早"):
        rollback(wd, "body")


def checks(wd):
    return {c["check"]: c for c in validate(wd)["checks"]}


def test_visual_review_gates_status(wd, tmp_path):
    prepare(wd, generated=("body", good(tmp_path), "p"))
    assert (wd / "visual_review" / "body.png").exists()
    assert Image.open(wd / "visual_review" / "body.png").width >= 3 * 90  # 原圖、圖層、移開遮擋物後 三個畫面
    assert checks(wd)["visual_review"]["status"] == "NOT_TESTED"  # 數值通過但還沒有人看過
    review(wd, "body", "unsure", "邊緣看不清楚", "tester")
    prepare(wd)
    assert checks(wd)["visual_review"]["status"] == "BLOCKED"
    review(wd, "body", "pass", "形狀與顏色自然，沒有殘留", "tester")
    prepare(wd)
    assert checks(wd)["visual_review"]["status"] == "PASS"
    assert prov(wd)["attempts"][0]["review"]["by"] == "tester"
    with pytest.raises(C2SError, match="說明"):
        review(wd, "body", "pass", "", "tester")


def test_visual_fail_withdraws_the_repair_and_counts(wd, tmp_path):
    before = (wd / "layers" / "body.png").read_bytes()
    prepare(wd, generated=("body", good(tmp_path), "p"))
    assert meta_parts(wd)["body"]["status"] == "ai_repaired"
    r = review(wd, "body", "fail", "圖層上看得到殘留的手臂", "tester")
    prepare(wd)
    assert r["remaining"] == 2
    assert meta_parts(wd)["body"]["status"] != "ai_repaired" and (wd / "layers" / "body.png").read_bytes() == before
    rec = prov(wd)
    assert rec["accepted"] is None and rec["attempts"][0]["review"]["verdict"] == "fail"
    assert begin(wd, "body", "p2")["remaining"] == 1  # 目視不通過算一次失敗


def test_no_generated_parts_means_review_passes(built):
    assert checks(built("synth_a"))["visual_review"]["status"] == "PASS"


def test_local_input_is_cropped_to_the_part(wd):
    """mask-local 策略：交給生成工具的圖只有部件附近，解析度相對更高；仍是原圖像素加洋紅標記。"""
    full = Image.open(wd / "gen_inputs" / "body.png")
    local = Image.open(wd / "gen_inputs" / "body_local.png")
    assert local.width < full.width and local.height < full.height
    box = load_json(wd / "gen_inputs" / "body_local.json")["box"]
    assert np.array_equal(np.array(full.crop(box)), np.array(local))
