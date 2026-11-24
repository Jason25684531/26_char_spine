"""把泛化測試的證據複製到 docs/generalization/<案例>/（output/ 不進版控）。

python scripts/export_generalization_docs.py

每個案例：最終與基準的視覺驗收圖、分層預覽、happy 動畫預覽、最終採用輪的異常影格、修補優先順序與對照圖、
修補任務、驗證報告。idle 預覽留在 output/（可由 run 重建）。
"""
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "generalization"
DOCS = ROOT / "docs" / "generalization"


def copy(src, dst):
    """PNG 縮到最長邊 1600、轉 256 色（證據圖只需看得清楚，避免 repo 膨脹）；其他檔案原樣複製。"""
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix != ".png":
        shutil.copy(src, dst)
        return
    img = Image.open(src).convert("RGB")
    img.thumbnail((1600, 1600))
    img.quantize(256).save(dst, optimize=True)


for case in sorted(p.name for p in OUT.iterdir() if (p / "work").is_dir()):
    wd, dst = OUT / case / "work", DOCS / case
    for label in ("baseline", "final"):
        copy(OUT / "_snapshots" / label / f"{case}_visual_sheet.png", dst / f"visual_sheet_{label}.png")
    copy(wd / "layer_preview.png", dst / "layer_preview.png")
    copy(wd / "repair_tasks.md", dst / "repair_tasks.md")
    copy(wd / "validation_report.json", dst / "validation_report.json")
    copy(wd / "quality" / "quality_report.json", dst / "quality_report.json")
    if case not in ("ren", "zc2"):
        copy(wd / "preview" / "happy_python_simulation_preview.gif", dst / "happy_python_simulation_preview.gif")
    for f in (wd / "report").glob("*"):
        copy(f, dst / "repair" / f.name)
    rounds = sorted((wd / "quality").glob("round_*"), key=lambda p: int(p.name.split("_")[1]))
    if rounds:
        for f in rounds[-1].glob("*.png"):
            copy(f, dst / "anomalies" / f.name)
    print(case)
