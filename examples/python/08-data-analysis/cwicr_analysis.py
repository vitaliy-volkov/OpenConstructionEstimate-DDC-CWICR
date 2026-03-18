"""
CWICR Data Analysis

Exploratory data analysis of the CWICR Parquet dataset. Produces charts for:
  - Cost distributions by department
  - Labour vs material cost ratios
  - Top most expensive work items
  - Resource utilisation patterns
  - Labour hours distribution

All charts are saved as PNG files.
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent
DEFAULT_PARQUET = (
    REPO_ROOT / "EN___DDC_CWICR" / "ENG_TORONTO_workitems_costs_resources_DDC_CWICR.parquet"
)
DEFAULT_OUTDIR = SCRIPT_DIR / "charts"


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def dataset_overview(df: pd.DataFrame):
    """Print basic dataset statistics."""
    print(f"  Shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
    print(f"  Columns: {', '.join(df.columns[:20])}{'...' if len(df.columns) > 20 else ''}")
    print(f"  Memory usage: {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")

    if "department_name" in df.columns:
        n_dept = df["department_name"].nunique()
        print(f"  Unique departments: {n_dept}")
    if "rate_code" in df.columns:
        n_rates = df["rate_code"].nunique()
        print(f"  Unique rate codes: {n_rates}")
    if "resource_name" in df.columns:
        n_res = df["resource_name"].nunique()
        print(f"  Unique resources: {n_res}")
    print()


def chart_cost_distribution_by_department(df: pd.DataFrame, outdir: Path):
    """Box plot of total_cost_per_position by department."""
    col = "total_cost_per_position"
    if col not in df.columns or "department_name" not in df.columns:
        print(f"  Skipping: missing '{col}' or 'department_name'")
        return

    # Keep departments with enough data points
    dept_counts = df.groupby("department_name")[col].count()
    top_depts = dept_counts.nlargest(15).index.tolist()
    subset = df[df["department_name"].isin(top_depts) & df[col].notna()].copy()

    if subset.empty:
        print("  Skipping: no data after filtering.")
        return

    fig, ax = plt.subplots(figsize=(14, 8))
    dept_order = (
        subset.groupby("department_name")[col]
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )
    data_groups = [
        subset[subset["department_name"] == d][col].dropna().values
        for d in dept_order
    ]
    bp = ax.boxplot(data_groups, vert=False, patch_artist=True, showfliers=False)
    for patch in bp["boxes"]:
        patch.set_facecolor("#4C72B0")
        patch.set_alpha(0.7)

    ax.set_yticklabels([d[:35] for d in dept_order], fontsize=8)
    ax.set_xlabel("Total Cost per Position (EUR)")
    ax.set_title("Cost Distribution by Department (Top 15)")
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    plt.tight_layout()
    path = outdir / "cost_distribution_by_department.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


def chart_labor_vs_material(df: pd.DataFrame, outdir: Path):
    """Scatter plot: material cost vs resource (labour) cost per position."""
    mat_col = "total_material_cost_per_position"
    res_col = "total_resource_cost_per_position"
    if mat_col not in df.columns or res_col not in df.columns:
        print(f"  Skipping: missing '{mat_col}' or '{res_col}'")
        return

    subset = df[[mat_col, res_col, "department_name"]].dropna().copy()
    # Sample if too large
    if len(subset) > 5000:
        subset = subset.sample(5000, random_state=42)

    fig, ax = plt.subplots(figsize=(10, 8))
    departments = subset["department_name"].unique()
    cmap = plt.cm.get_cmap("tab20", min(len(departments), 20))
    dept_to_color = {d: cmap(i % 20) for i, d in enumerate(departments)}

    for dept in departments[:20]:
        mask = subset["department_name"] == dept
        ax.scatter(
            subset.loc[mask, mat_col],
            subset.loc[mask, res_col],
            label=dept[:25],
            alpha=0.5,
            s=15,
            color=dept_to_color[dept],
        )

    ax.set_xlabel("Material Cost per Position (EUR)")
    ax.set_ylabel("Resource (Labour) Cost per Position (EUR)")
    ax.set_title("Material vs Labour Cost")
    ax.legend(fontsize=6, loc="upper left", ncol=2)
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    plt.tight_layout()
    path = outdir / "labor_vs_material_ratio.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


def chart_top_expensive_items(df: pd.DataFrame, outdir: Path, top_n: int = 25):
    """Horizontal bar chart of the most expensive work items."""
    col = "total_cost_per_position"
    name_col = "rate_final_name"
    if col not in df.columns:
        print(f"  Skipping: missing '{col}'")
        return
    if name_col not in df.columns:
        name_col = "rate_original_name"
        if name_col not in df.columns:
            print("  Skipping: no name column found")
            return

    # Deduplicate by rate_code, keep max cost
    if "rate_code" in df.columns:
        agg = (
            df.dropna(subset=[col])
            .groupby("rate_code")
            .agg({col: "max", name_col: "first"})
            .reset_index()
        )
    else:
        agg = df.dropna(subset=[col])[[col, name_col]].copy()

    top = agg.nlargest(top_n, col)

    fig, ax = plt.subplots(figsize=(12, max(6, top_n * 0.35)))
    labels = top[name_col].str[:50]
    ax.barh(range(len(top)), top[col].values, color="#4C72B0", alpha=0.85)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(labels, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("Total Cost per Position (EUR)")
    ax.set_title(f"Top {top_n} Most Expensive Work Items")
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    plt.tight_layout()
    path = outdir / "top_expensive_items.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


def chart_resource_utilization(df: pd.DataFrame, outdir: Path, top_n: int = 20):
    """Bar chart showing how frequently each resource is used."""
    if "resource_name" not in df.columns:
        print("  Skipping: missing 'resource_name'")
        return

    resource_stats = (
        df[df["resource_name"].notna()]
        .groupby("resource_name")
        .agg(
            usage_count=("resource_name", "count"),
            avg_quantity=("resource_quantity", "mean"),
            avg_price=("resource_price_per_unit_eur_current", "mean"),
        )
        .sort_values("usage_count", ascending=False)
        .head(top_n)
    )

    fig, ax1 = plt.subplots(figsize=(12, max(6, top_n * 0.35)))
    labels = [n[:45] for n in resource_stats.index]
    y = range(len(resource_stats))

    ax1.barh(y, resource_stats["usage_count"], color="#4C72B0", alpha=0.8)
    ax1.set_yticks(list(y))
    ax1.set_yticklabels(labels, fontsize=7)
    ax1.invert_yaxis()
    ax1.set_xlabel("Usage Count (number of work items)")
    ax1.set_title(f"Top {top_n} Most Used Resources")
    plt.tight_layout()
    path = outdir / "resource_utilization.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


def chart_labor_hours_distribution(df: pd.DataFrame, outdir: Path):
    """Histogram of labour hours for construction workers."""
    col = "labor_hours_construction_workers"
    if col not in df.columns:
        print(f"  Skipping: missing '{col}'")
        return

    values = df[col].dropna()
    values = values[values > 0]
    if values.empty:
        print("  Skipping: no positive labour hours.")
        return

    # Clip outliers for better visualisation
    upper = values.quantile(0.95)
    clipped = values[values <= upper]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(clipped, bins=50, color="#4C72B0", alpha=0.8, edgecolor="white")
    ax.set_xlabel("Labour Hours (construction workers)")
    ax.set_ylabel("Frequency")
    ax.set_title(f"Distribution of Labour Hours (clipped at 95th percentile = {upper:.1f}h)")
    plt.tight_layout()
    path = outdir / "labor_hours_distribution.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Exploratory data analysis of CWICR construction cost data.",
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        default=str(DEFAULT_PARQUET),
        help="Path to the CWICR Parquet file.",
    )
    parser.add_argument(
        "--outdir", "-o",
        type=str,
        default=str(DEFAULT_OUTDIR),
        help="Output directory for charts.",
    )
    parser.add_argument(
        "--top", "-t",
        type=int,
        default=25,
        help="Number of top items for bar charts (default: 25).",
    )
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # --- Load ---
    print(f"\n{'='*60}")
    print("CWICR Data Analysis")
    print(f"{'='*60}\n")
    print(f"Loading: {args.file}")
    parquet_path = Path(args.file)
    if not parquet_path.exists():
        print(f"ERROR: File not found: {parquet_path}")
        sys.exit(1)

    df = pd.read_parquet(parquet_path)

    print("\n--- Dataset Overview ---\n")
    dataset_overview(df)

    # --- Charts ---
    print("--- Generating Charts ---\n")

    print("[1/5] Cost distribution by department")
    chart_cost_distribution_by_department(df, outdir)

    print("[2/5] Labour vs material cost")
    chart_labor_vs_material(df, outdir)

    print("[3/5] Top expensive items")
    chart_top_expensive_items(df, outdir, top_n=args.top)

    print("[4/5] Resource utilisation")
    chart_resource_utilization(df, outdir, top_n=args.top)

    print("[5/5] Labour hours distribution")
    chart_labor_hours_distribution(df, outdir)

    print(f"\nAll charts saved to: {outdir}")
    print("Done.\n")


if __name__ == "__main__":
    main()
