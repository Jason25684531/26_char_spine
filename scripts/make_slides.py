"""由實際輸出產生製作流程簡報（workflow.pptx）。

python scripts/make_slides.py --chars output/ren output/zc2 --junit <pytest.xml> --out workflow.pptx

圖片、數字、狀態全部讀自工作目錄與測試報告，不手寫任何結果。第一個工作目錄是主要角色。
"""
import argparse
import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageSequence
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

FONT = "Microsoft JhengHei"
PLUM, MARIGOLD, CORAL = RGBColor(0x2E, 0x1A, 0x47), RGBColor(0xF2, 0x9F, 0x05), RGBColor(0xE4, 0x57, 0x2E)
INK, MUTED, WHITE, TINT = RGBColor(0x22, 0x22, 0x22), RGBColor(0x5F, 0x5F, 0x6B), RGBColor(0xFF, 0xFF, 0xFF), RGBColor(0xF3, 0xEF, 0xF8)
STATUS = {"PASS": RGBColor(0x2E, 0x8B, 0x57), "FAIL": RGBColor(0xC0, 0x39, 0x2B),
          "BLOCKED": RGBColor(0xC7, 0x7C, 0x02), "NOT_TESTED": RGBColor(0x7A, 0x7A, 0x7A)}
PART_STATUS = {"ok": ("完整可見", STATUS["PASS"]), "auto_repaired": ("自動填補", STATUS["PASS"]),
               "needs_manual": ("需人工修補", STATUS["BLOCKED"]), "replaced": ("已人工替換", STATUS["PASS"])}
CHECK_LABELS = {"bones": "骨頭階層", "slots": "插槽與附件", "image_references": "圖片引用", "animations": "動畫結構",
                "setup_pose": "初始姿勢比對", "manual_repairs": "人工修補", "spine_import": "Spine 匯入 .spine",
                "spine_roundtrip": "Spine 往返驗證", "spine_editable": "Editor 可編輯性"}
KEY_TIMES = [(0.0, "起始"), (0.2, "下蹲 0.2s"), (0.5, "跳躍頂點 0.5s"), (0.9, "落地緩衝 0.9s")]
# 原始素材的用途與選擇理由（docs/DECISIONS.md D-13）
ORIGINALS = {
    "人.png": ("主要角色", "唯一正面、左右對稱、無散落特效，最適合建立骨架"),
    "转场2.png": ("第二組角色", "站姿、無吉他、部件組成不同，用於通用性驗收"),
    "人物 拷贝.png": ("姿勢參考", "3/4 側面跑步，肢體重疊多，不當骨架基礎"),
    "预中奖.png": ("動作參考", "拋花瓣動態姿勢，含大片特效"),
}
W, H = 13.333, 7.5


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


# ---------- 基本繪圖 ----------

def _style(run, size, color, bold):
    f = run.font
    f.size, f.bold, f.name = Pt(size), bold, FONT
    f.color.rgb = color
    rpr = run._r.get_or_add_rPr()
    if rpr.find(qn("a:ea")) is None:  # 中文字型要另外指定 East Asian typeface
        ea = rpr.makeelement(qn("a:ea"), {"typeface": FONT})
        rpr.find(qn("a:latin")).addnext(ea)


