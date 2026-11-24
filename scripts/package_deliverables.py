"""從實際輸出組出交付目錄 Character-to-Spine-Deliverables/。

python scripts/package_deliverables.py --chars output/ren output/zc2 [--out Character-to-Spine-Deliverables] [--skip-tests]

每個檔案都複製自工作目錄或專案原始碼；沒有 .spine 時不放任何替代檔，README 標明 BLOCKED。
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from make_slides import CHECK_LABELS, build  # noqa: E402
from build_skill import build as build_skill  # noqa: E402
from character_to_spine.report import report as visual_report  # noqa: E402


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def copytree(src, dst, ignore=("__pycache__", "*.pyc", "*.egg-info")):
    if Path(src).exists():
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*ignore), dirs_exist_ok=True)


def package(chars, out, originals=ROOT / "examples" / "real", run_tests=True):
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    d = {k: out / k for k in ("00_Skill_v1.0", "01_Original_Images", "02_Layered_Assets", "03_Spine_Project", "04_Animation_Preview",
                              "05_Presentation", "06_Development", "07_Test_Reports")}
    for p in d.values():
        p.mkdir(parents=True)

    build_skill(d["00_Skill_v1.0"])  # 可安裝的 Skill：資料夾與 zip（新使用者照 README 解壓到 .claude/skills/）
    shutil.copy2(ROOT / "README.md", d["00_Skill_v1.0"] / "INSTALL_README.md")

    for img in sorted(Path(originals).glob("*.png")):
        shutil.copy2(img, d["01_Original_Images"])

    rows = []
    for wd in map(Path, chars):
        meta = load(wd / "metadata.json")
        name = Path(meta["image"]).stem if meta.get("image") else wd.name
        la = d["02_Layered_Assets"] / name
        copytree(wd / "layers", la / "PNG")
        for f in ("metadata.json", "parts.json", "missing_parts.json", "repair_tasks.md", "layer_preview.png", "grid_overlay.png"):
            if (wd / f).exists():
                shutil.copy2(wd / f, la)
        visual_report(wd, la / "report")  # 修補優先順序、三格對照、視覺驗收總覽
        sp = d["03_Spine_Project"] / name
        copytree(wd / "spine", sp, ignore=("roundtrip", "*.log"))
        (sp / "IMPORT.md").write_text(_import_md(name, sp, load(wd / "export_report.json")), encoding="utf-8")
        for gif in (wd / "preview").glob("*.gif"):
            shutil.copy2(gif, d["04_Animation_Preview"] / f"{name}_{gif.name}")
        tr = d["07_Test_Reports"] / name
        tr.mkdir()
        for f in ("validation_report.json", "export_report.json", "analysis.json", "tuning.json"):
            if (wd / f).exists():
                shutil.copy2(wd / f, tr)
        copytree(wd / "quality", tr / "quality")  # 動畫品質報告、每輪的異常影格
        checks = {c["check"]: c for c in load(wd / "validation_report.json")["checks"]}
        rows.append((name, checks, (sp / "character.spine").exists()))

    junit = d["07_Test_Reports"] / "pytest.xml"
    if run_tests:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={junit}"],
                           cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        (d["07_Test_Reports"] / "pytest_output.txt").write_text(r.stdout + r.stderr, encoding="utf-8")
    for f in ("TEST_RESULTS.md", "KNOWN_ISSUES.md"):
        shutil.copy2(ROOT / "docs" / f, d["07_Test_Reports"])

    build(chars, originals, junit if junit.exists() else None, d["05_Presentation"] / "workflow.pptx")

    dev = d["06_Development"]
    for sub in ("skills", "src", "tests", "openspec", "scripts", "docs"):
        copytree(ROOT / sub, dev / sub)
    for f in ("pyproject.toml", "README.md"):
        shutil.copy2(ROOT / f, dev)

    (out / "README.md").write_text(_readme(rows, junit), encoding="utf-8")
    return out


def _import_md(name, sp, export):
    """Spine 匯入說明：版本、檔案雜湊、匯入指令、驗收清單，全部取自實際檔案。"""
    import hashlib
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "src"))
    from character_to_spine.animation_builder import duration
    from character_to_spine.spine_exporter import find_spine
    skel = load(sp / "character.json")
    exe, trial = find_spine()
    imp = export["spine_import"]
    files = [sp / "character.json"] + sorted((sp / "images").glob("*.png"))
    lines = [f"# {name}：Spine 匯入說明", "",
             f"**`.spine` 驗收狀態：{imp['status']}**。{imp['detail']}", "",
             "## 版本", "",
             f"- JSON 的 `skeleton.spine`：`{skel['skeleton']['spine']}`（匯出時可用 `c2s export --spine-version <版本>` 改成實際 Editor 的版本）",
             f"- 本機偵測到的 Spine：`{exe or '未安裝'}`" + ("（試用版：CLI 不能匯入、不能存檔）" if trial else ""),
             "- 本專案只用 Spine 4.2／4.3 共通的格式：bones、slots、region 附件、rotate／translate／scale、bezier 曲線；"
             "不需要 Professional 功能（無 Mesh、IK、約束），Essential 授權即可",
             "", "## 內容", "",
             f"- 骨頭 {len(skel['bones'])} 根、插槽 {len(skel['slots'])} 個、圖片 {len(files) - 1} 張",
             "- 動畫：" + "、".join(f"{a}（{duration(v)} 秒）" for a, v in skel["animations"].items()),
             "", "## 檔案與 SHA-256", "", "| 檔案 | SHA-256 |", "|---|---|"]
    lines += [f"| `{p.relative_to(sp).as_posix()}` | `{hashlib.sha256(p.read_bytes()).hexdigest()}` |" for p in files]
    lines += ["", "## 匯入（需要 Essential 或 Professional 授權）", "",
              "圖形介面：Spine 選單的 Import Data，選 `character.json`，縮放 1.0。圖片從同目錄的 `images/` 讀取。"
              "（對話框的選項名稱未在完整版上驗證，以實際介面為準。）", "",
              "CLI（Windows，於本目錄執行；語法取自官方 Command Line Interface 文件）：", "", "```",
              f"Spine.com -u {skel['skeleton']['spine']} -i character.json -o character.spine -r character",
              "Spine.com -i character.spine -o roundtrip -e json", "```", "",
              "或用本專案自動匯入並往返比對：`set SPINE_EXE=<Spine.com 路徑>` 後執行 `c2s run <圖片>`。", "",
              "## 匯入後驗收清單", "",
              "- [ ] 匯入沒有錯誤或警告",
              "- [ ] Setup 模式下各部件位置與原圖一致",
              "- [ ] Animate 模式播放 `idle`、`happy`，動作與 `04_Animation_Preview` 的 Python Simulation Preview 一致",
              "- [ ] 拖動任一關鍵影格、改一根骨頭的角度，可以存檔（確認可編輯）",
              "- [ ] 往返匯出的 JSON 骨頭、插槽、動畫名稱與原始相同（`c2s run` 的 `spine_roundtrip` 會自動檢查）", ""]
    return "\n".join(lines)


def _readme(rows, junit):
    from make_slides import junit_counts
    tests = junit_counts(junit)
    lines = ["# Character-to-Spine AI 交付物", "",
             "所有檔案皆複製自實際輸出；狀態取自各角色的 `validation_report.json`。", ""]
    for name, _, has_spine in rows:
        if not has_spine:
            lines += [f"> **`{name}` 的 `.spine` 專案：BLOCKED。** 這台機器只有 Spine 試用版，CLI 無法匯入也不能存檔。"
                      f"`03_Spine_Project/{name}/` 內是 Spine JSON（`character.json`）與 `images/`，"
                      "取得完整版授權後執行 `c2s export --spine-exe <Spine.com>` 即可產生 `.spine`。", ""]
    lines += ["## 驗證狀態", "", "| 檢查項目 | " + " | ".join(n for n, _, _ in rows) + " |",
              "|---|" + "---|" * len(rows)]
    for key, lab in CHECK_LABELS.items():
        lines.append(f"| {lab} | " + " | ".join(c.get(key, {"status": "NOT_TESTED"})["status"] for _, c, _ in rows) + " |")
    lines += ["", f"自動化測試：{tests['passed']}/{tests['total']} 通過（`07_Test_Reports/pytest.xml`）" if tests else "自動化測試：未執行", "",
              "## 目錄", "",
              "| 目錄 | 內容 |", "|---|---|",
              "| `00_Skill_v1.0/` | **可安裝的 Claude Skill**：`character-to-spine-skill-v1.0.0.zip`（解壓到 `.claude/skills/`）、解壓後的資料夾、安裝說明 `INSTALL_README.md` |",
              "| `01_Original_Images/` | 原始角色圖片（未修改） |",
              "| `02_Layered_Assets/<角色>/` | `PNG/` 透明分層圖、`metadata.json`、`parts.json`、`repair_tasks.md`（待人工修補）、`layer_preview.png` |",
              "| `03_Spine_Project/<角色>/` | `character.json`（Spine 4.3 JSON）、`images/`；有完整版 Spine 時另有 `character.spine` |",
              "| `04_Animation_Preview/` | Idle／Happy 的 **Python Simulation Preview** GIF（自寫骨架求值器，不是 Spine 算圖） |",
              "| `05_Presentation/` | `workflow.pptx` 製作流程簡報 |",
              "| `06_Development/` | Skill、Python 原始碼、測試、OpenSpec 規格、文件 |",
              "| `07_Test_Reports/` | pytest 報告、各角色驗證報告、動畫品質報告與異常影格（`<角色>/quality/`）、`tuning.json`、`TEST_RESULTS.md`、`KNOWN_ISSUES.md` |", "",
              "## 在 Spine 中使用（需完整版）", "",
              "1. Spine → Import Data → 選 `03_Spine_Project/<角色>/character.json`（圖片路徑為同目錄的 `images/`）。",
              "2. 或用 CLI：`Spine.com -i character.json -o character.spine -r character`。", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--chars", nargs="+", required=True, help="角色工作目錄，第一個是主要角色")
    ap.add_argument("--out", default=str(ROOT / "Character-to-Spine-Deliverables"))
    ap.add_argument("--skip-tests", action="store_true")
    a = ap.parse_args()
    print(package(a.chars, a.out, run_tests=not a.skip_tests))
