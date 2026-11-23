"""spec: spine-exporter、delivery-validation"""
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageSequence

from character_to_spine import load_json, save_json, spine_exporter
from character_to_spine.animation_builder import build_animations
from character_to_spine.preview import write_previews
from character_to_spine.spine_exporter import build_skeleton, export
from character_to_spine.validator import validate

OFFICIAL = json.loads((Path(__file__).parent / "fixtures" / "spine43_keys.json").read_text(encoding="utf-8"))


def skel(wd):
    return load_json(wd / "spine" / "character.json")


def test_structure_and_image_sizes(built):
    s = skel(built("synth_b"))
    names = [b["name"] for b in s["bones"]]
    assert names[0] == "root" and "parent" not in s["bones"][0]
    assert all(b["parent"] in names[:i] for i, b in enumerate(s["bones"][1:], 1))
    skin = s["skins"][0]["attachments"]
    for slot in s["slots"]:
        att = skin[slot["name"]][slot["attachment"]]
        img = Image.open(built("synth_b") / "spine" / "images" / f"{slot['attachment']}.png")
        assert img.size == (att["width"], att["height"])


def test_spine_version_option(built):
    assert build_skeleton(built("synth_a"), "4.2.43")["skeleton"]["spine"] == "4.2.43"
    assert skel(built("synth_a"))["skeleton"]["spine"].startswith("4.3")


def test_keys_exist_in_official_export(built):
    s = skel(built("synth_b"))
    assert set(s) <= set(OFFICIAL["top"])
    assert set(s["skeleton"]) <= set(OFFICIAL["skeleton"])
    assert {k for b in s["bones"] for k in b} <= set(OFFICIAL["bone"])
    assert {k for x in s["slots"] for k in x} <= set(OFFICIAL["slot"])
    assert {k for x in s["skins"] for k in x} <= set(OFFICIAL["skin"])
    assert {k for atts in s["skins"][0]["attachments"].values() for a in atts.values() for k in a} <= set(OFFICIAL["region"])
    assert {k for a in s["animations"].values() for k in a} <= set(OFFICIAL["animation"])
    tls = {t: ks for a in s["animations"].values() for tl in a["bones"].values() for t, ks in tl.items()}
    assert set(tls) <= set(OFFICIAL["bone_timeline"])
    assert {k for ks in tls.values() for key in ks for k in key} <= set(OFFICIAL["bone_key"])


def test_no_spine_blocked(workcopy, monkeypatch):
    wd = workcopy("synth_a")
    monkeypatch.delenv("SPINE_EXE", raising=False)
    monkeypatch.setattr(spine_exporter, "find_spine", lambda: (None, False))
    r = export(wd)
    assert r["spine_import"]["status"] == "BLOCKED" and "SPINE_EXE" in r["spine_import"]["detail"]
    assert (wd / "spine" / "character.json").exists() and not (wd / "spine" / "character.spine").exists()


def test_trial_blocked_even_when_given_explicitly(workcopy, tmp_path):
    wd = workcopy("synth_a")
    fake_trial = tmp_path / "SpineTrial.com"
    fake_trial.write_bytes(b"")  # 不會被執行：試用版直接判定 BLOCKED
    r = export(wd, spine_exe=str(fake_trial))
    assert r["spine_import"]["status"] == "BLOCKED" and "試用版" in r["spine_import"]["detail"]
    assert not list((wd / "spine").glob("*.spine"))


def test_cli_failure_is_fail_with_log(workcopy, tmp_path):
    """包裝程式的邏輯測試：用一個會失敗的假執行檔。這不是 Spine 匯入驗證。"""
    wd = workcopy("synth_a")
    fake = tmp_path / "FakeSpine.cmd"
    fake.write_text("@echo boom\r\n@exit /b 3\r\n")
    r = export(wd, spine_exe=str(fake))["spine_import"]
    assert r["status"] == "FAIL" and "exit=3" in r["detail"]
    assert "boom" in Path(r["log"]).read_text(encoding="utf-8")


def test_missing_exe_is_fail_not_crash(workcopy, tmp_path):
    r = export(workcopy("synth_a"), spine_exe=str(tmp_path / "NoSuchSpine.com"))["spine_import"]
    assert r["status"] == "FAIL" and "無法執行" in r["detail"]