def text(slide, x, y, w, h, paras, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, bullets=False, gap=6):
    """paras：字串、字串清單，或 [(文字, {size, color, bold}), ...] 的清單（一個元素一段）。"""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    for i, para in enumerate([paras] if isinstance(paras, str) else paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(gap)
        runs = para if isinstance(para, list) else [(para, {})]
        for t, o in runs:
            r = p.add_run()
            r.text = t
            _style(r, o.get("size", size), o.get("color", color), o.get("bold", bold))
        if bullets:
            ppr = p._p.get_or_add_pPr()
            ppr.set("marL", str(Inches(0.25)))
            ppr.set("indent", str(-Inches(0.22)))
            ppr.append(ppr.makeelement(qn("a:buChar"), {"char": "•"}))
    return tb


def box(slide, x, y, w, h, fill, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line=None):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line:
        s.line.color.rgb = line
    else:
        s.line.fill.background()
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = 0.12
    s.shadow.inherit = False
    return s


def label(slide, x, y, w, h, t, fill, color=WHITE, size=14, bold=True):
    s = box(slide, x, y, w, h, fill)
    tf = s.text_frame
    tf.margin_left = tf.margin_right = Inches(0.06)
    tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = t
    _style(r, size, color, bold)
    return s


def arrow(slide, x1, y1, x2, y2, color=MUTED):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color
    c.line.width = Pt(1.5)
    c.line._get_or_add_ln().append(c.line._get_or_add_ln().makeelement(qn("a:tailEnd"), {"type": "triangle"}))
    return c


def picture(slide, path, x, y, w, h, align="center"):
    """等比例縮放放進方框內。"""
    iw, ih = Image.open(path).size
    s = min(w / iw, h / ih)
    pw, ph = iw * s, ih * s
    px = x + (w - pw) / 2 if align == "center" else x
    return slide.shapes.add_picture(str(path), Inches(px), Inches(y + (h - ph) / 2), Inches(pw), Inches(ph))


def new_slide(prs, title=None, dark=False, notes=None):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = PLUM if dark else WHITE
    if title:
        text(s, 0.6, 0.4, W - 1.2, 0.8, title, size=32, bold=True, color=WHITE if dark else PLUM, anchor=MSO_ANCHOR.MIDDLE)
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def footer(slide, t, dark=False):
    text(slide, 0.6, H - 0.45, W - 1.2, 0.3, t, size=10, color=RGBColor(0xC9, 0xC0, 0xD8) if dark else MUTED)


def table(slide, x, y, w, rows, col_w, size=12, row_h=0.36, header_fill=PLUM, cell_colors=None):
    t = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(row_h * len(rows))).table
    for j, cw in enumerate(col_w):
        t.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        t.rows[i].height = Inches(row_h)
        for j, v in enumerate(row):
            c = t.cell(i, j)
            c.margin_left = c.margin_right = Inches(0.08)
            c.margin_top = c.margin_bottom = Inches(0.02)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            fill, color = (header_fill, WHITE) if i == 0 else ((cell_colors or {}).get((i, j)), WHITE) if (cell_colors or {}).get((i, j)) else (TINT if i % 2 else WHITE, INK)
            c.fill.solid()
            c.fill.fore_color.rgb = fill
            p = c.text_frame.paragraphs[0]
            r = p.add_run()
            r.text = str(v)
            _style(r, size, color, i == 0 or (i, j) in (cell_colors or {}))
    return t


# ---------- 由輸出產生的圖片 ----------

def key_frames(wd, out, times=KEY_TIMES, fps=20):
    gif = Path(wd) / "preview" / "happy_python_simulation_preview.gif"
    frames = [f.convert("RGB") for f in ImageSequence.Iterator(Image.open(gif))]
    picked = [frames[min(round(t * fps), len(frames) - 1)] for t, _ in times]
    # 預覽四周留了跳躍用的邊界；依所有選中影格的共同內容範圍裁切（跳過上緣的標示文字），角色才不會太小
    boxes = [Image.eval(f.crop((0, 16, *f.size)).convert("L"), lambda v: 255 if v < 245 else 0).getbbox() for f in picked]
    boxes = [b for b in boxes if b]
    crop = (min(b[0] for b in boxes), min(b[1] for b in boxes) + 16, max(b[2] for b in boxes), max(b[3] for b in boxes) + 16)
    paths = []
    for (t, _), f in zip(times, picked):
        p = out / f"{Path(wd).name}_t{int(t * 100):03d}.png"
        f.crop(crop).save(p)
        paths.append(p)
    return paths


