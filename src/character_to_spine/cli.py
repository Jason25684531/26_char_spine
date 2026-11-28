"""c2s 命令列入口。結束碼：0 完成、1 失敗、2 需要補資料後接續、3 parts.json 宣告超出支援範圍。"""
import argparse
import json
import sys
import traceback
from pathlib import Path

from . import C2SError, NeedsInput, __version__, pipeline, spine_bridge
from .analyzer import analyze
from .doctor import doctor
from .animation_builder import MOTIONS, build_animations
from . import gen_repair
from .image_processor import grant_consent, prepare
from .preview import write_previews
from .quality import refine
from .rig_builder import PRESETS, build_rig
from .spine_exporter import DEFAULT_SPINE_VERSION, export
from .validator import validate


REPORT_HINT = ("照 SKILL.md 第 4～7 步檢查 layer_preview.png、report/visual_check.png 後回報；"
               "回報整份使用使用者提問的語言（中文提問就用中文），檔名與部件名稱是英文也一樣。")


def _parser():
    p = argparse.ArgumentParser(prog="c2s", description="Character-to-Spine：2D 角色圖片 → 分層 PNG → Spine 骨架與動畫")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)

    def cmd(name, help_, image=None):
        s = sub.add_parser(name, help=help_)
        if image:
            s.add_argument("image", nargs=None if image == "required" else "?", help="角色圖片（PNG/JPG）")
        s.add_argument("-w", "--workdir", help="工作目錄（預設 output/<圖片檔名>，或上一次使用的）")
        return s

    s = cmd("analyze", "讀圖、去背、檢查 parts.json", "required")
    s.add_argument("--parts", help="parts.json 路徑（預設找 <圖片>.parts.json 或工作目錄內的 parts.json）")
    s.add_argument("--preset", default="humanoid-chibi", choices=list(PRESETS))

    s = cmd("prepare", "依 parts.json 切出透明分層 PNG", "optional")
    s.add_argument("--part", help="強制重寫這個部件的圖層（其他圖層只在內容有變時才重寫）")
    s.add_argument("--replace", action="append", default=[], metavar="NAME=PNG", help="用人工修好的 PNG 取代某個部件（可重複）")
    s.add_argument("--generated", metavar="NAME=PNG", help="生成圖：只取被遮住的像素融合進這個部件，原始看得見的像素不變")
    s.add_argument("--prompt", help="產生 --generated 這張圖用的 Prompt（寫入來源紀錄）")
    s.add_argument("--from-reference", metavar="IMAGE", help="--generated 的圖取自這張同角色參考圖，不是雲端生成")
    s.add_argument("--strategy", choices=list(gen_repair.STRATEGIES), help="這張生成圖用的策略（預設取登記時的策略）")
    s.add_argument("--begin", metavar="NAME", help="生成前登記一次嘗試（搭配 --prompt），回傳剩餘次數、策略與要交給生成工具的圖")
    s.add_argument("--reopen", metavar="NAME", help="已達上限的部件重新計次（必須附 --reason）")
    s.add_argument("--reason", help="--reopen 的理由，會寫入來源紀錄")
    s.add_argument("--rollback", metavar="NAME", help="這個部件回到上一個通過的生成成果")

    s = cmd("review", "記錄生成式補圖的目視判定（看過 visual_review/<部件>.png 之後）")
    s.add_argument("part")
    s.add_argument("--verdict", required=True, choices=list(gen_repair.VERDICTS), help="fail 會撤回這個補圖並計一次失敗")
    s.add_argument("--note", required=True, help="看到了什麼")
    s.add_argument("--by", default="agent", help="判定者（例如 codex、claude、美術姓名）")

    cmd("consent", "記錄使用者已明確許可這個角色交給 Codex 內建 image_gen（雲端）處理", "optional")

    s = cmd("rig", "建立骨架")
    s.add_argument("--preset", default=None, choices=list(PRESETS))

    s = cmd("animate", "產生動畫關鍵影格（一律包含 idle）")
    s.add_argument("--motion", default="happy", choices=MOTIONS)

    s = cmd("export", "輸出 Spine JSON，並嘗試用 Spine CLI 建立 .spine")
    s.add_argument("--format", default="spine", choices=["spine"])
    s.add_argument("--spine-version", default=DEFAULT_SPINE_VERSION)
    s.add_argument("--spine-exe", help="Spine.com 路徑（預設讀環境變數 SPINE_EXE 或自動尋找）")

    s = cmd("refine", "逐格檢查動畫品質並自動修正動作幅度（最多 3 輪），結束時 export")
    s.add_argument("--motion", default="happy", choices=MOTIONS)
    s.add_argument("--spine-version", default=DEFAULT_SPINE_VERSION)
    s.add_argument("--spine-exe")

    cmd("validate", "檢查輸出內容並產生 validation_report.json")
    cmd("preview", "用內建算圖器輸出動畫預覽 GIF（不是 Spine 的算圖結果）")

    sub.add_parser("doctor", help="檢查 Python、套件、Codex、image_gen、Spine 與 Skill 安裝位置")
    s = cmd("spine", "Spine Editor 橋接：import 匯入成新版本專案、open 開啟最新專案、sync 熱更新單一部件圖片")
    s.add_argument("action", choices=["import", "open", "sync"])
    s.add_argument("--part", help="sync：要更新的部件名稱")
    s.add_argument("--restore", action="store_true", help="sync：還原這個部件的上一版圖片")
    s.add_argument("--project", help="open：指定專案檔（預設最新版本）")
    s.add_argument("--spine-exe")

    s = cmd("run", "一次跑完整個流程", "required")
    s.add_argument("--motion", default="happy", choices=MOTIONS)
    s.add_argument("--parts")
    s.add_argument("--preset", default="humanoid-chibi", choices=list(PRESETS))
    s.add_argument("--spine-version", default=DEFAULT_SPINE_VERSION)
    s.add_argument("--spine-exe")
    return p


