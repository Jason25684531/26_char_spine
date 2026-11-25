"""Character-to-Spine 的執行入口，只用 Python 標準函式庫。

python scripts/c2s.py <c2s 參數...>      例：python scripts/c2s.py run hero.png

第一次執行時在本 Skill 資料夾建立 .venv，安裝 core/ 內附的 c2s（需要網路下載 numpy、Pillow、OpenCV），
之後直接把參數轉給 c2s。換新版的 core/*.whl 時會自動重裝。不使用、也不需要任何其他專案的虛擬環境。
"""
import subprocess
import sys
import venv
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
VENV = SKILL / ".venv"
PY = VENV / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def ensure_runtime():
    if sys.version_info < (3, 11):
        sys.exit(f"Character-to-Spine 需要 Python 3.11 以上，目前是 {sys.version.split()[0]}")
    wheels = sorted((SKILL / "core").glob("*.whl"))
    if not wheels:
        sys.exit(f"{SKILL / 'core'} 裡沒有 c2s 的 .whl，Skill 套件不完整，請重新解壓安裝")
    stamp = VENV / "c2s-installed.txt"
    if stamp.exists() and stamp.read_text(encoding="utf-8").strip() == wheels[-1].name:
        return
    print(f"第一次使用：安裝執行環境到 {VENV}（約 1～3 分鐘）", file=sys.stderr, flush=True)
    venv.create(VENV, with_pip=True, clear=True)
    pip = [str(PY), "-m", "pip", "install", "--disable-pip-version-check", "-q"]
    if subprocess.run([*pip, "-c", str(SKILL / "core" / "constraints.txt"), str(wheels[-1])]).returncode:
        print("釘選版本安裝失敗，改裝與這個 Python 相容的最新版本", file=sys.stderr, flush=True)
        subprocess.run([*pip, str(wheels[-1])], check=True)
    stamp.write_text(wheels[-1].name, encoding="utf-8")


if __name__ == "__main__":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # Windows 管線預設 cp950，Agent 讀到的中文會變亂碼
    ensure_runtime()
    sys.exit(subprocess.run([str(PY), "-m", "character_to_spine.cli", *sys.argv[1:]]).returncode)
