"""新使用者驗收：在 repo 外的全新資料夾照 README 安裝 Skill zip，放一張未參與開發的圖片，用一句話啟動真正的 Claude Code。

python scripts/acceptance.py <圖片> [--slash] [--name <資料夾名>]

安裝與 README 相同（PowerShell Expand-Archive 到 .claude\\skills）；PATH 移除本專案、不載入使用者層設定與 MCP。
紀錄（stream-json、判定、最後回覆）存到 output/acceptance/<名稱>/，沙盒保留供檢查輸出。
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_skill import __version__  # noqa: E402
from generalization import claude_session, skill_evidence  # noqa: E402

SENTENCE = "請將這張角色圖拆補圖、建立骨架，製作 Idle／Happy 動畫並輸出結果：{file}"


def accept(image, slash=False, name=None):
    image = Path(image).resolve()
    name = name or f"{image.stem}_{'slash' if slash else 'nl'}"
    box = Path(tempfile.gettempdir()) / "c2s_acceptance" / name
    shutil.rmtree(box, ignore_errors=True)
    box.mkdir(parents=True)
    zip_path = ROOT / "dist" / f"character-to-spine-skill-v{__version__}.zip"
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    f"Expand-Archive -Path '{zip_path}' -DestinationPath '{box / '.claude' / 'skills'}'"], check=True)
    shutil.copy(image, box / image.name)
    prompt = f"/character-to-spine {image.name}" if slash else SENTENCE.format(file=image.name)
    out = ROOT / "output" / "acceptance" / name
    out.mkdir(parents=True, exist_ok=True)
    raw = out / "session.jsonl"
    proc = claude_session(prompt, box, raw)
    ev = skill_evidence(raw, box)
    wd = box / "output" / image.stem
    files = {k: (wd / k).exists() for k in ("validation_report.json", "spine/character.json", "layer_preview.png",
                                            "report/visual_check.png", "report/repair_priority.md", "repair_tasks.md",
                                            "preview/idle_python_simulation_preview.gif",
                                            "preview/happy_python_simulation_preview.gif")}
    layers = sorted(p.name for p in (wd / "layers").glob("*.png")) if (wd / "layers").exists() else []
    checks = {c["check"]: c["status"] for c in json.loads((wd / "validation_report.json").read_text(encoding="utf-8"))["checks"]} \
        if files["validation_report.json"] else {}
    result = {"prompt": prompt, "exit_code": proc.returncode, "sandbox": str(box), "installed_from": str(zip_path),
              "parts_json_written": (box / f"{image.stem}.parts.json").exists(), "outputs": files, "layers": layers,
              "validation": checks, **{k: v for k, v in ev.items() if k not in ("calls",)}}
    (out / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "final_reply.md").write_text(ev["final_reply"], encoding="utf-8")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--slash", action="store_true")
    ap.add_argument("--name")
    a = ap.parse_args()
    r = accept(a.image, a.slash, a.name)
    print(json.dumps({k: r[k] for k in ("exit_code", "skill_tool_called", "c2s_after_skill", "parts_json_written",
                                        "outputs", "validation", "forbidden_reads", "tool_escapes")}, ensure_ascii=False, indent=2))
