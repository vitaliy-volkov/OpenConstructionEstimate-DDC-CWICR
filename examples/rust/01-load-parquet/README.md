# 01 - Load Parquet (Rust)

## Description

Read the CWICR construction cost dataset from a Parquet file using the
`parquet` and `arrow` crates. Prints the schema, the first 10 rows of selected
columns, and basic statistics for cost columns.

## Prerequisites

- Rust toolchain (1.75+)
- Sample Parquet file at `examples/sample-data/sample_cwicr_en_100rows.parquet`

## Usage

```bash
# From the examples/rust directory:
cargo run -p load-parquet -- ../../sample-data/sample_cwicr_en_100rows.parquet

# Or without an argument (uses the default relative path):
cargo run -p load-parquet
```
