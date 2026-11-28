"""生成式補圖實驗：Codex 內建 image_gen 生成一個部件 → c2s prepare --generated 融合 → 對照圖與量測值。

python scripts/repair_experiment.py <圖片> <部件> --what "部件描述" --hide "要移除的遮擋者" --tag e1 [--gen 已有的生成圖]
    工作目錄 output/v12/<tag 的角色>；結果在 output/experiments/<tag>/：<部件>_<n>.png（生成圖）、
    <部件>_<n>_compare.png（原圖｜v1.1 草稿｜對齊後的生成圖｜融合後）、<部件>_<n>.json（量測值與判定）。
只能用在使用者已許可雲端處理的角色（c2s consent）。--gen 給定時不呼叫 Codex。
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from character_to_spine import load_json  # noqa: E402
from character_to_spine.fusion import MARKER, align  # noqa: E402
from character_to_spine.gen_repair import load_provenance, overrides_dir  # noqa: E402
from character_to_spine.image_processor import part_mask  # noqa: E402

C2S = ROOT / ".venv" / "Scripts" / "c2s.exe"
PROMPT = """請使用內建 image_gen 工具（編輯模式，以附加的角色圖片為參考；不要使用 CLI、API Key 或其他模型）。
生成一張只有這個角色「{what}」的圖：想像把{hide}拿掉後，這個部件完整的樣子。
- 畫布構圖與參考圖完全相同：部件的位置、大小、比例都和參考圖裡一致，不要放大置中。
- 保持原角色的 3D 算圖風格、顏色、光影、材質與服裝細節；肢體數量與關節位置正確。
- 只畫這個部件，不要畫其他身體部位、道具、頭髮或特效。背景完全透明。
生成後把檔案從 $CODEX_HOME/generated_images 複製到 {dest}（覆蓋同名檔）。
最後只回報一行：實際送給 image_gen 的 prompt。若 image_gen 不可用，原樣回報錯誤，不要改用其他方式。"""


REMOVE = """請使用內建 image_gen 工具（編輯模式，編輯附加的角色圖片；不要使用 CLI、API Key 或其他模型）。
把圖中的{hide}完全移除，並補畫出原本被擋住的{what}。
- 其他所有內容保持不變：構圖、畫布大小比例、角色位置與大小、姿勢、臉、服裝、顏色、光影與 3D 材質，不要重新構圖或放大。
- 補畫的部分要延續原角色的設計與材質；肢體數量與關節位置正確，不要多出或少掉手腳。
- 背景保持透明（或純白）。
生成後把檔案從 $CODEX_HOME/generated_images 複製到 {dest}（覆蓋同名檔）。
最後只回報一行：實際送給 image_gen 的 prompt。若 image_gen 不可用，原樣回報錯誤，不要改用其他方式。"""


MASKED = """請使用內建 image_gen 工具（編輯模式，編輯附加的圖片；不要使用 CLI、API Key 或其他模型）。
圖中洋紅色（#FF00FF）的區域原本被{hide}擋住。請把洋紅色區域補畫成{what}，自然延續周圍看得見的形狀、材質與光影。
- 洋紅色以外的所有內容保持完全不變：構圖、畫布大小比例、角色位置與大小、姿勢、臉、服裝、顏色與 3D 材質，不要重新構圖或放大。
- 補畫的部分要延續原角色的設計；肢體數量與關節位置正確。不要留下任何洋紅色。背景保持透明（或純白）。
- 不要自行裁切、縮放、對齊、合成或後製；直接複製 image_gen 的原始輸出檔（對齊與融合由 c2s 處理）。
生成後把檔案從 $CODEX_HOME/generated_images 複製到 {dest}（覆蓋同名檔）。
最後只回報一行：實際送給 image_gen 的 prompt。若 image_gen 不可用，原樣回報錯誤，不要改用其他方式。"""


def generate(image, what, hide, dest, mode="remove"):
    prompt = {"remove": REMOVE, "part": PROMPT, "mask": MASKED}[mode].format(what=what, hide=hide, dest=dest)
    log = dest.with_suffix(".codex.log")
    with open(log, "w", encoding="utf-8") as f:
        subprocess.run(["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", str(ROOT),
                        "-i", str(image), "-"], input=prompt, text=True, encoding="utf-8", stdout=f, stderr=subprocess.STDOUT,
                       timeout=1200)
    if not dest.exists():
        raise SystemExit(f"Codex 沒有產生 {dest}，見 {log}")
    return prompt


def marked(wd, part, out):
    """原圖，部件被遮住的區域塗成 MARKER。"""
    src = np.array(Image.open(wd / "source_rgba.png"))
    h, w = src.shape[:2]
    doc = load_json(wd / "parts.json")
    p = next(q for q in doc["parts"] if q["name"] == part)
    above = np.zeros((h, w), bool)
    for q in doc["parts"]:
        if q["z"] > p["z"]:
            above |= part_mask(q, (h, w))
    hid = part_mask(p, (h, w)) & above & (src[..., 3] > 0)
    src[hid] = (*MARKER, 255)
    Image.fromarray(src).save(out)


def checker(h, w, n=12):
    yy, xx = np.mgrid[0:h, 0:w]
    return np.where(((yy // n + xx // n) % 2)[..., None] == 0, 235, 200).astype(np.float32).repeat(3, 2)


def over(rgba, bg):
    a = rgba[..., 3:4] / 255.0
    return (rgba[..., :3] * a + bg * (1 - a)).astype(np.uint8)


def compare(wd, part, gen_path, baseline_layer, out):
    """四欄：原圖｜v1.1 草稿圖層｜對齊後的生成圖｜融合後的圖層。紅框＝被遮住、由生成圖補上的區域。"""
    src = np.array(Image.open(wd / "source_rgba.png"))
    h, w = src.shape[:2]
    doc = load_json(wd / "parts.json")
    p = next(q for q in doc["parts"] if q["name"] == part)
    mask = part_mask(p, (h, w))
    above = np.zeros((h, w), bool)
    for q in doc["parts"]:
        if q["z"] > p["z"]:
            above |= part_mask(q, (h, w))
    solid = mask & ~above & (src[..., 3] > 200)
    gen = np.array(Image.open(gen_path).convert("RGBA"))
    s, ox, oy = align(src, solid, gen)
    g = cv2.resize(gen, (round(gen.shape[1] * s), round(gen.shape[0] * s)), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    aligned = cv2.warpAffine(g, np.float32([[1, 0, ox], [0, 1, oy]]), (w, h), borderValue=(0, 0, 0, 0))

    def canvas_layer(path):
        if not path or not Path(path).exists():
            return np.zeros((h, w, 4), np.uint8)
        meta = load_json(Path(path).parents[1] / "metadata.json")
        e = next(x for x in meta["parts"] if x["name"] == part)
        c = np.zeros((h, w, 4), np.uint8)
        c[e["y"]:e["y"] + e["h"], e["x"]:e["x"] + e["w"]] = np.array(Image.open(path).convert("RGBA"))
        return c

    ys, xs = np.nonzero(mask)
    m = 20
    x0, y0, x1, y1 = max(0, xs.min() - m), max(0, ys.min() - m), min(w, xs.max() + m), min(h, ys.max() + m)
    bg = checker(y1 - y0, x1 - x0)
    cols = [over(src[y0:y1, x0:x1], bg), over(canvas_layer(baseline_layer)[y0:y1, x0:x1], bg),
            over(aligned[y0:y1, x0:x1], bg), over(canvas_layer(wd / "layers" / f"{part}.png")[y0:y1, x0:x1], bg)]
    hid = (mask & above)[y0:y1, x0:x1].astype(np.uint8)
    edge = cv2.morphologyEx(hid, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(bool)
    for c in cols[1:]:
        c[edge] = (230, 30, 30)
    sheet = Image.new("RGB", ((x1 - x0) * 4 + 30, y1 - y0 + 24), "white")
    d = ImageDraw.Draw(sheet)
    for i, (c, label) in enumerate(zip(cols, ["original", "v1.1 draft", "image_gen aligned", "v1.2 fused"])):
        sheet.paste(Image.fromarray(c), (i * (x1 - x0 + 10), 24))
        d.text((i * (x1 - x0 + 10) + 4, 4), label, fill="black")
    sheet.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("part")
    ap.add_argument("--what", required=True)
    ap.add_argument("--hide", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--workdir")
    ap.add_argument("--baseline", help="v1.1 的工作目錄（取草稿圖層做對照）")
    ap.add_argument("--gen")
    ap.add_argument("--mode", choices=["mask", "remove", "part"], default="mask",
                    help="mask：被遮區塗成洋紅色再請 image_gen 填（預設）；remove：編輯原圖、移除遮擋者；part：只畫這個部件")
    a = ap.parse_args()
    image = Path(a.image).resolve()
    wd = Path(a.workdir or ROOT / "output" / "v12" / a.tag.split("_")[0]).resolve()
    if not (wd / "parts.json").exists():
        subprocess.run([str(C2S), "analyze", str(image), "-w", str(wd)], check=True, capture_output=True)
    exp = ROOT / "output" / "experiments" / a.tag
    exp.mkdir(parents=True, exist_ok=True)
    n = 1 + len(list(exp.glob(f"{a.part}_[0-9].png")))
    gen = exp / f"{a.part}_{n}.png"
    if a.gen:
        gen.write_bytes(Path(a.gen).read_bytes())
        prompt = None
    else:
        source = image
        if a.mode == "mask":
            source = exp / f"{a.part}_{n}_input.png"
            marked(wd, a.part, source)
        prompt = generate(source, a.what, a.hide, gen, a.mode)
    r = subprocess.run([str(C2S), "prepare", "-w", str(wd), "--generated", f"{a.part}={gen}", "--prompt", prompt or "(given)"],
                       capture_output=True, text=True, encoding="utf-8")
    prov = load_provenance(overrides_dir(wd, load_json(wd / "parts.json")))
    att = prov["parts"][a.part]["attempts"][-1]
    baseline = Path(a.baseline) / "layers" / f"{a.part}.png" if a.baseline else None
    compare(wd, a.part, gen, baseline, exp / f"{a.part}_{n}_compare.png")
    result = {"image": str(image), "part": a.part, "attempt": n, "exit_code": r.returncode, "verdict": att["verdict"],
              "reasons": att["reasons"], "metrics": att["metrics"], "prompt": prompt, "generated": str(gen)}
    (exp / f"{a.part}_{n}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
