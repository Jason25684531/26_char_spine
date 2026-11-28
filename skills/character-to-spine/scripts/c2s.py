"""Character-to-Spine 的執行入口，只用 Python 標準函式庫。

python scripts/c2s.py <c2s 參數...>      例：python scripts/c2s.py run hero.png

先找 install.ps1 建立的共用執行環境（%LOCALAPPDATA%/character-to-spine/runtime）；沒有時第一次執行在本 Skill 資料夾建立 .venv（資料夾唯讀時改在目前專案的 .c2s-runtime/，例如 Codex 沙盒），安裝 core/ 內附的 c2s（需要網路下載 numpy、Pillow、OpenCV），
之後直接把參數轉給 c2s。換新版的 core/*.whl 時會自動重裝。不使用、也不需要任何其他專案的虛擬環境。
"""
import os
import subprocess
import sys
import venv
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]


def shared_runtime():
    """install.ps1 建立的共用執行環境（在沙盒外建好，沙盒內只讀）；C2S_RUNTIME 可改向。"""
    return Path(os.environ.get("C2S_RUNTIME") or Path(os.environ.get("LOCALAPPDATA", Path.home())) / "character-to-spine" / "runtime")


def venv_dir(skill, wheel):
    """已裝好這版的環境優先（共用 → Skill 內 → 專案 .c2s-runtime/）；都沒有時 Skill 資料夾寫得進去就裝在裡面，否則裝在專案內。"""
    candidates = [shared_runtime() / ".venv", skill / ".venv", Path.cwd() / ".c2s-runtime" / ".venv"]
    for d in candidates:
        stamp = d / "c2s-installed.txt"
        if stamp.exists() and stamp.read_text(encoding="utf-8").strip() == wheel:
            return d
    probe = skill / ".c2s-write-test"
    try:
        probe.write_text("", encoding="utf-8")
        probe.unlink()
        return candidates[1]
    except OSError:
        return candidates[2]


def python_in(venv_path):
    return venv_path / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def ensure_runtime():
    if sys.version_info < (3, 11):
        sys.exit(f"Character-to-Spine 需要 Python 3.11 以上，目前是 {sys.version.split()[0]}")
    wheels = sorted((SKILL / "core").glob("*.whl"))
    if not wheels:
        sys.exit(f"{SKILL / 'core'} 裡沒有 c2s 的 .whl，Skill 套件不完整，請重新解壓安裝")
    target = venv_dir(SKILL, wheels[-1].name)
    stamp = target / "c2s-installed.txt"
    if stamp.exists() and stamp.read_text(encoding="utf-8").strip() == wheels[-1].name:
        return python_in(target)
    print(f"第一次使用：安裝執行環境到 {target}（約 1～3 分鐘）", file=sys.stderr, flush=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    venv.create(target, with_pip=True, clear=True)
    pip = [str(python_in(target)), "-m", "pip", "install", "--disable-pip-version-check", "-q"]
    if subprocess.run([*pip, "-c", str(SKILL / "core" / "constraints.txt"), str(wheels[-1])]).returncode:
        print("釘選版本安裝失敗，改裝與這個 Python 相容的最新版本", file=sys.stderr, flush=True)
        subprocess.run([*pip, str(wheels[-1])], check=True)
    stamp.write_text(wheels[-1].name, encoding="utf-8")
    return python_in(target)


if __name__ == "__main__":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # Windows 管線預設 cp950，Agent 讀到的中文會變亂碼
    py = ensure_runtime()
    sys.exit(subprocess.run([str(py), "-m", "character_to_spine.cli", *sys.argv[1:]]).returncode)
