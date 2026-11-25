"""spec: scope-handling（parts.json 的 unsupported 與 absent）"""
import json
import shutil

from character_to_spine import load_json
from test_cli import c2s


def _variant(synth, tmp_path, edit):
    img, _ = synth("synth_b")
    shutil.copy(img, tmp_path / img.name)
    doc = load_json(img.with_suffix(".parts.json"))
    edit(doc)
    (tmp_path / img.with_suffix(".parts.json").name).write_text(json.dumps(doc), encoding="utf-8")
    return tmp_path / img.name


def test_unsupported_stops_with_exit_3_and_reason(synth, tmp_path):
    img = _variant(synth, tmp_path, lambda d: d.update(unsupported="四足動物，沒有可對應的手臂與腿"))
    code, out, _ = c2s("run", img, "--workdir", tmp_path / "w", cwd=tmp_path)
    assert code == 3
    assert "四足動物" in json.loads(out)["reason"]
    wd = tmp_path / "w"
    assert not (wd / "rig.json").exists() and not (wd / "spine").exists()
    assert load_json(wd / "validation_report.json")["status"] == "UNSUPPORTED"


def test_unsupported_invalidates_previous_success(synth, tmp_path):
    img = _variant(synth, tmp_path, lambda d: None)
    assert c2s("run", img, "--workdir", tmp_path / "w", cwd=tmp_path)[0] in (0, 1)
    doc = load_json(img.with_suffix(".parts.json"))
    doc["unsupported"] = "多個角色"
    img.with_suffix(".parts.json").write_text(json.dumps(doc), encoding="utf-8")
    assert c2s("run", img, "--workdir", tmp_path / "w", cwd=tmp_path)[0] == 3
    wd = tmp_path / "w"
    assert not (wd / "rig.json").exists() and not (wd / "spine" / "character.json").exists()
    assert load_json(wd / "validation_report.json")["status"] == "UNSUPPORTED"


def _drop_arm_r(d):
    d["parts"] = [p for p in d["parts"] if p["name"] not in ("arm_r", "flag")]
    d["absent"] = ["arm_r"]


def test_absent_part_has_no_bone_and_is_reported(synth, tmp_path):
    img = _variant(synth, tmp_path, _drop_arm_r)
    code, out, err = c2s("run", img, "--workdir", tmp_path / "w", cwd=tmp_path)
    assert code in (0, 1), err
    wd = tmp_path / "w"
    bones = [b["name"] for b in load_json(wd / "spine" / "character.json")["bones"]]
    assert "arm_r" not in bones and "arm_l" in bones
    checks = {c["check"]: c for c in load_json(wd / "validation_report.json")["checks"]}
    assert checks["absent_parts"]["status"] == "BLOCKED" and "arm_r" in checks["absent_parts"]["detail"]
    assert "arm_r" in (wd / "repair_tasks.md").read_text(encoding="utf-8")


def test_head_or_body_cannot_be_absent(synth, tmp_path):
    img = _variant(synth, tmp_path, lambda d: d.update(absent=["body"]))
    code, out, _ = c2s("analyze", img, "--workdir", tmp_path / "w", cwd=tmp_path)
    assert code == 2 and "body" in out


def test_absent_and_present_is_contradiction(synth, tmp_path):
    img = _variant(synth, tmp_path, lambda d: d.update(absent=["arm_r"]))
    code, out, _ = c2s("analyze", img, "--workdir", tmp_path / "w", cwd=tmp_path)
    assert code == 2 and "arm_r" in out
