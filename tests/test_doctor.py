"""spec: skill-installation（c2s doctor 的環境檢查，以注入的指令結果測試）"""
from character_to_spine import cli
from character_to_spine.doctor import doctor

NO_SPINE = {"exe": None, "launcher_version": None, "editor_version": None, "trial": False, "source": None}
TRIAL = {"exe": r"C:\S\SpineTrial.com", "launcher_version": "4.3.08", "editor_version": "4.3.26", "trial": True, "source": "registry"}
FULL = {**TRIAL, "exe": r"C:\S\Spine.com", "trial": False}


def by_name(checks):
    return {c["name"]: c for c in checks}


def fake_run(features):
    def run(cmd):
        if cmd[1:] == ["--version"]:
            return 0, "codex-cli 0.172.0"
        if cmd[1:] == ["features", "list"]:
            return 0, features
        raise AssertionError(cmd)
    return run


def test_every_check_has_chinese_detail_and_valid_status():
    checks = doctor(run=fake_run("image_generation  stable  true"), which=lambda n: "C:/bin/codex.cmd", spine=FULL)
    assert {c["name"] for c in checks} >= {"Python", "套件", "Codex", "image_generation", "Spine", "Skill 安裝位置", "執行環境"}
    assert all(c["status"] in ("PASS", "FAIL", "BLOCKED", "NOT_TESTED") and c["detail"] for c in checks)
    c = by_name(checks)
    assert c["Python"]["status"] == c["套件"]["status"] == "PASS"
    assert c["Codex"]["status"] == "PASS" and "0.172.0" in c["Codex"]["detail"]
    assert c["image_generation"]["status"] == "PASS"
    assert c["Spine"]["status"] == "PASS" and "4.3.26" in c["Spine"]["detail"]


def test_missing_codex():
    c = by_name(doctor(run=fake_run(""), which=lambda n: None, spine=FULL))
    assert c["Codex"]["status"] == "BLOCKED" and "未安裝" in c["Codex"]["detail"] and c["Codex"]["fix"]
    assert c["image_generation"]["status"] == "NOT_TESTED"


def test_image_generation_disabled():
    c = by_name(doctor(run=fake_run("image_generation  stable  false"), which=lambda n: "codex", spine=FULL))
    assert c["image_generation"]["status"] == "BLOCKED" and "codex features enable image_generation" in c["image_generation"]["fix"]


def test_missing_and_trial_spine():
    run, which = fake_run("image_generation stable true"), lambda n: "codex"
    c = by_name(doctor(run=run, which=which, spine=NO_SPINE))["Spine"]
    assert c["status"] == "BLOCKED" and "找不到" in c["detail"] and "SPINE_EXE" in c["fix"]
    c = by_name(doctor(run=run, which=which, spine=TRIAL))["Spine"]
    assert c["status"] == "BLOCKED" and "試用版" in c["detail"] and "4.3.08" in c["detail"]


def test_skill_locations(tmp_path, monkeypatch):
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.chdir(tmp_path)
    args = dict(run=fake_run(""), which=lambda n: None, spine=NO_SPINE)
    assert by_name(doctor(**args))["Skill 安裝位置"]["status"] == "FAIL"
    skill = tmp_path / "home" / ".agents" / "skills" / "character-to-spine"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("x", encoding="utf-8")
    c = by_name(doctor(**args))["Skill 安裝位置"]
    assert c["status"] == "PASS" and str(skill) in c["detail"]


def test_cli_doctor_prints_lines(capsys):
    code = cli.main(["doctor"])
    out = capsys.readouterr().out
    assert code in (0, 1) and "[PASS] Python" in out and "Spine" in out
