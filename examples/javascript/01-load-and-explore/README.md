# 01 - Load and Explore CWICR Parquet Data

## Description

Load the CWICR construction cost dataset from a Parquet file using `parquet-wasm`
and `apache-arrow`, then display the schema, preview the first 10 rows, and
compute basic statistics on cost columns.

## Prerequisites

- Node.js >= 18
- Install dependencies from the parent directory:
  ```bash
  cd examples/javascript
  npm install
  ```
- Sample Parquet file at `examples/sample-data/sample_cwicr_en_100rows.parquet`

## Usage

```bash
node load_parquet.mjs
# or from the parent directory:
npm run 01:load
```

The script will print:
1. Full schema (all 84 columns with types)
2. The first 10 rows as a formatted table
3. Basic statistics for `total_cost_per_position` and `total_material_cost_per_position`