def _dispatch(a, wd):
    if a.command == "analyze":
        return analyze(a.image, wd, a.parts, a.preset)
    if a.command == "prepare":
        if a.image and not (wd / "source_rgba.png").exists():
            analyze(a.image, wd)
        bad = [r for r in a.replace + [a.generated or "="] if "=" not in r]
        if bad:
            raise C2SError(f"--replace／--generated 格式應為 NAME=PNG，收到 {bad[0]!r}")
        gen = (*a.generated.split("=", 1), a.prompt) if a.generated else None
        if a.begin:
            return gen_repair.begin(wd, a.begin, a.prompt, a.strategy)
        if a.reopen:
            gen_repair.reopen(wd, a.reopen, a.reason)
        if a.rollback:
            gen_repair.rollback(wd, a.rollback)
        return prepare(wd, a.part, dict(r.split("=", 1) for r in a.replace), gen, a.from_reference, a.strategy)
    if a.command == "review":
        out = gen_repair.review(wd, a.part, a.verdict, a.note, a.by)
        prepare(wd)
        return out
    if a.command == "consent":
        if a.image and not (wd / "parts.json").exists():
            analyze(a.image, wd)
        return grant_consent(wd)
    if a.command == "rig":
        return build_rig(wd, a.preset)
    if a.command == "animate":
        return build_animations(wd, a.motion)
    if a.command == "export":
        return export(wd, a.spine_version, a.spine_exe)
    if a.command == "refine":
        return refine(wd, a.motion, a.spine_version, a.spine_exe)
    if a.command == "validate":
        return validate(wd)
    if a.command == "preview":
        return {"status": "ok", "previews": write_previews(wd)}
    if a.command == "spine":
        if a.action == "import":
            return spine_bridge.import_project(wd, a.spine_exe)
        if a.action == "open":
            return spine_bridge.open_project(wd, a.project, a.spine_exe)
        if not a.part:
            raise C2SError("c2s spine sync 需要 --part <部件名稱>")
        return spine_bridge.sync_image(wd, a.part, a.restore)
    return pipeline.run(a.image, a.motion, a.workdir, a.parts, a.preset, a.spine_version, a.spine_exe)


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    a = _parser().parse_args(argv)
    if a.command == "doctor":  # 不需要工作目錄；給人看的逐行結果
        checks = doctor()
        for c in checks:
            print(f"[{c['status']}] {c['name']}：{c['detail']}" + (f"\n    → {c['fix']}" if c["fix"] else ""))
        return 1 if any(c["status"] == "FAIL" for c in checks) else 0
    wd = None
    try:
        wd = pipeline.resolve_workdir(getattr(a, "image", None), a.workdir)
        result = _dispatch(a, wd)
    except NeedsInput as e:
        print(json.dumps({"status": "needs_input", "workdir": str(wd), "message": str(e)}, ensure_ascii=False, indent=2))
        return 2
    except Exception as e:
        log = _write_log(wd, argv, traceback.format_exc())
        kind = "error" if isinstance(e, C2SError) else "unexpected_error"
        print(json.dumps({"status": kind, "message": str(e), "log": log}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    if a.command == "run" and result.get("status") not in ("needs_input", "needs_parts"):
        # 放在 Agent 寫回報前最後讀到的輸出：只寫在 SKILL.md 開頭時，Ref_pic 驗收 12 次有 2 次最後回報改用英文
        result["next"] = REPORT_HINT
    print(json.dumps(result, ensure_ascii=False, indent=2))
    status = result.get("status")
    if status == "FAIL":
        failed = [c for c in result.get("checks", result.get("steps", {}).get("validate", {}).get("checks", []))
                  if c["status"] == "FAIL"]
        _write_log(wd, argv, "驗證失敗：\n" + json.dumps(failed, ensure_ascii=False, indent=2))
        return 1
    (Path(wd) / "c2s_error.log").unlink(missing_ok=True)  # 成功後不留上一次失敗的紀錄
    if status == "unsupported":
        return 3
    if a.command == "spine" and status == "BLOCKED":  # 只限 spine：validate 的 BLOCKED 維持結束碼 0
        return 2
    return 2 if status in ("needs_input", "needs_parts") else 0


def _write_log(wd, argv, body):
    """任何失敗都留下診斷資訊。回傳 log 路徑（寫不進去時為 None）。"""
    log = Path(wd or ".") / "c2s_error.log"
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(f"command: {sys.argv if argv is None else argv}\n\n{body}", encoding="utf-8")
        return str(log)
    except OSError:
        return None


if __name__ == "__main__":
    sys.exit(main())
