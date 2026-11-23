"""spec: delivery-validation（交付打包、簡報）"""
import sys
from pathlib import Path

from pptx import Presentation

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from package_deliverables import package  # noqa: E402

DIRS = ["01_Original_Images", "02_Layered_Assets", "03_Spine_Project", "04_Animation_Preview",
        "05_Presentation", "06_Development", "07_Test_Reports"]


def test_package_from_real_outputs(built, tmp_path):
    a, b = built("synth_a"), built("synth_b")
    out = package([a, b], tmp_path / "deliv", run_tests=False)
    assert sorted(p.name for p in out.iterdir()) == sorted(DIRS + ["README.md"])
    # 檔案複製自實際輸出
    assert (out / "02_Layered_Assets" / "synth_a" / "PNG" / "head.png").read_bytes() == (a / "layers" / "head.png").read_bytes()
    assert (out / "03_Spine_Project" / "synth_b" / "character.json").read_bytes() == (b / "spine" / "character.json").read_bytes()
    assert list((out / "04_Animation_Preview").glob("*_python_simulation_preview.gif"))
    assert (out / "07_Test_Reports" / "synth_b" / "quality" / "quality_report.json").exists()
    # Spine 匯入說明：雜湊與實際檔案一致、標明狀態
    import hashlib
    imp = (out / "03_Spine_Project" / "synth_b" / "IMPORT.md").read_text(encoding="utf-8")
    assert hashlib.sha256((b / "spine" / "character.json").read_bytes()).hexdigest() in imp and "BLOCKED" in imp
    assert (out / "02_Layered_Assets" / "synth_b" / "report" / "repair_priority.md").exists()
    # 沒有 .spine：不放替代檔，README 標明 BLOCKED
    assert not list(out.rglob("*.spine"))
    readme = (out / "README.md").read_text(encoding="utf-8")
    assert "BLOCKED" in readme and "Python Simulation Preview" in readme
    # 簡報：文字與圖片取自輸出
    prs = Presentation(out / "05_Presentation" / "workflow.pptx")
    text = "\n".join(sh.text_frame.text for s in prs.slides for sh in s.shapes if sh.has_text_frame)
    assert "Python Simulation Preview" in text and "BLOCKED" in text and "synth_b" in text
    assert len(prs.slides) >= 12
