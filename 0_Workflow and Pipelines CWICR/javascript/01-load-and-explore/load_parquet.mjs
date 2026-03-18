/**
 * 01 - Load and Explore CWICR Parquet Data
 *
 * Demonstrates how to read the CWICR construction cost dataset from a Parquet
 * file using parquet-wasm and apache-arrow in Node.js.
 *
 * Usage:
 *   node load_parquet.mjs [path_to_parquet]
 */

import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { tableFromIPC } from "apache-arrow";
import { readParquet } from "parquet-wasm/node/arrow1.js";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const __dirname = dirname(fileURLToPath(import.meta.url));
const defaultParquetPath = resolve(
  __dirname,
  "../../sample-data/sample_cwicr_en_100rows.parquet"
);
const parquetPath = process.argv[2] || defaultParquetPath;

// ---------------------------------------------------------------------------
// Load the Parquet file
// ---------------------------------------------------------------------------

console.log(`\nLoading Parquet file: ${parquetPath}\n`);

const parquetBytes = readFileSync(parquetPath);
const arrowIPCBytes = readParquet(new Uint8Array(parquetBytes));
const table = tableFromIPC(arrowIPCBytes);

// ---------------------------------------------------------------------------
// 1. Display the schema
// ---------------------------------------------------------------------------

console.log("=== Schema ===");
console.log(`Total columns: ${table.schema.fields.length}\n`);

for (const field of table.schema.fields) {
  console.log(`  ${field.name.padEnd(50)} ${field.type}`);
}

console.log(`\nTotal rows: ${table.numRows}\n`);

// ---------------------------------------------------------------------------
// 2. Preview the first 10 rows
// ---------------------------------------------------------------------------

console.log("=== First 10 Rows (selected columns) ===\n");

const previewColumns = [
  "rate_code",
  "rate_original_name",
  "rate_unit",
  "department_name",
  "total_cost_per_position",
];

// Build a simple table view
const rows = [];
for (let i = 0; i < Math.min(10, table.numRows); i++) {
  const row = {};
  for (const col of previewColumns) {
    const column = table.getChild(col);
    row[col] = column ? column.get(i) : "N/A";
  }
  rows.push(row);
}

console.table(rows);

// ---------------------------------------------------------------------------
// 3. Basic statistics for cost columns
// ---------------------------------------------------------------------------

console.log("\n=== Basic Statistics ===\n");

const costColumns = [
  "total_cost_per_position",
  "total_material_cost_per_position",
  "resource_price_per_unit_eur_current",
  "labor_hours_construction_workers",
];

for (const colName of costColumns) {
  const column = table.getChild(colName);
  if (!column) {
    console.log(`  Column '${colName}' not found — skipping.`);
    continue;
  }

  const values = [];
  for (let i = 0; i < column.length; i++) {
    const v = column.get(i);
    if (v !== null && v !== undefined && !Number.isNaN(Number(v))) {
      values.push(Number(v));
    }
  }

  if (values.length === 0) {
    console.log(`  ${colName}: no numeric values`);
    continue;
  }

  values.sort((a, b) => a - b);

  const count = values.length;
  const sum = values.reduce((a, b) => a + b, 0);
  const mean = sum / count;
  const min = values[0];
  const max = values[count - 1];
  const median =
    count % 2 === 0
      ? (values[count / 2 - 1] + values[count / 2]) / 2
      : values[Math.floor(count / 2)];

  console.log(`  ${colName}`);
  console.log(`    count  : ${count}`);
  console.log(`    min    : ${min.toFixed(2)}`);
  console.log(`    max    : ${max.toFixed(2)}`);
  console.log(`    mean   : ${mean.toFixed(2)}`);
  console.log(`    median : ${median.toFixed(2)}`);
  console.log();
}

console.log("Done.");
