"""簡報的近似版面預覽：沒有 PowerPoint／LibreOffice 時的 QA 工具。

python scripts/qa_slides.py <deck.pptx> <輸出目錄>

用微軟正黑體逐字換行，標出文字溢出（紅框）並列出超出投影片邊界的元素。只是近似：
不畫連接線，色塊內文字一律靠左。最終版面仍以 PowerPoint 為準。
# ponytail: 字型路徑寫死 Windows；其他平台再改成參數
"""
import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Emu

DPI = 100
FONT = "C:/Windows/Fonts/msjh.ttc"
FONT_B = "C:/Windows/Fonts/msjhbd.ttc"


def px(emu):
    return Emu(emu).inches * DPI


def font(size_pt, bold):
    return ImageFont.truetype(FONT_B if bold else FONT, max(6, round(size_pt * DPI / 72)))


def wrap_runs(tf, width):
    """回傳 [(行文字, font, color)]（每行使用該段第一個 run 的字型）。"""
    lines = []
    for p in tf.paragraphs:
        runs = [r for r in p.runs]
        if not runs:
            continue
        r0 = runs[0]
        f = font(r0.font.size.pt if r0.font.size else 18, bool(r0.font.bold))
        color = tuple(r0.font.color.rgb) if r0.font.color and r0.font.color.type is not None else (0, 0, 0)
        text = "".join(r.text for r in runs)
        indent = px(int(p._p.pPr.get("marL"))) if p._p.pPr is not None and p._p.pPr.get("marL") else 0
        line = "• " if indent else ""
        for ch in text:
            if f.getlength(line + ch) > width - indent:
                lines.append((line, f, color))
                line = ""
            line += ch
        lines.append((line, f, color))
    return lines


def draw_text(d, tf, x, y, w, h, problems, name):
    lines = wrap_runs(tf, w)
    total = sum(f.size * 1.25 for _, f, _ in lines)
    cy = y
    for t, f, c in lines:
        d.text((x, cy), t, font=f, fill=c)
        cy += f.size * 1.25
    if total > h + 2:
        d.rectangle([x, y, x + w, y + h], outline=(255, 0, 0), width=3)
        problems.append(f"{name}: 文字高度 {total:.0f}px > 方框 {h:.0f}px")


def render(path, out_dir):
    prs = Presentation(path)
    W, H = px(prs.slide_width), px(prs.slide_height)
    out_dir.mkdir(exist_ok=True)
    for i, slide in enumerate(prs.slides, 1):
        bg = slide.background.fill.fore_color.rgb if slide.background.fill.type else (255, 255, 255)
        img = Image.new("RGB", (round(W), round(H)), tuple(bg))
        d = ImageDraw.Draw(img)
        problems = []
        for sh in slide.shapes:
            x, y, w, h = px(sh.left), px(sh.top), px(sh.width), px(sh.height)
            if x < -1 or y < -1 or x + w > W + 1 or y + h > H + 1:
                problems.append(f"{sh.name}: 超出投影片邊界")
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
                pic = Image.open(io.BytesIO(sh.image.blob)).convert("RGB").resize((max(1, round(w)), max(1, round(h))))
                img.paste(pic, (round(x), round(y)))
            elif sh.shape_type == MSO_SHAPE_TYPE.LINE or sh.shape_type == MSO_SHAPE_TYPE.CONNECTOR if hasattr(MSO_SHAPE_TYPE, "CONNECTOR") else False:
                d.line([px(sh.begin_x), px(sh.begin_y), px(sh.end_x), px(sh.end_y)], fill=(110, 110, 120), width=2)
            elif sh.has_table if hasattr(sh, "has_table") else False:
                cy = y
                for r_i, row in enumerate(sh.table.rows):
                    cx = x
                    for c_i, col in enumerate(sh.table.columns):
                        cell = sh.table.cell(r_i, c_i)
                        cw, ch = px(col.width), px(row.height)
                        fill = tuple(cell.fill.fore_color.rgb) if cell.fill.type else (255, 255, 255)
                        d.rectangle([cx, cy, cx + cw, cy + ch], fill=fill, outline=(200, 200, 200))
                        draw_text(d, cell.text_frame, cx + 8, cy + 4, cw - 16, ch - 8, problems, f"{sh.name}[{r_i},{c_i}]")
                        cx += cw
                    cy += px(row.height)
            else:
                if getattr(sh, "fill", None) is not None and sh.fill.type == 1:
                    d.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=tuple(sh.fill.fore_color.rgb))
                if sh.has_text_frame and sh.text_frame.text.strip():
                    tf = sh.text_frame
                    ml, mt = px(tf.margin_left or 0), px(tf.margin_top or 0)
                    draw_text(d, tf, x + ml, y + mt, w - 2 * ml, h - 2 * mt, problems, sh.name)
        img.save(out_dir / f"slide-{i:02d}.png")
        print(f"slide {i:02d}: " + ("; ".join(problems) if problems else "OK"))


if __name__ == "__main__":
    render(sys.argv[1], Path(sys.argv[2]))
