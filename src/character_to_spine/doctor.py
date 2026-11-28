"""c2s doctor：檢查執行這個 Skill 需要的環境，每項回報 PASS／FAIL／BLOCKED／NOT_TESTED 與中文的補救方式。"""
import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import spine_bridge


def _run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, str(e)


def _check(name, status, detail, fix=""):
    return {"name": name, "status": status, "detail": detail, "fix": fix}


def shared_runtime():
    """install.ps1 與啟動器共用的執行環境位置（C2S_RUNTIME 可改向）。"""
    return Path(os.environ.get("C2S_RUNTIME") or Path(os.environ.get("LOCALAPPDATA", Path.home())) / "character-to-spine" / "runtime")


def doctor(run=_run, which=shutil.which, spine=None):
    checks = []
    v = sys.version.split()[0]
    checks.append(_check("Python", "PASS", v) if sys.version_info >= (3, 11) else
                  _check("Python", "FAIL", f"需要 3.11 以上，目前是 {v}", "從 https://www.python.org/downloads/ 安裝 3.11 以上後重新執行 install.ps1"))

    missing = []
    for mod in ("numpy", "cv2", "PIL"):
        try:
            importlib.import_module(mod)
        except Exception as e:  # DLL 缺失等也算裝壞
            missing.append(f"{mod}（{e}）")
    checks.append(_check("套件", "FAIL", "無法載入：" + "、".join(missing), "重新執行 install.ps1 重建執行環境") if missing else
                  _check("套件", "PASS", "numpy、OpenCV、Pillow 可載入"))

    codex = which("codex")
    if codex is None:
        checks.append(_check("Codex", "BLOCKED", "Codex CLI 未安裝：拆圖、骨架、動畫可用，但被遮住部分的生成式補圖無法使用",
                             "安裝 Codex CLI（https://developers.openai.com/codex）並登入後重新執行 c2s doctor"))
        checks.append(_check("image_generation", "NOT_TESTED", "沒有 Codex，無法檢查內建圖像生成功能"))
    else:
        code, out = run([codex, "--version"])
        checks.append(_check("Codex", "PASS" if code == 0 else "FAIL", f"{codex}：{out or '沒有輸出'}",
                             "" if code == 0 else "codex --version 執行失敗，請重新安裝 Codex CLI"))
        code, out = run([codex, "features", "list"])
        row = next((ln.split() for ln in out.splitlines() if ln.split()[:1] == ["image_generation"]), None)
        if code == 0 and row and row[-1] == "true":
            checks.append(_check("image_generation", "PASS", "Codex 內建圖像生成已啟用：" + " ".join(row)))
        else:
            checks.append(_check("image_generation", "BLOCKED",
                                 "Codex 內建圖像生成未啟用：" + (" ".join(row) if row else f"codex features list 沒有這一項（exit={code}）"),
                                 "執行 codex features enable image_generation，或更新 Codex CLI"))

    s = spine_bridge.detect() if spine is None else spine
    versions = f"Launcher {s.get('launcher_version') or '未知'}、Editor {s.get('editor_version') or '未知'}"
    if s["exe"] is None:
        checks.append(_check("Spine", "BLOCKED", "找不到 Spine：仍會輸出 Spine JSON 與圖片，但無法自動匯入成 .spine 專案",
                             "安裝並啟用 Spine 完整版，或設定環境變數 SPINE_EXE 指向 Spine.com"))
    elif s["trial"]:
        checks.append(_check("Spine", "BLOCKED", f"只有試用版（{s['exe']}，{versions}，來源 {s['source']}）："
                                                  "試用版不能儲存專案，c2s spine import 無法產生 .spine",
                             "啟用完整版授權後設定 SPINE_EXE 指向 Spine.com；在那之前可用完整版的 Spine 手動匯入 spine/character.json"))
    else:
        checks.append(_check("Spine", "PASS", f"{s['exe']}（{versions}，來源 {s['source']}）"))

    roots = [Path.home() / ".agents" / "skills", Path.home() / ".claude" / "skills",
             Path.cwd() / ".agents" / "skills", Path.cwd() / ".claude" / "skills"]
    found = [str(r / "character-to-spine") for r in roots if (r / "character-to-spine" / "SKILL.md").is_file()]
    checks.append(_check("Skill 安裝位置", "PASS", "；".join(found)) if found else
                  _check("Skill 安裝位置", "FAIL", "Codex（.agents/skills）與 Claude Code（.claude/skills）的搜尋位置都沒有 character-to-spine",
                         "執行 Skill 資料夾內的 install.ps1"))

    shared = shared_runtime() / ".venv"
    here = Path(sys.prefix)
    checks.append(_check("執行環境", "PASS", f"{here}" + ("（共用執行環境）" if here == shared else f"（不是共用執行環境 {shared}）")))
    return checks
