"""
Generate README.pdf by parsing README.md directly — no manual text.
"""
import os, re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    HRFlowable, KeepTogether
)

BASE      = "/Users/symea1/ClaudeBoardStats"
DATA      = os.path.join(BASE, "data")
README    = os.path.join(BASE, "README.md")
OUTPUT    = os.path.join(BASE, "README.pdf")
MARGIN    = 2.2 * cm
PAGE_W, _ = A4
CONTENT_W = PAGE_W - 2 * MARGIN

body  = ParagraphStyle("body",  fontSize=10.5, fontName="Helvetica",
        textColor=colors.HexColor("#333344"), spaceAfter=8, leading=15)
code  = ParagraphStyle("code",  fontSize=8,    fontName="Courier",
        textColor=colors.HexColor("#333344"), backColor=colors.HexColor("#f5f5f8"),
        spaceAfter=2, leading=11, leftIndent=8, rightIndent=8)


def md_to_rl(text):
    """Convert minimal markdown inline formatting to ReportLab XML."""
    # strip markdown image syntax entirely (we handle images separately)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # links: keep link text only
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # bold+code e.g. **`foo`**
    text = re.sub(r'\*\*`([^`]+)`\*\*', r'<b><font name="Courier">\1</font></b>', text)
    # bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # inline code
    text = re.sub(r'`([^`]+)`', r'<font name="Courier" fontSize="9">\1</font>', text)
    # escape bare & < > that aren't our tags
    # (do this before adding tags — already done above via substitution order)
    text = text.replace('→', '\u2192').replace('—', '\u2014')
    return text.strip()


def embed_img(filename, max_w=CONTENT_W, max_h=16*cm):
    path = os.path.join(DATA, filename)
    if not os.path.exists(path):
        return []
    from PIL import Image as PILImage
    with PILImage.open(path) as im:
        pw, ph = im.size
    aspect = ph / pw
    w = min(max_w, max_h / aspect)
    ri = RLImage(path, width=w, height=w * aspect)
    ri.hAlign = "CENTER"
    return [ri, Spacer(1, 6)]


def hr():
    return HRFlowable(width="100%", thickness=0.5,
                      color=colors.HexColor("#ddddee"), spaceAfter=6, spaceBefore=2)


# ── Parse README ──────────────────────────────────────────────────────────────
with open(README, encoding="utf-8") as f:
    lines = f.readlines()

story = []
in_code_block = False
code_lines = []
i = 0

while i < len(lines):
    line = lines[i].rstrip('\n')

    # fenced code block
    if line.strip().startswith('```'):
        if not in_code_block:
            in_code_block = True
            code_lines = []
        else:
            for cl in code_lines:
                story.append(Paragraph(cl.replace('&', '&amp;').replace('<', '&lt;'), code))
            story.append(Spacer(1, 4))
            in_code_block = False
        i += 1
        continue

    if in_code_block:
        code_lines.append(line)
        i += 1
        continue

    # blank line
    if not line.strip():
        i += 1
        continue

    # image line — embed the chart
    img_match = re.match(r'!\[.*?\]\(data/([^\)]+)\)', line.strip())
    if img_match:
        filename = img_match.group(1)
        block = embed_img(filename) + [hr()]
        story += block
        i += 1
        continue

    # ordinary paragraph (may contain bold, code, links)
    xml = md_to_rl(line)
    if xml:
        story.append(Paragraph(xml, body))
    i += 1

# ── Build ─────────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(OUTPUT, pagesize=A4,
      leftMargin=MARGIN, rightMargin=MARGIN,
      topMargin=MARGIN, bottomMargin=MARGIN)
doc.build(story)
print(f"Saved {OUTPUT}")