def test_preview_labelled_and_moving(built):
    from character_to_spine import preview
    assert "Python Simulation Preview" in preview.LABEL and "not a Spine render" in preview.LABEL
    wd = built("synth_a")
    paths = write_previews(wd)
    assert {Path(p).name for p in paths} == {"idle_python_simulation_preview.gif", "happy_python_simulation_preview.gif"}
    frames = [np.array(f.convert("RGB")) for f in ImageSequence.Iterator(Image.open(wd / "preview" / "happy_python_simulation_preview.gif"))]
    assert len(frames) > 1 and not np.array_equal(frames[0], frames[len(frames) // 3])
    assert (frames[0][:14] < 128).any()  # 上緣的標示文字


# ---- delivery-validation ----

def checks(r):
    return {c["check"]: c for c in r["checks"]}


def test_validate_ok(built):
    c = checks(validate(built("synth_a")))
    assert all(c[k]["status"] == "PASS" for k in ("bones", "slots", "image_references", "animations", "setup_pose")), c


def test_validate_catches_missing_image(workcopy):
    wd = workcopy("synth_a")
    (wd / "spine" / "images" / "head.png").unlink()
    c = checks(validate(wd))["image_references"]
    assert c["status"] == "FAIL" and "head.png" in c["detail"]


def test_validate_catches_bad_bone(workcopy):
    wd = workcopy("synth_a")
    s = skel(wd)
    s["slots"][0]["bone"] = "ghost"
    save_json(wd / "spine" / "character.json", s)
    c = checks(validate(wd))["slots"]
    assert c["status"] == "FAIL" and "ghost" in c["detail"]


def test_validate_catches_short_happy(workcopy):
    wd = workcopy("synth_a")
    s = skel(wd)
    for tls in s["animations"]["happy"]["bones"].values():
        for tl, keys in tls.items():
            tls[tl] = [k for k in keys if k.get("time", 0) <= 1.0]
            for k in tls[tl][-1:]:
                k.pop("curve", None)
    save_json(wd / "spine" / "character.json", s)
    c = checks(validate(wd))["animations"]
    assert c["status"] == "FAIL" and "happy" in c["detail"]


def test_validate_catches_offset_attachment(workcopy):
    wd = workcopy("synth_a")
    s = skel(wd)
    s["skins"][0]["attachments"]["body"]["body"]["x"] += 60
    save_json(wd / "spine" / "character.json", s)
    assert checks(validate(wd))["setup_pose"]["status"] == "FAIL"


def test_validate_catches_flipped_rotations(workcopy):
    """審查發現：舊版整張畫布平均，附件旋轉全部反向仍會 PASS。"""
    wd = workcopy("synth_b")
    s = skel(wd)
    for atts in s["skins"][0]["attachments"].values():
        for a in atts.values():
            a["rotation"] = -a.get("rotation", 0)
    save_json(wd / "spine" / "character.json", s)
    assert checks(validate(wd))["setup_pose"]["status"] == "FAIL"


def test_idle_only_is_valid(workcopy):
    wd = workcopy("synth_a")
    build_animations(wd, "idle")
    export(wd)
    c = checks(validate(wd))["animations"]
    assert c["status"] == "PASS" and "happy" not in load_json(wd / "animations.json")


def test_trial_environment_not_pass(workcopy, monkeypatch):
    wd = workcopy("synth_a")
    monkeypatch.setattr(spine_exporter, "find_spine", lambda: (r"C:\Program Files\Spine Trial\SpineTrial.com", True))
    export(wd)
    r = validate(wd)
    c = checks(r)
    assert c["spine_import"]["status"] == "BLOCKED"
    assert c["spine_roundtrip"]["status"] == "NOT_TESTED" and c["spine_editable"]["status"] == "NOT_TESTED"
    assert r["status"] == "BLOCKED"


def test_manual_repairs_blocked(built):
    c = checks(validate(built("synth_b")))["manual_repairs"]
    assert c["status"] == "BLOCKED" and "hair_back" in c["detail"]


def test_no_character_specific_code():
    src = Path(__file__).parents[1] / "src" / "character_to_spine"
    text = "".join(p.read_text(encoding="utf-8") for p in src.rglob("*.py"))
    for marker in ("人.png", "转场", "预中奖", "synth_", "guitar", "hair_back"):
        assert marker not in text, marker


def test_validate_catches_wrong_image_content(workcopy):
    """審查發現：舊版拿匯出的圖跟自己比，換成純色或翻轉都會 PASS。"""
    for tamper in ("magenta", "flip"):
        wd = workcopy("synth_b")
        p = wd / "spine" / "images" / ("head.png" if tamper == "magenta" else "flag.png")  # 旗子上下不對稱
        im = Image.open(p)
        im = Image.new("RGBA", im.size, (255, 0, 255, 255)) if tamper == "magenta" else im.transpose(Image.FLIP_TOP_BOTTOM)
        im.save(p)
        assert checks(validate(wd))["setup_pose"]["status"] == "FAIL", tamper
        import shutil
        shutil.rmtree(wd)


def test_curve_values_are_absolute_bezier():
    """Spine 4.x：每個 channel 四個數字 [t1, v1, t2, v2]，時間與數值都是絕對值（不是 3.x 的 0~1 比例）。"""
    from character_to_spine.animation_builder import _keys
    k = _keys([(0.0, 10, 20), (0.6, 40, 50)], ["x", "y"])[0]
    assert k["curve"] == pytest.approx([0.2, 10, 0.4, 40, 0.2, 20, 0.4, 50])