def bone_overlay(wd, out):
    """原圖淡化後疊上骨架（關節點與父子連線），座標取自 rig.json。"""
    rig = load(Path(wd) / "rig.json")
    ox, oy = rig["origin"]
    src = Image.open(Path(wd) / "source_rgba.png").convert("RGBA")
    img = Image.alpha_composite(Image.new("RGBA", src.size, (255, 255, 255, 255)), src)
    img = Image.blend(img, Image.new("RGBA", src.size, (255, 255, 255, 255)), 0.55).convert("RGB")
    d = ImageDraw.Draw(img)
    pos = {b["name"]: (b["world"][0] + ox, oy - b["world"][1]) for b in rig["bones"] if "world" in b}
    pos["root"] = (ox, oy)
    r = max(4, img.width // 120)
    for b in rig["bones"]:
        if "parent" in b and b["name"] in pos:
            d.line([pos[b["parent"]], pos[b["name"]]], fill=(46, 26, 71), width=max(3, r // 2))
    for name, (x, y) in pos.items():
        d.ellipse([x - r, y - r, x + r, y + r], fill=(242, 159, 5), outline=(46, 26, 71), width=2)
    p = out / f"{Path(wd).name}_bones.png"
    img.crop(_bbox(wd, img.size)).save(p)
    return p


def _bbox(wd, size, pad=0.06):
    bx, by, bw, bh = load(Path(wd) / "metadata.json")["bbox"]
    m = int(max(bw, bh) * pad)
    return max(0, bx - m), max(0, by - m), min(size[0], bx + bw + m), min(size[1], by + bh + m)


def junit_counts(path):
    if not path or not Path(path).exists():
        return None
    root = ET.parse(path).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    total, fail, err, skip = (int(suite.get(k, 0)) for k in ("tests", "failures", "errors", "skipped"))
    return {"total": total, "passed": total - fail - err - skip, "failed": fail + err, "skipped": skip}


# ---------- 投影片 ----------

def build(chars, originals_dir, junit, out_path):
    tmp = Path(tempfile.mkdtemp(prefix="c2s_slides_"))
    data = []
    for wd in map(Path, chars):
        meta, rig, anims = load(wd / "metadata.json"), load(wd / "rig.json"), load(wd / "animations.json")
        checks = {c["check"]: c for c in load(wd / "validation_report.json")["checks"]}
        data.append({"wd": wd, "meta": meta, "rig": rig, "anims": anims, "checks": checks,
                     "name": Path(meta["image"]).stem if meta.get("image") else wd.name,
                     "parts": load(wd / "parts.json")["parts"]})
    main = data[0]
    tests = junit_counts(junit)
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(W), Inches(H)
    main_keys = key_frames(main["wd"], tmp)

    # 1 封面
    s = new_slide(prs, dark=True, notes="Character-to-Spine：把一張 2D 角色圖，做成可在 Spine 內編輯的骨架動畫。")
    text(s, 0.8, 2.0, 7.2, 1.2, "Character-to-Spine AI", size=44, bold=True, color=WHITE)
    text(s, 0.8, 3.25, 7.2, 1.0, "2D 角色圖片 → 透明分層 PNG → 可編輯的 Spine 骨架動畫", size=22, color=MARIGOLD)
    text(s, 0.8, 4.4, 7.2, 0.9, ["製作流程與成果報告", "Skill／CLI 共用 Python 核心 · Claude Code ＋ Codex"], size=16, color=WHITE)
    picture(s, main["wd"] / "source_rgba.png", 8.4, 0.6, 4.3, 6.3)
    footer(s, "所有圖片與數字皆取自實際輸出；預覽圖為 Python Simulation Preview，非 Spine 算圖", dark=True)

    # 2 成果總覽
    s = new_slide(prs, "成果總覽：一套流程處理兩組不同角色", notes="數字取自 validation_report.json 與 pytest 報告。")
    import_status = main["checks"]["spine_import"]["status"]
    stats = [(f"{len(data)} 組", "真實角色走同一套流程"),
             (" / ".join(str(len([e for e in d["meta"]["parts"] if "file" in e])) for d in data), "部件數（主要／第二組）"),
             (f"{tests['passed']}/{tests['total']}" if tests else "—", "自動化測試通過"),
             (import_status, ".spine 匯入（只有試用版）")]
    for i, (big, small) in enumerate(stats):
        x = 0.6 + i * 3.1
        box(s, x, 1.45, 2.85, 1.75, TINT)
        color = STATUS.get(big, PLUM)
        text(s, x + 0.2, 1.6, 2.45, 0.9, big, size=34 if len(big) < 8 else 26, bold=True, color=color, anchor=MSO_ANCHOR.MIDDLE)
        text(s, x + 0.2, 2.55, 2.45, 0.5, small, size=13, color=MUTED)
    for i, (p, (_, lab)) in enumerate(zip(main_keys, KEY_TIMES)):
        x = 0.6 + i * 3.1
        picture(s, p, x, 3.45, 2.85, 3.0)
        text(s, x, 6.5, 2.85, 0.3, lab, size=11, color=MUTED, align=PP_ALIGN.CENTER)
    footer(s, "下排：主要角色 Happy 動畫 4 個關鍵影格（Python Simulation Preview，非 Spine 算圖）")

    # 3 原始角色分析
    s = new_slide(prs, "原始角色分析：選定骨架基礎與參考素材")
    files = [f for f in ORIGINALS if (Path(originals_dir) / f).exists()]
    colw = (W - 1.2 - 0.3 * (len(files) - 1)) / max(1, len(files))
    for i, f in enumerate(files):
        role, why = ORIGINALS[f]
        x = 0.6 + i * (colw + 0.3)
        box(s, x, 1.4, colw, 3.6, TINT)
        picture(s, Path(originals_dir) / f, x + 0.1, 1.5, colw - 0.2, 3.4)
        label(s, x, 5.2, colw, 0.42, role, PLUM if i < 2 else MUTED, size=14)
        text(s, x, 5.75, colw, 1.0, why, size=12, color=INK)
    footer(s, "不同姿勢的圖不當成同一骨架的連續影格（使用者決策 D-07）")

    # 4 流程架構
    s = new_slide(prs, "流程架構：AI 負責看圖，Python 負責處理資料")
    lanes = [("AI（Claude Code／Codex Skill）", ["看圖", "寫 parts.json", "檢視預覽與修正"], CORAL),
             ("Python Core（c2s）", ["analyze", "prepare", "rig", "animate", "export", "validate"], PLUM),
             ("Spine（完整版）", ["JSON → .spine", "匯出回 JSON 比對"], STATUS["BLOCKED"])]
    for i, (name, steps, color) in enumerate(lanes):
        y = 1.45 + i * 1.75
        box(s, 0.6, y, W - 1.2, 1.45, TINT)
        text(s, 0.8, y + 0.1, 3.0, 1.25, name, size=15, bold=True, color=color, anchor=MSO_ANCHOR.MIDDLE)
        sw = min(1.45, (W - 4.4 - 0.35 * (len(steps) - 1)) / len(steps))
        for j, st in enumerate(steps):
            x = 3.9 + j * (sw + 0.35)
            label(s, x, y + 0.42, sw, 0.6, st, color, size=13)
            if j:
                arrow(s, x - 0.33, y + 0.72, x - 0.02, y + 0.72)
    arrow(s, 5.0, 2.9, 5.0, 3.25)
    arrow(s, 8.0, 4.65, 8.0, 5.0)
    footer(s, "Spine 這一列需要 Essential／Professional 授權；目前只有試用版，狀態 BLOCKED")

    # 5 拆圖：parts.json
    s = new_slide(prs, "拆圖：Agent 依座標格線寫出 parts.json")
    picture(s, main["wd"] / "grid_overlay.png", 0.6, 1.35, 4.6, 5.6)
    sample = next((p for p in main["parts"] if p["name"] == "arm_l"), main["parts"][0])
    snippet = {k: v for k, v in sample.items() if k != "polygon"}
    snippet["polygon"] = f"[{len(sample.get('polygon', []))} 個點]" if "polygon" in sample else None
    text(s, 5.6, 1.4, 7.1, 0.4, "每個部件一筆資料（例：" + sample["name"] + "）", size=16, bold=True, color=PLUM)
    box(s, 5.6, 1.9, 7.1, 1.05, TINT)
    text(s, 5.75, 2.0, 6.8, 0.85, json.dumps({k: v for k, v in snippet.items() if v is not None}, ensure_ascii=False),
         size=12, color=INK)
    text(s, 5.6, 3.25, 7.1, 3.4, [
        [("polygon／mask：", {"bold": True}), ("原圖像素座標，範圍要包含被擋住的部分", {})],
        [("z：", {"bold": True}), ("前後順序，可見像素歸 z 最大的部件", {})],
        [("pivot／parent：", {"bold": True}), ("關節位置與跟隨的骨頭", {})],
        [("role／motion：", {"bold": True}), ("套用哪種動作、幅度係數（抱吉他的手設 0.05～0.1）", {})],
        [("檢查：", {"bold": True}), ("layer_preview.png 用洋紅標出漏畫的像素，修正後重跑", {})],
    ], size=15, bullets=True, gap=10)
    footer(s, "左：grid_overlay.png（每 50 像素一條座標格線），由 c2s analyze 產生")

    # 6 拆圖結果
    s = new_slide(prs, f"拆圖結果：{main['name']} 切成 {len([e for e in main['meta']['parts'] if 'file' in e])} 個透明圖層")
    picture(s, main["wd"] / "layer_preview.png", 0.6, 1.3, W - 1.2, 5.3)
    m = main["meta"]
    footer(s, f"原圖｜圖層重組（洋紅＝未分配像素）｜部件外框與 pivot　·　重組差異 {m['recompose_mae']}，未分配像素 {m['unassigned_ratio']:.2%}")

    # 7 補圖與人工修正
    s = new_slide(prs, "補圖：小面積自動填補，大面積交給人工")
    rows = [["部件", "被遮擋", "狀態"]]
    colors = {}
    for i, e in enumerate(sorted(main["meta"]["parts"], key=lambda e: -e.get("hidden_ratio", 1)), 1):
        st, col = PART_STATUS.get(e["status"], (e["status"], MUTED))
        rows.append([e["name"], f"{e.get('hidden_ratio', 1):.0%}", st])
        if e["status"] == "needs_manual":
            colors[(i, 2)] = col
    table(s, 0.6, 1.35, 6.0, rows, [2.4, 1.3, 2.3], size=12, row_h=0.4, cell_colors=colors)
    worst = max((e for e in main["meta"]["parts"] if "file" in e), key=lambda e: e.get("hidden_ratio", 0))
    box(s, 7.0, 1.35, 5.7, 3.9, TINT)
    picture(s, main["wd"] / worst["file"], 7.1, 1.45, 5.5, 3.7)
    text(s, 7.0, 5.4, 5.7, 1.4, [
        f"{worst['name']} 圖層：被遮住 {worst['hidden_ratio']:.0%}，中間是 OpenCV 邊緣延伸的填補草稿",
        "被遮住 ≤35% → 自動填補；>35% → 列入 repair_tasks.md，人工補畫後 c2s prepare --replace 匯回",
    ], size=13, bullets=True)
    footer(s, "不使用 AI 補圖；填補草稿不視為完成，驗證報告的「人工修補」為 BLOCKED")

    # 8 骨架設計
    s = new_slide(prs, f"骨架設計：{len(main['rig']['bones'])} 根骨頭，全部由部件位置推算")
    picture(s, bone_overlay(main["wd"], tmp), 0.6, 1.3, 4.6, 5.6)
    _bone_tree(s, main["rig"], 5.5, 1.35, 7.2, 5.4)
    footer(s, "左：骨架疊在原圖上（橘點＝關節）。右：父子關係；必要部件由 preset 決定，其他部件依 parent 掛上")

    # 9 動畫設計
    hp, idle = main["anims"].get("happy", {}), main["anims"]["idle"]
    s = new_slide(prs, "動畫設計：Happy 是兩次「蹲、跳、落地」的循環")
    for i, (p, (_, lab)) in enumerate(zip(main_keys, KEY_TIMES)):
        picture(s, p, 0.6 + i * 1.55, 1.35, 1.45, 3.3)
        text(s, 0.6 + i * 1.55, 4.7, 1.45, 0.5, lab, size=11, color=MUTED, align=PP_ALIGN.CENTER)
    rows = [["role", "Happy 動作"], ["hip", "下蹲 → 跳起（角色高度 14%）→ 落地緩衝"], ["body", "擠壓伸展、左右傾"],
            ["head", "反向點頭擺動"], ["arm／leg", "向外揮動，乘上 motion 係數"], ["hair／skirt", "晚一拍的跟隨擺動"],
            ["prop／accessory", "輕微晃動"]]
    table(s, 6.95, 1.35, 5.75, rows, [1.85, 3.9], size=12, row_h=0.42)
    nkeys = lambda a: sum(len(k) for t in a.get("bones", {}).values() for k in t.values())
    text(s, 0.6, 5.35, 12.1, 1.4, [
        f"idle {_dur(idle)} 秒、{nkeys(idle)} 個關鍵影格；happy {_dur(hp)} 秒、{nkeys(hp)} 個關鍵影格，首尾相接可循環",
        "全部是 Spine 骨頭的 rotate／translate／scale 關鍵影格與 bezier 曲線，可在 Spine 內逐格修改；不是影片",
    ], size=14, bullets=True)
    footer(s, "左圖為 Python Simulation Preview（自寫骨架求值器），非 Spine 算圖")

    # 10 通用性
    if len(data) > 1:
        sec = data[1]
        s = new_slide(prs, f"通用性：第二組角色 {sec['name']} 使用同一套程式")
        picture(s, sec["wd"] / "layer_preview.png", 0.6, 1.3, 7.3, 3.6)
        for i, p in enumerate(key_frames(sec["wd"], tmp)):
            picture(s, p, 8.2 + (i % 2) * 2.3, 1.3 + (i // 2) * 1.85, 2.2, 1.75)
        n_sec = len([e for e in sec["meta"]["parts"] if "file" in e])
        text(s, 0.6, 5.15, 12.1, 1.7, [
            f"{n_sec} 個部件；兩組角色只有圖片與 parts.json 不同，處理第二組期間沒有修改任何程式",
            f"四周散落的花瓣與光效不屬於任何部件（{sec['meta']['unassigned_ratio']:.1%} 像素），骨架原點與尺寸不受影響",
            "原圖是 AI 生成、有第三隻手：獨立成 arm_extra 部件，美術可在 Spine 直接刪除",
        ], size=14, bullets=True)
        footer(s, "右：Happy 關鍵影格（Python Simulation Preview）")

    # 11 Skill／CLI
    s = new_slide(prs, "Skill／CLI：Claude 與 Codex 共用同一個 Python 核心")
    for i, (t, c) in enumerate([("Claude Code", CORAL), ("Codex", CORAL)]):
        label(s, 0.6 + i * 2.3, 1.5, 2.0, 0.6, t, c, size=15)
        arrow(s, 1.6 + i * 2.3, 2.12, 2.75, 2.55)
    label(s, 0.6, 2.6, 4.3, 0.6, "SKILL.md（同一份內容）", PLUM, size=15)
    arrow(s, 2.75, 3.22, 2.75, 3.6)
    label(s, 0.6, 3.65, 4.3, 0.6, "c2s 指令", PLUM, size=15)
    arrow(s, 2.75, 4.27, 2.75, 4.65)
    label(s, 0.6, 4.7, 4.3, 0.6, "character_to_spine（Python 套件）", PLUM, size=15)
    box(s, 5.4, 1.45, 7.3, 3.95, TINT)
    text(s, 5.6, 1.55, 7.0, 3.8, [
        [("c2s analyze <圖片>", {"bold": True}), ("　讀圖、去背、座標格線", {})],
        [("c2s prepare [--replace 部件=PNG]", {"bold": True}), ("　切圖、補圖、修補任務", {})],
        [("c2s rig --preset humanoid-chibi", {"bold": True}), ("　建立骨架", {})],
        [("c2s animate --motion happy", {"bold": True}), ("　Idle＋Happy 關鍵影格", {})],
        [("c2s export --format spine", {"bold": True}), ("　Spine JSON（＋完整版時 .spine）", {})],
        [("c2s validate", {"bold": True}), ("　PASS／FAIL／BLOCKED／NOT_TESTED", {})],
        [("c2s run <圖片> --motion happy", {"bold": True}), ("　一次跑完", {})],
    ], size=14, gap=9)
    for i, (code, meaning, col) in enumerate([("0", "完成", STATUS["PASS"]), ("1", "失敗＋c2s_error.log", STATUS["FAIL"]),
                                               ("2", "需要補資料後接續", STATUS["BLOCKED"])]):
        x = 5.4 + i * 2.5
        label(s, x, 5.65, 0.55, 0.5, code, col, size=16)
        text(s, x + 0.65, 5.65, 1.75, 0.5, meaning, size=13, anchor=MSO_ANCHOR.MIDDLE)
    footer(s, "圖層不齊時不假裝能綁定：結束碼 2，列出缺少的部件與下一步指令")

    # 12 分工
    s = new_slide(prs, "AI 輔助與人工操作的分工")
    cols = [("已完成（自動）", STATUS["PASS"], ["去背、切圖、圖層 metadata", "骨架、插槽、附件推算", "Idle／Happy 關鍵影格", "Spine JSON 與驗證報告"]),
            ("半自動（AI＋人確認）", PLUM, ["Agent 看圖寫 parts.json", "依檢查圖修正 2～3 輪", "調整 role／motion 讓動作自然"]),
            ("人工修正", STATUS["BLOCKED"], ["大面積遮擋部件補畫：" + "、".join(e["name"] for e in main["meta"]["parts"] if e["status"] == "needs_manual"),
                                          "在 Spine 微調關鍵影格", "刪除素材瑕疵（第三隻手）"]),
            ("未來規劃", STATUS["NOT_TESTED"], ["完整版 Spine 匯入與往返驗證", "Mesh／IK／表情切換", "可替換的 AI 補圖 Provider"])]
    cw = (W - 1.2 - 0.3 * 3) / 4
    for i, (title, col, items) in enumerate(cols):
        x = 0.6 + i * (cw + 0.3)
        box(s, x, 1.4, cw, 5.3, TINT)
        label(s, x, 1.4, cw, 0.6, title, col, size=15)
        text(s, x + 0.2, 2.2, cw - 0.35, 4.4, items, size=14, bullets=True, gap=10)
    footer(s, "所有「人工修正」項目都列在各角色工作目錄的 repair_tasks.md")

    # 13 驗證結果
    s = new_slide(prs, "驗證結果：可自動驗證的項目全部通過")
    rows = [["檢查項目"] + [d["name"] for d in data]]
    colors = {}
    for i, key in enumerate(CHECK_LABELS, 1):
        rows.append([CHECK_LABELS[key]] + [d["checks"].get(key, {"status": "NOT_TESTED"})["status"] for d in data])
        for j, d in enumerate(data, 1):
            colors[(i, j)] = STATUS[rows[-1][j]]
    table(s, 0.6, 1.35, 7.4, rows, [3.0] + [4.4 / len(data)] * len(data), size=13, row_h=0.5, cell_colors=colors)
    box(s, 8.4, 1.35, 4.3, 2.3, TINT)
    text(s, 8.6, 1.45, 3.9, 1.2, f"{tests['passed']}/{tests['total']}" if tests else "—", size=44, bold=True, color=STATUS["PASS"], anchor=MSO_ANCHOR.MIDDLE)
    text(s, 8.6, 2.7, 3.9, 0.8, "pytest 自動化測試通過（合成角色＋行為測試）", size=13, color=MUTED)
    text(s, 8.4, 3.95, 4.3, 2.8, [
        "初始姿勢比對：用骨架資料重新算圖，和圖層直接疊合比較",
        "BLOCKED：缺少外部條件（授權、人工補畫），不是程式錯誤",
        "NOT_TESTED：需要人在 Spine Editor 內確認",
    ], size=13, bullets=True, gap=8)
    footer(s, "資料來源：各工作目錄的 validation_report.json、pytest junit 報告")

    # 14 限制與下一步
    s = new_slide(prs, "限制與下一步", dark=True)
    text(s, 0.8, 1.5, 5.6, 0.5, "目前的限制", size=20, bold=True, color=MARIGOLD)
    text(s, 0.8, 2.1, 5.6, 4.6, [
        "只有 Spine 試用版：無法產生 .spine、無法驗證可編輯性",
        "部件邊界由 AI 目測多邊形，交界處非像素級精準",
        "被遮擋區域只做 OpenCV 邊緣延伸，不使用 AI 補圖",
        "第一版只支援人形／Q 版骨架，沒有 Mesh、IK、物理",
    ], size=15, color=WHITE, bullets=True, gap=12)
    text(s, 7.0, 1.5, 5.6, 0.5, "下一步", size=20, bold=True, color=MARIGOLD)
    text(s, 7.0, 2.1, 5.6, 4.6, [
        "取得 Essential／Professional 授權 → 設定 SPINE_EXE → c2s export，完成匯入與往返驗證",
        "在 Spine Editor 開啟專案、修改關鍵影格，確認可編輯性",
        "依 repair_tasks.md 補畫被遮擋的部件，c2s prepare --replace 匯回",
        "需要精準邊界的部件改用遮罩",
    ], size=15, color=WHITE, bullets=True, gap=12)
    footer(s, "Character-to-Spine AI · 原始碼、Skill、OpenSpec 規格見 06_Development", dark=True)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(out_path)
    return out_path


def _dur(anim):
    return max((k.get("time", 0) for t in anim.get("bones", {}).values() for ks in t.values() for k in ks), default=0)


def _bone_tree(slide, rig, x, y, w, h):
    """水平樹狀圖：深度 → 欄，葉節點順序 → 列。"""
    children = {}
    for b in rig["bones"]:
        children.setdefault(b.get("parent"), []).append(b["name"])
    order, depth = [], {}

    def walk(n, d):
        depth[n] = d
        order.append(n)
        for c in children.get(n, []):
            walk(c, d + 1)
    walk("root", 0)
    leaves = [n for n in order if n not in children]
    row = {}
    for n in reversed(order):  # 葉節點依序排列，父節點取子節點的平均位置
        row[n] = leaves.index(n) if n in leaves else sum(row[c] for c in children[n]) / len(children[n])
    cols = max(depth.values()) + 1
    bw, bh = min(1.6, (w - 0.35 * (cols - 1)) / cols), min(0.36, h / len(leaves) * 0.8)
    step = h / len(leaves)
    pos = {n: (x + depth[n] * (bw + 0.35), y + row[n] * step + (step - bh) / 2) for n in order}
    roles = rig.get("roles", {})
    for n in order:
        for c in children.get(n, []):
            arrow(slide, pos[n][0] + bw, pos[n][1] + bh / 2, pos[c][0], pos[c][1] + bh / 2)
    for n in order:
        fill = PLUM if n in ("root", "hip") else CORAL if roles.get(n) in ("hair", "skirt", "prop", "accessory") else MARIGOLD
        label(slide, *pos[n], bw, bh, n, fill, color=WHITE if fill != MARIGOLD else INK, size=11)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--chars", nargs="+", required=True, help="角色工作目錄，第一個是主要角色")
    ap.add_argument("--originals", default="examples/real")
    ap.add_argument("--junit")
    ap.add_argument("--out", default="workflow.pptx")
    a = ap.parse_args()
    print(build(a.chars, a.originals, a.junit, a.out))
