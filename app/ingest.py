import sys
from pathlib import Path

from app.loader import extract_text
from app.parser import parse_menu

if __name__ == "__main__":
    pdf_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/parsed_menu.json")

    text = extract_text(pdf_path.read_bytes())
    menu, warnings = parse_menu(text)
    out_path.write_text(menu.model_dump_json(indent=2), encoding="utf-8")

    print(f"{len(menu.dishes)} dishes parsed -> {out_path}")
    for w in warnings:
        print("WARNING:", w)