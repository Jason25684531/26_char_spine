"""spec: skill-cli-integration（以子行程實際執行 c2s）"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

from character_to_spine import cli

ROOT = Path(__file__).parents[1]


def c2s(*args, cwd):
    r = subprocess.run([sys.executable, "-m", "character_to_spine.cli", *map(str, args)], cwd=cwd,
                       capture_output=True, text=True, encoding="utf-8", timeout=300)
    return r.returncode, r.stdout, r.stderr


def test_step_by_step(synth, tmp_path):
    img, _ = synth("synth_a")
    steps = [("analyze", img), ("prepare",), ("rig", "--preset", "humanoid-chibi"), ("animate", "--motion", "happy"),
             ("export", "--format", "spine"), ("validate",)]
    for step in steps:
        code, out, err = c2s(*step, cwd=tmp_path)
        assert code == 0, (step, out, err)
        json.loads(out)
    wd = tmp_path / "output" / "synth_a"
    assert (wd / "spine" / "character.json").exists() and (wd / "validation_report.json").exists()


def test_run_with_workdir(synth, tmp_path):
    img, _ = synth("synth_b")
    code, out, err = c2s("run", img, "--motion", "happy", "--workdir", tmp_path / "w", cwd=tmp_path)
    assert code == 0, err
    wd = tmp_path / "w"
    assert (wd / "layers" / "head.png").exists() and (wd / "metadata.json").exists()
    assert (wd / "spine" / "character.json").exists() and (wd / "validation_report.json").exists()
    assert list((wd / "preview").glob("*.gif"))
    assert (tmp_path / "output" / ".current").read_text(encoding="utf-8") == str(wd.resolve())
    assert c2s("validate", cwd=tmp_path)[0] == 0  # 不帶參數的下一個指令接續同一個工作目錄


def test_run_without_parts_exit_2(tmp_path):
    img = tmp_path / "plain.png"
    im = Image.new("RGBA", (40, 60), (0, 0, 0, 0))
    im.paste((200, 0, 0, 255), (10, 10, 30, 50))
    im.save(img)
    code, out, _ = c2s("run", img, cwd=tmp_path)
    assert code == 2
    msg = json.loads(out)["message"]
    assert "head" in msg and "c2s run" in msg
    wd = tmp_path / "output" / "plain"
    assert not (wd / "rig.json").exists() and not (wd / "spine").exists()


def test_wrong_order_exit_2(synth, tmp_path):
    img, _ = synth("synth_a")
    assert c2s("analyze", img, cwd=tmp_path)[0] == 0
    code, out, _ = c2s("rig", cwd=tmp_path)
    assert code == 2 and "c2s prepare" in json.loads(out)["message"]


def test_unexpected_error_logged(built, monkeypatch, capsys):
    wd = built("synth_a")

    def boom(_):
        raise RuntimeError("kaboom")
    monkeypatch.setattr(cli, "validate", boom)
    assert cli.main(["validate", "-w", str(wd)]) == 1
    assert "c2s_error.log" in capsys.readouterr().err
    log = (wd / "c2s_error.log").read_text(encoding="utf-8")
    assert "Traceback" in log and "kaboom" in log
    (wd / "c2s_error.log").unlink()


def test_skill_copies_identical():
    """正本在 skills/（進版控）；.claude/ 與 .codex/ 的複本不進版控，存在時必須與正本一致。"""
    canonical = (ROOT / "skills/character-to-spine/SKILL.md").read_text(encoding="utf-8")
    for d in (".claude/skills/character-to-spine", ".codex/skills/character-to-spine"):
        copy = ROOT / d / "SKILL.md"
        if copy.exists():
            assert copy.read_text(encoding="utf-8") == canonical, f"{copy} 與正本不同，請重新複製"
    for needed in ("parts.json", "c2s run", "layer_preview.png", "repair_tasks.md", "BLOCKED"):
        assert needed in canonical


def test_validation_fail_exits_1_with_log(workcopy, tmp_path):
    wd = workcopy("synth_a")
    (wd / "spine" / "images" / "head.png").unlink()
    code, out, _ = c2s("validate", "-w", wd, cwd=tmp_path)
    assert code == 1 and json.loads(out)["status"] == "FAIL"
    assert "image_references" in (wd / "c2s_error.log").read_text(encoding="utf-8")
    c2s("export", "-w", wd, cwd=tmp_path)  # 補回圖片後成功
    assert c2s("validate", "-w", wd, cwd=tmp_path)[0] == 0
    assert not (wd / "c2s_error.log").exists()  # 不留過期的錯誤紀錄


def test_tiny_and_unreadable_inputs_are_clean_errors(tmp_path):
    tiny = tmp_path / "tiny.png"
    Image.new("RGB", (1, 1), (9, 9, 9)).save(tiny)
    code, _, err = c2s("analyze", tiny, cwd=tmp_path)
    assert code == 1 and json.loads(err)["status"] == "error"  # 不是 unexpected_error
