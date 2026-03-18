/**
 * 04 - Cost Estimation from Text Description
 *
 * Decomposes a free-text construction task into individual work items using
 * OpenAI, searches the DDC-CWICR Qdrant database for matching cost rates,
 * and produces a structured cost estimate.
 *
 * Usage:
 *   export OPENAI_API_KEY="sk-..."
 *   node estimate_from_text.mjs
 */

import { QdrantClient } from "@qdrant/js-client-rest";
import OpenAI from "openai";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const QDRANT_URL = process.env.QDRANT_URL || "http://localhost:6333";
const QDRANT_API_KEY = process.env.QDRANT_API_KEY || undefined;
const COLLECTION = "ddc_en_toronto";
const EMBEDDING_MODEL = "text-embedding-3-large";
const EMBEDDING_DIMS = 3072;
const TOP_K = 3;

const TASK_DESCRIPTION = `
Build a reinforced concrete foundation for a two-story residential house.
The foundation is 12 m x 10 m, 0.4 m thick, with steel rebar reinforcement.
Include formwork, concrete pouring, and waterproofing membrane.
`;

// ---------------------------------------------------------------------------
// Initialize clients
// ---------------------------------------------------------------------------

const openai = new OpenAI();

const qdrant = new QdrantClient({
  url: QDRANT_URL,
  ...(QDRANT_API_KEY && { apiKey: QDRANT_API_KEY }),
});

// ---------------------------------------------------------------------------
// Step 1 — Decompose the task into searchable work items
// ---------------------------------------------------------------------------

async function decomposeTask(description) {
  console.log("Step 1: Decomposing task into work items...\n");

  const response = await openai.chat.completions.create({
    model: "gpt-4o",
    temperature: 0,
    messages: [
      {
        role: "system",
        content: `You are a construction cost estimator. Given a construction task
description, decompose it into individual work items that can be searched in a
construction cost database. Return a JSON array of objects with:
- "item": short description of the work item (suitable for semantic search)
- "quantity": estimated quantity (number)
- "unit": unit of measurement (e.g., m2, m3, kg, pcs, lm)

Return ONLY valid JSON, no markdown fences.`,
      },
      {
        role: "user",
        content: description.trim(),
      },
    ],
  });

  const items = JSON.parse(response.choices[0].message.content);
  console.log(`  Identified ${items.length} work items:\n`);
  for (const item of items) {
    console.log(`    - ${item.item} (${item.quantity} ${item.unit})`);
  }
  console.log();
  return items;
}

// ---------------------------------------------------------------------------
// Step 2 — Search Qdrant for each work item
// ---------------------------------------------------------------------------

async function searchWorkItem(item) {
  const embResponse = await openai.embeddings.create({
    model: EMBEDDING_MODEL,
    input: item.item,
    dimensions: EMBEDDING_DIMS,
  });
  const vector = embResponse.data[0].embedding;

  const results = await qdrant.search(COLLECTION, {
    vector,
    limit: TOP_K,
    with_payload: true,
  });

  return results;
}

// ---------------------------------------------------------------------------
// Step 3 — Build the estimate
// ---------------------------------------------------------------------------

async function buildEstimate(workItems) {
  console.log("Step 2: Searching database for matching cost rates...\n");
  console.log("Step 3: Building cost estimate...\n");

  const estimate = [];
  let grandTotal = 0;

  for (const item of workItems) {
    const results = await searchWorkItem(item);

    // Use the best match (highest score)
    const best = results[0];
    if (!best) {
      estimate.push({
        workItem: item.item,
        quantity: item.quantity,
        unit: item.unit,
        match: "No match found",
        unitCost: 0,
        totalCost: 0,
        score: 0,
      });
      continue;
    }

    const payload = best.payload || {};
    const unitCost = Number(payload.total_cost_per_position) || 0;
    const materialCost = Number(payload.total_material_cost_per_position) || 0;
    const totalCost = unitCost * item.quantity;
    grandTotal += totalCost;

    estimate.push({
      workItem: item.item,
      quantity: item.quantity,
      unit: item.unit,
      matchedRate: payload.rate_final_name || payload.rate_original_name || "N/A",
      rateCode: payload.rate_code || "N/A",
      rateUnit: payload.rate_unit || "N/A",
      unitCost,
      materialCost,
      totalCost,
      score: best.score,
    });
  }

  return { lineItems: estimate, grandTotal };
}

// ---------------------------------------------------------------------------
// Display
// ---------------------------------------------------------------------------

function displayEstimate(result) {
  console.log("=".repeat(80));
  console.log("  CONSTRUCTION COST ESTIMATE");
  console.log("=".repeat(80));
  console.log();

  for (const [i, line] of result.lineItems.entries()) {
    console.log(`  ${i + 1}. ${line.workItem}`);
    console.log(`     Matched Rate : ${line.matchedRate || "N/A"} [${line.rateCode}]`);
    console.log(`     Match Score  : ${(line.score || 0).toFixed(4)}`);
    console.log(`     Quantity     : ${line.quantity} ${line.unit}`);
    console.log(`     Unit Cost    : EUR ${line.unitCost.toFixed(2)} / ${line.rateUnit}`);
    console.log(`     Line Total   : EUR ${line.totalCost.toFixed(2)}`);
    console.log();
  }

  console.log("-".repeat(80));
  console.log(`  GRAND TOTAL: EUR ${result.grandTotal.toFixed(2)}`);
  console.log("-".repeat(80));
  console.log();
  console.log(
    "  Note: This is an indicative estimate based on the closest matching"
  );
  console.log(
    "  rates in the DDC-CWICR database. Actual costs may vary."
  );
  console.log();
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  console.log("\nTask Description:");
  console.log(`  ${TASK_DESCRIPTION.trim()}\n`);

  const workItems = await decomposeTask(TASK_DESCRIPTION);
  const estimate = await buildEstimate(workItems);
  displayEstimate(estimate);
}

main().catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});
