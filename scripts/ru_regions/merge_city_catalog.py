#!/usr/bin/env python3
"""Merge regional RU price list into DDC CWICR city catalog.

Usage:
  python3 scripts/ru_regions/merge_city_catalog.py \
    --base RU___DDC_CWICR/DDC_CWICR_RU_STPETERSBURG_Catalog.csv \
    --overrides RU___DDC_CWICR/intake/price_list_template_ru.csv \
    --city RU_MOSCOW \
    --out RU___DDC_CWICR/DDC_CWICR_RU_MOSCOW_Catalog.csv \
    --report RU___DDC_CWICR/intake/report_RU_MOSCOW.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


def _norm_text(v: str | None) -> str:
    return (v or "").strip().lower()


def _to_float(v: str | None, default: float = 0.0) -> float:
    if v is None:
        return default
    s = str(v).strip().replace(" ", "").replace(",", ".")
    if not s:
        return default
    try:
        return float(s)
    except ValueError:
        return default


def _pick_price(row: dict[str, Any]) -> tuple[float, float, float, float]:
    pmin = _to_float(row.get("price_min"))
    pmax = _to_float(row.get("price_max"))
    pavg = _to_float(row.get("price_avg"))
    pmed = _to_float(row.get("price_median"))

    if pavg <= 0 and pmed > 0:
        pavg = pmed
    if pmed <= 0 and pavg > 0:
        pmed = pavg

    if pmin <= 0 and pavg > 0:
        pmin = pavg
    if pmax <= 0 and pavg > 0:
        pmax = pavg

    return pmin, pmax, pavg, pmed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--overrides", required=True)
    parser.add_argument("--city", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    base_path = Path(args.base)
    overrides_path = Path(args.overrides)
    out_path = Path(args.out)
    report_path = Path(args.report)

    with base_path.open("r", encoding="utf-8", newline="") as f:
        base_rows = list(csv.DictReader(f))

    with overrides_path.open("r", encoding="utf-8", newline="") as f:
        incoming = list(csv.DictReader(f))

    by_code: dict[str, dict[str, Any]] = {}
    by_name_unit: dict[tuple[str, str], dict[str, Any]] = {}

    for row in incoming:
        code = _norm_text(row.get("resource_code"))
        key_nu = (_norm_text(row.get("name")), _norm_text(row.get("unit")))
        if code:
            by_code[code] = row
        if key_nu[0] and key_nu[1]:
            by_name_unit[key_nu] = row

    report_rows: list[dict[str, Any]] = []
    updates = 0

    for row in base_rows:
        match = None

        code = _norm_text(row.get("resource_code"))
        if code and code in by_code:
            match = by_code[code]
            match_key = "resource_code"
        else:
            nu = (_norm_text(row.get("name")), _norm_text(row.get("unit")))
            if nu in by_name_unit:
                match = by_name_unit[nu]
                match_key = "name+unit"
            else:
                match_key = "none"

        if match:
            pmin, pmax, pavg, pmed = _pick_price(match)
            if pavg > 0 or pmed > 0:
                row["price_min"] = f"{pmin:.2f}" if pmin > 0 else row.get("price_min", "")
                row["price_max"] = f"{pmax:.2f}" if pmax > 0 else row.get("price_max", "")
                row["price_avg"] = f"{pavg:.2f}" if pavg > 0 else row.get("price_avg", "")
                row["price_median"] = f"{pmed:.2f}" if pmed > 0 else row.get("price_median", "")
                row["currency"] = (match.get("currency") or row.get("currency") or "RUB").strip() or "RUB"
                updates += 1

        report_rows.append(
            {
                "resource_code": row.get("resource_code", ""),
                "name": row.get("name", ""),
                "unit": row.get("unit", ""),
                "match_key": match_key,
                "updated": "yes" if match and match_key != "none" else "no",
            }
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(base_rows[0].keys()))
        writer.writeheader()
        writer.writerows(base_rows)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["resource_code", "name", "unit", "match_key", "updated"])
        writer.writeheader()
        writer.writerows(report_rows)

    print(f"Done. City={args.city} updated_rows={updates} total_rows={len(base_rows)}")
    print(f"Catalog: {out_path}")
    print(f"Report:  {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
