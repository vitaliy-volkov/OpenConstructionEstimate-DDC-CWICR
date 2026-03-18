# 01 - Load and Explore DDC CWICR Data

Load the DDC CWICR Parquet dataset and explore its schema, structure, and basic statistics.

## Scripts

- **load_parquet.py** - Load the dataset, display schema, first rows, and cost/department statistics.
- **explore_schema.py** - Print all 84 columns with data types, value ranges, and null counts.

## Prerequisites

- Python 3.9+
- `pip install -r ../requirements.txt`

No API keys or external services required.

## Usage

```bash
# Load sample data (100 rows)
python load_parquet.py

# Load full English dataset
python load_parquet.py --full

# Explore schema
python explore_schema.py
python explore_schema.py --full
```
