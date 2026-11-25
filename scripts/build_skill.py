"""組出可安裝的 Skill 套件：skills/character-to-spine/ + Python Core 的 wheel + 版本釘選。

python scripts/build_skill.py    → dist/character-to-spine/ 與 dist/character-to-spine-skill-v<版本>.zip
解壓後的 character-to-spine/ 資料夾放進 ~/.claude/skills/ 或 <專案>/.claude/skills/ 即可使用。
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from character_to_spine import __version__  # noqa: E402

RUNTIME = ("numpy", "opencv-python", "pillow")  # pyproject 的執行期依賴；版本取自 requirements-lock.txt


def build(dist=ROOT / "dist"):
    out = dist / "character-to-spine"
    shutil.rmtree(out, ignore_errors=True)
    shutil.copytree(ROOT / "skills" / "character-to-spine", out, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    subprocess.run([sys.executable, "-m", "pip", "wheel", str(ROOT), "--no-deps", "-q", "-w", str(out / "core")], check=True)
    pins = [ln for ln in (ROOT / "requirements-lock.txt").read_text(encoding="utf-8").splitlines()
            if ln.split("==")[0].lower() in RUNTIME]
    assert len(pins) == len(RUNTIME), pins
    (out / "core" / "constraints.txt").write_text("\n".join(pins) + "\n", encoding="utf-8")
    zip_path = shutil.make_archive(str(dist / f"character-to-spine-skill-v{__version__}"), "zip", dist, out.name)
    return out, Path(zip_path)


if __name__ == "__main__":
    for p in build():
        print(p)
