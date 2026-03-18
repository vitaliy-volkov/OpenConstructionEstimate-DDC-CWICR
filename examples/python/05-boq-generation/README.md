# 05 - Bill of Quantities (BOQ) Generation

Read a list of work items from a CSV file, look up each in the DDC CWICR
database via Qdrant, and generate a priced Bill of Quantities exported to Excel.

## Scripts

- **generate_boq.py** - Main BOQ generation script.
- **sample_input.csv** - Example input CSV with construction work items.

## Prerequisites

- Python 3.9+
- `pip install -r ../requirements.txt`
- Qdrant running locally with indexed DDC data
- OpenAI API key in `.env`:
  ```
  OPENAI_API_KEY=sk-...
  ```

## Usage

```bash
# Using the provided sample input
python generate_boq.py sample_input.csv

# Custom input with output path
python generate_boq.py my_items.csv --output my_boq.xlsx

# Use a different collection
python generate_boq.py sample_input.csv --collection ddc_de_berlin
```

## Input CSV Format

```csv
description,quantity,unit
concrete foundation slab,120,m²
brick wall construction,85,m²
```
