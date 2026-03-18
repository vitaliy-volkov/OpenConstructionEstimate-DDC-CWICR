"""
Load the DDC CWICR Parquet dataset and display basic information.

Uses the 100-row sample by default. Pass --full to load the complete
English dataset (900,225 rows).
"""

import argparse
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    sys.exit("pandas is required. Install with: pip install pandas pyarrow")


SAMPLE_PATH = Path(__file__).resolve().parents[2] / "sample-data" / "sample_cwicr_en_100rows.parquet"
FULL_PATH = Path(__file__).resolve().parents[3] / "EN___DDC_CWICR" / "ENG_TORONTO_workitems_costs_resources_DDC_CWICR.parquet"


def main():
    parser = argparse.ArgumentParser(description="Load and explore DDC CWICR Parquet data.")
    parser.add_argument("--full", action="store_true", help="Load the full English dataset instead of the sample.")
    parser.add_argument("--path", type=str, default=None, help="Custom path to a Parquet file.")
    args = parser.parse_args()

    # Resolve file path
    if args.path:
        parquet_path = Path(args.path)
    elif args.full:
        parquet_path = FULL_PATH
    else:
        parquet_path = SAMPLE_PATH

    if not parquet_path.exists():
        sys.exit(f"File not found: {parquet_path}")

    print(f"Loading: {parquet_path}\n")
    df = pd.read_parquet(parquet_path)

    # Basic shape
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}\n")

    # Schema overview
    print("=== Column Names & Types ===")
    for col in df.columns:
        print(f"  {col:<50} {df[col].dtype}")
    print()

    # First 10 rows (selected columns for readability)
    display_cols = [
        "rate_code", "rate_original_name", "rate_unit",
        "total_cost_per_position", "department_name", "section_name",
    ]
    available = [c for c in display_cols if c in df.columns]
    print("=== First 10 Rows (key columns) ===")
    print(df[available].head(10).to_string(index=False))
    print()

    # Cost distribution
    if "total_cost_per_position" in df.columns:
        cost = df["total_cost_per_position"].dropna()
        print("=== total_cost_per_position Distribution ===")
        print(f"  Count:  {cost.count():,}")
        print(f"  Mean:   {cost.mean():,.2f} EUR")
        print(f"  Median: {cost.median():,.2f} EUR")
        print(f"  Min:    {cost.min():,.2f} EUR")
        print(f"  Max:    {cost.max():,.2f} EUR")
        print(f"  Std:    {cost.std():,.2f} EUR")
        print()

    # Department counts
    if "department_name" in df.columns:
        print("=== Rows per Department ===")
        dept_counts = df["department_name"].value_counts()
        for dept, count in dept_counts.items():
            print(f"  {dept:<50} {count:>8,}")
        print()

    print("Done.")


if __name__ == "__main__":
    main()
