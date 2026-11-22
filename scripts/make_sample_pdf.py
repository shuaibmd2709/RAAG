import json
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

CODES = {"vegan": "VG", "vegetarian": "V", "gluten-free": "GF"}

menu = json.loads(Path("data/sample_menu.json").read_text(encoding="utf-8"))
c = canvas.Canvas("data/sample_menu.pdf", pagesize=A4)
W, H = A4
y = H - 60


def line(text, size=10, gap=14, bold=False):
    global y
    if y < 60:
        c.showPage(); y = H - 60
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawString(50, y, text)
    y -= gap


line(menu["restaurant"], 20, 26, True)
line("VG = vegan, V = vegetarian, GF = gluten-free. Please ask staff about any allergy.", 9, 22)

current = None
for d in menu["dishes"]:
    if d["category"] != current:
        current = d["category"]
        y -= 6
        line(current.upper(), 13, 20, True)
    tags = ", ".join(CODES[t] for t in d["dietary_tags"] if t in CODES)
    line(f'{d["name"]}   EUR {d["price_eur"]:.2f}', 11, 14, True)
    extra = f" ({tags})" if tags else ""
    line(d["description"] + extra, 10, 13)
    if d["allergens_stated"]:
        line("Allergens: " + (", ".join(d["allergens"]) or "none"), 9, 18)
    else:
        y -= 5
c.save()
print("wrote data/sample_menu.pdf")