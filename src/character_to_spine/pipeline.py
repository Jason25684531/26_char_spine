"""共用流程：CLI 與 Skill 都走這裡。"""
from pathlib import Path

from . import C2SError, NeedsInput
from .analyzer import analyze
from .animation_builder import build_animations
from .image_processor import prepare
from .preview import write_previews
from .quality import refine
from .rig_builder import build_rig
from .spine_exporter import DEFAULT_SPINE_VERSION
from .validator import validate


def resolve_workdir(image=None, workdir=None):
    """工作目錄：明確指定 > ./output/<圖片檔名> > 上一次使用的（絕對路徑記在 ./output/.current）。"""
    root = Path("output").resolve()
    current = root / ".current"
    if workdir:
        wd = Path(workdir).resolve()
    elif image:
        wd = root / Path(image).stem
    elif current.exists():
        return Path(current.read_text(encoding="utf-8").strip())
    else:
        raise C2SError("不知道要處理哪個工作目錄：請用 --workdir 指定，或先執行 c2s analyze <圖片>")
    root.mkdir(exist_ok=True)
    current.write_text(str(wd), encoding="utf-8")
    return wd


def run(image, motion="happy", workdir=None, parts=None, preset="humanoid-chibi",
        spine_version=DEFAULT_SPINE_VERSION, spine_exe=None):
    """analyze → prepare → rig → animate → export → validate。缺資料時停在那一步並回報接續方式。"""
    wd = resolve_workdir(image, workdir)
    steps = {}
    try:
        steps["analyze"] = analyze(image, wd, parts, preset)
        if steps["analyze"]["status"] != "ok":
            a = steps["analyze"]
            reasons = a["parts_errors"] or [f"缺少必要部件：{', '.join(a['missing_required'])}"]
            raise NeedsInput("parts.json 尚未就緒：" + "；".join(reasons) + "。" + " → ".join(a["next_steps"]))
        steps["prepare"] = prepare(wd)
        steps["rig"] = build_rig(wd, preset)
        steps["animate"] = build_animations(wd, motion)
        steps["refine"] = refine(wd, motion, spine_version, spine_exe)  # 品質檢查與自我修正，結束時 export 一次
        steps["validate"] = validate(wd)
        steps["preview"] = write_previews(wd)
    except NeedsInput as e:
        return {"status": "needs_input", "workdir": str(wd), "stopped_after": list(steps), "message": str(e), "steps": steps}
    return {"status": steps["validate"]["status"], "workdir": str(wd), "steps": steps}
