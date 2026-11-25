import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import generalization as g  # noqa: E402
from motion_metrics import limb_travel  # noqa: E402

from character_to_spine import load_json, save_json  # noqa: E402

C = {"unassigned_max": 0.01, "free_arm_min": 0.02, "bounce_only_max": 0.005}
REVIEW_OK = {"reviewer": "agent", **{k: ["OK", "看過"] for k in ("layers", "joints", "motion", "occlusion")}}


def ran(**kw):
    r = {"id": "X", "origin": "public", "expected_scope": "supported", "status": "ran", "exit_code": 0, "has_parts": True,
         "provenance": {"status": "PASS", "detail": []}, "validator": {"bones": "PASS", "spine_import": "BLOCKED"},
         "recompose": {"unassigned_ratio": 0.0}, "loop_ok": True, "bounce_only": False, "free_arms": {"arm_l": 0.05},
         "quality": {"unresolved": []}, "over_reduced": {}, "manual": [], "absent": [], "visual": REVIEW_OK}
    r.update(kw)
    return r


@pytest.mark.parametrize("r, level", [
    (ran(), "PASS"),
    (ran(manual=["body"]), "PARTIAL"),
    (ran(absent=["arm_r"]), "PARTIAL"),
    (ran(over_reduced={"arm_l": {"factor": 0.125, "limit": "素材限制", "caused_by": ["exposure"]}}), "PARTIAL"),
    (ran(over_reduced={"arm_l": {"factor": 0.125, "limit": "演算法限制", "caused_by": ["gap"]}}), "FAIL"),
    (ran(unsupported="四足", expected_scope="unsupported"), "UNSUPPORTED"),
    (ran(unsupported="四足", expected_scope="partial"), "FAIL"),
    (ran(has_parts=False, status="stopped"), "FAIL"),
    (ran(provenance={"status": "FAIL", "detail": ["arm_l 與既有部件 arm_l 的多邊形雷同"]}), "FAIL"),
    (ran(status="stopped", exit_code=1, message="boom"), "FAIL"),
    (ran(validator={"setup_pose": "FAIL"}), "FAIL"),
    (ran(bounce_only=True), "FAIL"),
    (ran(free_arms={"arm_l": 0.01}), "FAIL"),
    (ran(recompose={"unassigned_ratio": 0.05}), "FAIL"),
    (ran(visual=None), "NOT_TESTED"),
    (ran(exit_code=1), "FAIL"),
    (ran(absent=["arm_r"], expected_absent=[]), "FAIL"),
    (ran(absent=["leg_l"], expected_absent=["leg_l", "leg_r"]), "PARTIAL"),
    (ran(over_reduced={"arm_l": {"factor": 0.125, "limit": "未歸因", "caused_by": []}}), "FAIL"),
    (ran(visual={**REVIEW_OK, "joints": ["BAD", "手臂繞手肘轉"]}), "FAIL"),
    (ran(visual={**REVIEW_OK, "occlusion": ["MINOR", "裙下有草稿痕跡"]}), "PARTIAL"),
    ({"id": "X", "origin": "public", "expected_scope": "supported", "problems": ["圖片雜湊與 manifest 不符"]}, "NOT_TESTED"),
    ({"id": "X", "origin": "public", "expected_scope": "supported", "problems": ["找不到圖片 E/gen_e.png"]}, "BLOCKED"),
])
def test_grade_table(r, level):
    assert g.grade(r, C)[0] == level


def test_spine_license_does_not_decide_grade():
    assert g.grade(ran(validator={"spine_import": "BLOCKED", "spine_roundtrip": "NOT_TESTED", "spine_editable": "NOT_TESTED"}), C)[0] == "PASS"


def test_provenance_flags_copied_and_shifted_polygons(synth, tmp_path):
    img, _ = synth("synth_b")
    real = load_json(Path(__file__).resolve().parents[1] / "examples" / "synthetic" / "synth_b.parts.json")
    poly = next(p for p in real["parts"] if p.get("polygon"))
    shifted = [[x + 7, y - 4] for x, y in poly["polygon"]]
    save_json(tmp_path / "copy.parts.json", {"parts": [{"name": "body", "polygon": shifted, "z": 0}]})
    copied = g.provenance(img, tmp_path / "copy.parts.json")
    assert copied["status"] == "FAIL" and "雷同" in copied["detail"][0]
    save_json(tmp_path / "own.parts.json", {"parts": [{"name": "body", "polygon": [[160, 200], [250, 203], [255, 280], [155, 285], [150, 240]], "z": 0}]})
    assert g.provenance(img, tmp_path / "own.parts.json")["status"] == "PASS"


def _events(*items):
    return "\n".join(json.dumps(e, ensure_ascii=False) for e in items)


def test_skill_evidence_needs_a_skill_call_not_a_read(tmp_path):
    read_only = tmp_path / "read.jsonl"
    read_only.write_text(_events(
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read", "input": {"file_path": ".claude/skills/character-to-spine/SKILL.md"}}]}},
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": "c2s run x.png"}}]}},
        {"type": "result", "result": "done"}), encoding="utf-8")
    ev = g.skill_evidence(read_only)
    assert not ev["skill_tool_called"] and not ev["c2s_after_skill"]

    real = tmp_path / "skill.jsonl"
    real.write_text(_events(
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "character-to-spine"}}]}},
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read", "input": {"file_path": "examples/real/人.parts.json"}}]}},
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": ".venv/Scripts/c2s.exe run x.png"}}]}}),
        encoding="utf-8")
    ev = g.skill_evidence(real)
    assert ev["skill_tool_called"] and ev["c2s_after_skill"]
    assert ev["forbidden_reads"] and ev["forbidden_reads"][0]["hit"] == "examples/real"


def test_limb_travel_sees_free_arms(built):
    wd = built("synth_a")
    travel = limb_travel(wd, load_json(wd / "spine" / "character.json"))
    assert travel["arm_l"]["happy"] > 0.02 and travel["arm_r"]["happy"] > 0.02
    assert all(np.isfinite(v["idle"]) for v in travel.values())


def test_escape_detection_handles_windows_paths(tmp_path):
    box = tmp_path / "A" / "sandbox_nl"
    box.mkdir(parents=True)
    raw = tmp_path / "s.jsonl"
    raw.write_text(_events(
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read", "input": {"file_path": str(box / "gen_a.png")}}]}},
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read", "input": {"file_path": "D:\\01_Project\\26_char_spine\\examples\\real\\转场2.parts.json"}}]}},
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": "cat ../../other.parts.json"}}]}}),
        encoding="utf-8")
    ev = g.skill_evidence(raw, box)
    assert {h["hit"] for h in ev["forbidden_reads"]} >= {"examples/real", "转场2.parts"}
    assert {h["hit"] for h in ev["tool_escapes"]} == {"沙盒外的專案路徑", "上層目錄 ../"}
    assert not any("gen_a.png" in h["input"] for h in ev["forbidden_reads"] + ev["tool_escapes"])
