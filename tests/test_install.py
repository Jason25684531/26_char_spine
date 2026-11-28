"""spec: skill-installation（install.ps1 安裝到暫存位置；啟動器的執行環境候選順序）"""
import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "character-to-spine"
pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="install.ps1 只支援 Windows")


def install(script, *args):
    r = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), *map(str, args)],
                       capture_output=True, timeout=1800)
    assert r.returncode == 0, r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")
    return r


def tree(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def roots(tmp_path):
    claude = tmp_path / "claude_skills"
    claude.mkdir()  # 已存在才會安裝給 Claude Code
    return {"-SkillRoot": tmp_path / "agents_skills", "-ClaudeSkillRoot": claude, "-RuntimeRoot": tmp_path / "runtime"}


def flat(d):
    return [x for kv in d.items() for x in kv]


def test_install_twice_identical(tmp_path):
    r = roots(tmp_path)
    install(SKILL / "install.ps1", *flat(r), "-SkipRuntime")
    first = tree(tmp_path)
    install(SKILL / "install.ps1", *flat(r), "-SkipRuntime")
    assert tree(tmp_path) == first
    expected = {k: v for k, v in tree(SKILL).items() if not any(s in k.split("/") for s in (".venv", "__pycache__"))}
    assert tree(r["-SkillRoot"] / "character-to-spine") == expected
    assert tree(r["-ClaudeSkillRoot"] / "character-to-spine") == expected
    assert not r["-RuntimeRoot"].exists(), "-SkipRuntime 不建立執行環境"


def test_update_replaces_old_files(tmp_path):
    r = roots(tmp_path)
    stale = r["-SkillRoot"] / "character-to-spine" / "references" / "old_removed.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("舊版留下的檔案", encoding="utf-8")
    install(SKILL / "install.ps1", *flat(r), "-SkipRuntime")
    assert not stale.exists() and (r["-SkillRoot"] / "character-to-spine" / "SKILL.md").exists()


def test_uninstall_only_removes_own_folders(tmp_path):
    r = roots(tmp_path)
    install(SKILL / "install.ps1", *flat(r), "-SkipRuntime")
    venv = r["-RuntimeRoot"] / ".venv"
    venv.mkdir(parents=True)  # 代表安裝時建立的執行環境
    (venv / "c2s-installed.txt").write_text("x.whl", encoding="utf-8")
    other_skill = r["-SkillRoot"] / "other-skill" / "SKILL.md"
    other_skill.parent.mkdir()
    other_skill.write_text("別的 Skill", encoding="utf-8")
    project = tmp_path / "my_project" / "output" / "hero" / "layers" / "head.png"
    project.parent.mkdir(parents=True)
    project.write_bytes(b"user art")
    install(SKILL / "install.ps1", *flat(r), "-Uninstall")
    assert not (r["-SkillRoot"] / "character-to-spine").exists() and not (r["-ClaudeSkillRoot"] / "character-to-spine").exists()
    assert not r["-RuntimeRoot"].exists()
    assert project.read_bytes() == b"user art" and other_skill.read_text(encoding="utf-8") == "別的 Skill"


def load_launcher():
    spec = importlib.util.spec_from_file_location("c2s_launcher", SKILL / "scripts" / "c2s.py")
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    return launcher


def test_launcher_prefers_shared_runtime(tmp_path, monkeypatch):
    launcher = load_launcher()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("C2S_RUNTIME", str(tmp_path / "shared"))
    skill = tmp_path / "skill"
    for d in (tmp_path / "shared" / ".venv", skill / ".venv"):
        d.mkdir(parents=True)
        (d / "c2s-installed.txt").write_text("c2s-1.2.1.whl", encoding="utf-8")
    assert launcher.venv_dir(skill, "c2s-1.2.1.whl") == tmp_path / "shared" / ".venv"
    (tmp_path / "shared" / ".venv" / "c2s-installed.txt").write_text("c2s-1.2.0.whl", encoding="utf-8")
    assert launcher.venv_dir(skill, "c2s-1.2.1.whl") == skill / ".venv", "共用環境版本不符時不使用"
    read_only = tmp_path / "no_such_dir" / "skill"
    assert launcher.venv_dir(read_only, "c2s-1.2.1.whl") == tmp_path / ".c2s-runtime" / ".venv"


WHEEL_DIR = ROOT / "dist" / "character-to-spine" / "core"


@pytest.mark.skipif(not list(WHEEL_DIR.glob("*.whl")) or not os.environ.get("C2S_SLOW_INSTALL"),
                    reason="需要 dist/character-to-spine/core/*.whl 與環境變數 C2S_SLOW_INSTALL=1（會建立真的 venv 並下載套件）")
def test_real_runtime_then_launcher_uses_it(tmp_path):
    src = tmp_path / "pkg" / "character-to-spine"
    shutil.copytree(SKILL, src, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    (src / "core").mkdir()
    shutil.copyfile(WHEEL_DIR / "constraints.txt", src / "core" / "constraints.txt")
    # dist 內的 wheel 可能早於 doctor 指令：用目前原始碼重建，只沿用 dist 的版本釘選
    subprocess.run([sys.executable, "-m", "pip", "wheel", str(ROOT), "--no-deps", "-q", "-w", str(src / "core")], check=True, timeout=600)
    r = roots(tmp_path)
    out = install(src / "install.ps1", *flat(r)).stdout.decode("utf-8", "replace")
    assert "[PASS] Python" in out and "[PASS] 套件" in out
    venv = r["-RuntimeRoot"] / ".venv"
    whl = sorted((src / "core").glob("*.whl"))[-1].name
    assert (venv / "c2s-installed.txt").read_bytes() == whl.encode("ascii")
    second = install(src / "install.ps1", *flat(r)).stdout.decode("utf-8", "replace")
    assert "已是最新" in second
    # Skill 資料夾唯讀時（Codex 沙盒）啟動器直接用共用環境，不再安裝
    env = {**os.environ, "C2S_RUNTIME": str(r["-RuntimeRoot"])}
    run = subprocess.run([sys.executable, str(r["-SkillRoot"] / "character-to-spine" / "scripts" / "c2s.py"), "--version"],
                         capture_output=True, text=True, encoding="utf-8", env=env, cwd=tmp_path, timeout=120)
    assert run.returncode == 0 and "第一次使用" not in run.stderr and not (r["-SkillRoot"] / "character-to-spine" / ".venv").exists()
