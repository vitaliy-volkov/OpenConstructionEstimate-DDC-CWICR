# 01 - Load and Explore CWICR Data (R)

## Description

Load the CWICR construction cost dataset from a Parquet file using the
`arrow` R package, display the schema, summary statistics, and preview
the first rows.

## Prerequisites

- R >= 4.1
- Required packages:
  ```r
  install.packages(c("arrow", "dplyr", "tibble"))
  ```
- Sample Parquet file at `examples/sample-data/sample_cwicr_en_100rows.parquet`

## Usage

```bash
Rscript load_cwicr.R
# or with a custom path:
Rscript load_cwicr.R /path/to/your/file.parquet
```
