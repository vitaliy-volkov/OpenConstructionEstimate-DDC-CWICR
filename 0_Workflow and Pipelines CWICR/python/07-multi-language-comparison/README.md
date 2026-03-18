# 07 - Multi-Language / Multi-Region Comparison

Compare construction costs across regions by loading multiple CWICR Parquet files and matching equivalent work items by `rate_code`.

## Scripts

| Script | Description |
|---|---|
| `compare_regions.py` | Load 2+ regional Parquet files, match work items by rate_code, compare costs, and generate a chart |

## How It Works

1. Loads CWICR Parquet files from multiple language/region folders (EN Toronto, DE Berlin, RU St. Petersburg, etc.).
2. Matches equivalent work items across regions using the `rate_code` column.
3. Compares `total_cost_per_position` and other cost columns across regions.
4. Outputs a comparison table and saves a matplotlib bar chart.

## Prerequisites

```bash
pip install pandas pyarrow matplotlib python-dotenv
```

## Usage

```bash
# Compare EN, DE, and RU datasets (default)
python compare_regions.py

# Specify custom parquet paths
python compare_regions.py \
    --files ../../data/EN___DDC_CWICR/ENG_TORONTO_workitems_costs_resources_DDC_CWICR.parquet \
           ../../data/DE___DDC_CWICR/DE_BERLIN_workitems_costs_resources_DDC_CWICR.parquet

# Filter to a specific department
python compare_regions.py --department "Concrete"

# Show top N most expensive items
python compare_regions.py --top 20
```
