import sys, os
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

ACCENT = HexColor("#2e7d32")
DARK = HexColor("#1b1b1b")
GRAY = HexColor("#555555")

def render_markdown_pdf(md_text, title, out_path, page=letter):
    c = canvas.Canvas(out_path, pagesize=page)
    w, h = page
    y = h - 25*mm
    x0 = 20*mm
    maxw = w - 40*mm
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(ACCENT)
    c.drawString(x0, y, title[:60])
    y -= 10*mm
    c.setStrokeColor(ACCENT)
    c.setLineWidth(1.5)
    c.line(x0, y, x0 + 60*mm, y)
    y -= 8*mm
    for raw in md_text.splitlines():
        line = raw.rstrip()
        if not line.strip(): y -= 4*mm; continue
        if line.startswith("# "):
            c.setFont("Helvetica-Bold", 16); c.setFillColor(DARK)
            c.drawString(x0, y, line[2:]); y -= 7*mm
        elif line.startswith("## "):
            c.setFont("Helvetica-Bold", 13); c.setFillColor(ACCENT)
            c.drawString(x0, y, line[3:]); y -= 6*mm
        elif line.startswith("- "):
            c.setFont("Helvetica", 10.5); c.setFillColor(GRAY)
            c.drawString(x0+4*mm, y, "• " + line[2:]); y -= 4.5*mm
        else:
            c.setFont("Helvetica", 11); c.setFillColor(DARK)
            c.drawString(x0, y, line); y -= 5*mm
        if y < 20*mm: c.showPage(); y = h - 25*mm
    c.save()

if __name__ == "__main__":
    render_markdown_pdf(open(sys.argv[2], encoding="utf-8").read(), sys.argv[1], sys.argv[3])
