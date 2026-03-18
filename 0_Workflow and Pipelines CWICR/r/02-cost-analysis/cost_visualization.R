#!/usr/bin/env Rscript
#
# 02 - Cost Analysis and Visualization (R)
#
# Generates ggplot2 visualizations of the DDC-CWICR construction cost dataset.
# Saves plots as PNG files in the current working directory.
#
# Usage:
#   Rscript cost_visualization.R [path_to_parquet]

library(arrow)
library(ggplot2)
library(dplyr)
library(scales)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

args <- commandArgs(trailingOnly = TRUE)
default_path <- file.path(
  dirname(dirname(dirname(normalizePath(sys.frame(1)$ofile, mustWork = FALSE)))),
  "sample-data", "sample_cwicr_en_100rows.parquet"
)
parquet_path <- if (length(args) >= 1) args[1] else default_path

cat("Loading Parquet file:", parquet_path, "\n\n")

df <- arrow::read_parquet(parquet_path)

# Ensure numeric columns are actually numeric
df <- df %>%
  mutate(
    total_cost = as.numeric(total_cost_per_position),
    material_cost = as.numeric(total_material_cost_per_position),
    labor_hours = as.numeric(labor_hours_construction_workers),
    resource_price = as.numeric(resource_price_per_unit_eur_current)
  )

# Common theme
theme_cwicr <- theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", size = 14),
    plot.subtitle = element_text(color = "grey40"),
    axis.text.x = element_text(angle = 45, hjust = 1)
  )

# ---------------------------------------------------------------------------
# Plot 1: Distribution of Total Costs
# ---------------------------------------------------------------------------

cat("Generating Plot 1: Cost distribution...\n")

p1 <- df %>%
  filter(!is.na(total_cost), total_cost > 0) %>%
  ggplot(aes(x = total_cost)) +
  geom_histogram(
    aes(y = after_stat(density)),
    bins = 30,
    fill = "#2196F3",
    color = "white",
    alpha = 0.7
  ) +
  geom_density(color = "#F44336", linewidth = 1) +
  scale_x_log10(labels = label_comma(prefix = "EUR ")) +
  labs(
    title = "Distribution of Total Cost per Position",
    subtitle = "DDC-CWICR Dataset (log scale)",
    x = "Total Cost (EUR, log scale)",
    y = "Density"
  ) +
  theme_cwicr

ggsave("01_cost_distribution.png", p1, width = 10, height = 6, dpi = 150)

# ---------------------------------------------------------------------------
# Plot 2: Cost by Department (Box Plot)
# ---------------------------------------------------------------------------

cat("Generating Plot 2: Cost by department...\n")

if ("department_name" %in% names(df)) {
  p2 <- df %>%
    filter(!is.na(total_cost), !is.na(department_name), total_cost > 0) %>%
    ggplot(aes(x = reorder(department_name, total_cost, FUN = median), y = total_cost)) +
    geom_boxplot(
      fill = "#4CAF50",
      color = "#2E7D32",
      alpha = 0.7,
      outlier.alpha = 0.3
    ) +
    scale_y_log10(labels = label_comma(prefix = "EUR ")) +
    coord_flip() +
    labs(
      title = "Total Cost per Position by Department",
      subtitle = "Box plots ordered by median cost (log scale)",
      x = NULL,
      y = "Total Cost (EUR, log scale)"
    ) +
    theme_cwicr +
    theme(axis.text.x = element_text(angle = 0, hjust = 0.5))

  ggsave("02_cost_by_department.png", p2, width = 10, height = 7, dpi = 150)
} else {
  cat("  Skipping: 'department_name' column not found.\n")
}

# ---------------------------------------------------------------------------
# Plot 3: Material Cost vs. Total Cost
# ---------------------------------------------------------------------------

cat("Generating Plot 3: Material vs total cost scatter...\n")

p3 <- df %>%
  filter(
    !is.na(total_cost), !is.na(material_cost),
    total_cost > 0, material_cost > 0
  ) %>%
  ggplot(aes(x = total_cost, y = material_cost)) +
  geom_point(
    aes(color = department_name),
    alpha = 0.6,
    size = 2
  ) +
  geom_abline(
    slope = 1, intercept = 0,
    linetype = "dashed", color = "grey50"
  ) +
  scale_x_log10(labels = label_comma(prefix = "EUR ")) +
  scale_y_log10(labels = label_comma(prefix = "EUR ")) +
  labs(
    title = "Material Cost vs. Total Cost per Position",
    subtitle = "Dashed line = material cost equals total cost",
    x = "Total Cost (EUR, log scale)",
    y = "Material Cost (EUR, log scale)",
    color = "Department"
  ) +
  theme_cwicr +
  theme(
    legend.position = "bottom",
    legend.title = element_text(face = "bold"),
    axis.text.x = element_text(angle = 0, hjust = 0.5)
  )

ggsave("03_material_vs_total_cost.png", p3, width = 10, height = 8, dpi = 150)

# ---------------------------------------------------------------------------
# Plot 4: Top 15 Sections by Average Cost
# ---------------------------------------------------------------------------

cat("Generating Plot 4: Top sections by average cost...\n")

if ("section_name" %in% names(df)) {
  top_sections <- df %>%
    filter(!is.na(total_cost), !is.na(section_name)) %>%
    group_by(section_name) %>%
    summarise(
      avg_cost = mean(total_cost, na.rm = TRUE),
      count = n(),
      .groups = "drop"
    ) %>%
    filter(count >= 2) %>%
    slice_max(avg_cost, n = 15)

  p4 <- top_sections %>%
    ggplot(aes(x = reorder(section_name, avg_cost), y = avg_cost)) +
    geom_col(fill = "#FF9800", alpha = 0.8) +
    geom_text(
      aes(label = sprintf("EUR %.0f (n=%d)", avg_cost, count)),
      hjust = -0.1,
      size = 3
    ) +
    coord_flip() +
    scale_y_continuous(
      labels = label_comma(prefix = "EUR "),
      expand = expansion(mult = c(0, 0.3))
    ) +
    labs(
      title = "Top 15 Sections by Average Cost per Position",
      subtitle = "Minimum 2 records per section",
      x = NULL,
      y = "Average Cost (EUR)"
    ) +
    theme_cwicr +
    theme(axis.text.x = element_text(angle = 0, hjust = 0.5))

  ggsave("04_top_sections_by_cost.png", p4, width = 12, height = 7, dpi = 150)
} else {
  cat("  Skipping: 'section_name' column not found.\n")
}

cat("\nAll plots saved. Done.\n")
