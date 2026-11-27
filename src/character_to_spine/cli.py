"""c2s 命令列入口。結束碼：0 完成、1 失敗、2 需要補資料後接續、3 parts.json 宣告超出支援範圍。"""
import argparse
import json
import sys
import traceback
from pathlib import Path

from . import C2SError, NeedsInput, __version__, pipeline
from .analyzer import analyze
from .animation_builder import MOTIONS, build_animations
from .image_processor import prepare
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
        bad = [r for r in a.replace if "=" not in r]
        if bad:
            raise C2SError(f"--replace 格式應為 NAME=PNG，收到 {bad[0]!r}")
        return prepare(wd, a.part, dict(r.split("=", 1) for r in a.replace))
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
    return pipeline.run(a.image, a.motion, a.workdir, a.parts, a.preset, a.spine_version, a.spine_exe)


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    a = _parser().parse_args(argv)
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
