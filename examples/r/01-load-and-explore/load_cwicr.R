#!/usr/bin/env Rscript
#
# 01 - Load and Explore CWICR Parquet Data (R)
#
# Reads the CWICR construction cost dataset from a Parquet file using the
# arrow package, displays the schema, summary statistics, and previews
# the first rows.
#
# Usage:
#   Rscript load_cwicr.R [path_to_parquet]

library(arrow)
library(dplyr)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

args <- commandArgs(trailingOnly = TRUE)
default_path <- file.path(
  dirname(dirname(dirname(normalizePath(sys.frame(1)$ofile, mustWork = FALSE)))),
  "sample-data", "sample_cwicr_en_100rows.parquet"
)
parquet_path <- if (length(args) >= 1) args[1] else default_path

cat("\nLoading Parquet file:", parquet_path, "\n\n")

# ---------------------------------------------------------------------------
# Load the data
# ---------------------------------------------------------------------------

df <- arrow::read_parquet(parquet_path)

# ---------------------------------------------------------------------------
# 1. Schema
# ---------------------------------------------------------------------------

cat("=== Schema ===\n")
cat("Total columns:", ncol(df), "\n")
cat("Total rows:", nrow(df), "\n\n")

schema_info <- data.frame(
  column = names(df),
  type = sapply(df, class),
  stringsAsFactors = FALSE
)
print(schema_info, right = FALSE, row.names = FALSE)
cat("\n")

# ---------------------------------------------------------------------------
# 2. Preview first 10 rows (selected columns)
# ---------------------------------------------------------------------------

cat("=== First 10 Rows (selected columns) ===\n\n")

preview_columns <- c(
  "rate_code",
  "rate_original_name",
  "rate_unit",
  "department_name",
  "total_cost_per_position"
)

# Only use columns that exist
available_cols <- intersect(preview_columns, names(df))
preview <- head(df[, available_cols, drop = FALSE], 10)
print(as.data.frame(preview), right = FALSE, row.names = FALSE)
cat("\n")

# ---------------------------------------------------------------------------
# 3. Summary statistics for cost columns
# ---------------------------------------------------------------------------

cat("=== Summary Statistics ===\n\n")

cost_columns <- c(
  "total_cost_per_position",
  "total_material_cost_per_position",
  "resource_price_per_unit_eur_current",
  "labor_hours_construction_workers"
)

for (col_name in cost_columns) {
  if (!(col_name %in% names(df))) {
    cat(sprintf("  Column '%s' not found -- skipping.\n\n", col_name))
    next
  }

  values <- as.numeric(df[[col_name]])
  values <- values[!is.na(values)]

  if (length(values) == 0) {
    cat(sprintf("  %s: no numeric values\n\n", col_name))
    next
  }

  cat(sprintf("  %s\n", col_name))
  cat(sprintf("    count  : %d\n", length(values)))
  cat(sprintf("    min    : %.2f\n", min(values)))
  cat(sprintf("    max    : %.2f\n", max(values)))
  cat(sprintf("    mean   : %.2f\n", mean(values)))
  cat(sprintf("    median : %.2f\n", median(values)))
  cat(sprintf("    sd     : %.2f\n", sd(values)))
  cat("\n")
}

# ---------------------------------------------------------------------------
# 4. Department breakdown
# ---------------------------------------------------------------------------

cat("=== Records per Department ===\n\n")

if ("department_name" %in% names(df)) {
  dept_counts <- df %>%
    group_by(department_name) %>%
    summarise(
      count = n(),
      avg_cost = mean(as.numeric(total_cost_per_position), na.rm = TRUE),
      .groups = "drop"
    ) %>%
    arrange(desc(count))

  print(as.data.frame(dept_counts), right = FALSE, row.names = FALSE)
} else {
  cat("  Column 'department_name' not found.\n")
}

cat("\n\nDone.\n")
