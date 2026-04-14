#!/usr/bin/env python3
"""Quick extractor for Russian contractor price-list PDFs -> CSV.

Heuristic parser:
- expects plain text from `pdftotext -layout`
- picks lines ending with `<unit> <price>`
- keeps source file and line for audit
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

UNIT_RE = r"(?:м2|м²|м3|м³|м\.п\.|п\.м\.|шт\.|компл\.|компл|дм3|дм³|чел\s*/\s*час|чел\./\s*смена|модуль|группа|комплекс|компл\.|м\.)"
PRICE_RE = r"\d{1,3}(?:[\s\u00A0]\d{3})*(?:[\.,]\d+)?"
LINE_RE = re.compile(rf"^(?P<name>.+?)\s+(?P<unit>{UNIT_RE})\s+(?P<price>{PRICE_RE})\s*$", re.IGNORECASE)


def norm_price(raw: str) -> str:
    raw = raw.replace("\u00A0", " ").replace(" ", "").replace(",", ".")
    return raw


def extract_rows(txt_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, line in enumerate(txt_path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        s = " ".join(line.strip().split())
        if not s:
            continue
        m = LINE_RE.match(s)
        if not m:
            continue
        name = m.group("name").strip(" -–—")
        if len(name) < 6:
            continue
        rows.append(
            {
                "source_file": txt_path.name,
                "source_line": str(idx),
                "name": name,
                "unit": m.group("unit").strip(),
                "price_rub": norm_price(m.group("price")),
                "currency": "RUB",
            }
        )
    return rows


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: extract_price_list_from_pdf.py <output.csv> <input1.txt> [input2.txt ...]")
        return 2

    out = Path(sys.argv[1])
    inputs = [Path(p) for p in sys.argv[2:]]

    all_rows: list[dict[str, str]] = []
    for p in inputs:
        all_rows.extend(extract_rows(p))

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["source_file", "source_line", "name", "unit", "price_rub", "currency"],
        )
        w.writeheader()
        w.writerows(all_rows)

    print(f"written {len(all_rows)} rows -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
