"""
Print all columns with data types, value ranges for numeric columns,
and null counts for the DDC CWICR dataset.
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
    parser = argparse.ArgumentParser(description="Explore DDC CWICR Parquet schema in detail.")
    parser.add_argument("--full", action="store_true", help="Use full dataset.")
    parser.add_argument("--path", type=str, default=None, help="Custom Parquet path.")
    args = parser.parse_args()

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

    total_rows = len(df)
    print(f"Total rows: {total_rows:,}")
    print(f"Total columns: {len(df.columns)}\n")

    # Detailed column report
    print(f"{'#':<4} {'Column':<50} {'Type':<15} {'Nulls':<10} {'Null%':<8} {'Range / Sample Values'}")
    print("-" * 140)

    for i, col in enumerate(df.columns, 1):
        dtype = str(df[col].dtype)
        null_count = df[col].isna().sum()
        null_pct = f"{null_count / total_rows * 100:.1f}%"

        # Value range or sample
        if pd.api.types.is_numeric_dtype(df[col]):
            non_null = df[col].dropna()
            if len(non_null) > 0:
                range_str = f"min={non_null.min():.4g}, max={non_null.max():.4g}, mean={non_null.mean():.4g}"
            else:
                range_str = "(all null)"
        elif pd.api.types.is_bool_dtype(df[col]):
            true_count = df[col].sum()
            range_str = f"True={true_count}, False={total_rows - null_count - true_count}"
        else:
            unique = df[col].nunique()
            samples = df[col].dropna().unique()[:3]
            sample_str = ", ".join(str(s)[:30] for s in samples)
            range_str = f"unique={unique} | {sample_str}"

        print(f"{i:<4} {col:<50} {dtype:<15} {null_count:<10} {null_pct:<8} {range_str}")

    # Summary
    print(f"\n=== Null Summary ===")
    all_nulls = df.isna().sum()
    cols_with_nulls = (all_nulls > 0).sum()
    cols_no_nulls = (all_nulls == 0).sum()
    print(f"  Columns with nulls:    {cols_with_nulls}")
    print(f"  Columns without nulls: {cols_no_nulls}")

    mostly_null = all_nulls[all_nulls > total_rows * 0.5]
    if len(mostly_null) > 0:
        print(f"\n  Columns that are >50% null:")
        for col, cnt in mostly_null.sort_values(ascending=False).items():
            print(f"    {col:<50} {cnt:>8,} ({cnt/total_rows*100:.1f}%)")

    print("\nDone.")


if __name__ == "__main__":
    main()
