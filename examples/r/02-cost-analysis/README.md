# 02 - Cost Analysis and Visualization (R)

## Description

Visualize the DDC-CWICR construction cost dataset using ggplot2. Produces:
1. Distribution of total costs (histogram + density)
2. Cost comparison by department (box plot)
3. Material cost vs. total cost scatter plot
4. Top 15 sections by average cost (bar chart)

Plots are saved as PNG files in the working directory.

## Prerequisites

- R >= 4.1
- Required packages:
  ```r
  install.packages(c("arrow", "ggplot2", "dplyr", "scales", "tidyr"))
  ```
- Sample Parquet file at `examples/sample-data/sample_cwicr_en_100rows.parquet`

## Usage

```bash
Rscript cost_visualization.R
# or with a custom path:
Rscript cost_visualization.R /path/to/your/file.parquet
```

Output PNGs will be saved in the current working directory.
