/**
 * 03 - Semantic Search with Qdrant Client
 *
 * Uses the official @qdrant/js-client-rest SDK together with the OpenAI
 * embeddings API to search the DDC-CWICR construction cost database.
 *
 * Usage:
 *   export OPENAI_API_KEY="sk-..."
 *   node basic_search.mjs
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
const TOP_K = 5;

const QUERIES = [
  "exterior wall insulation for office building",
  "plumbing installation copper pipes",
  "electrical wiring and panel installation",
];

// ---------------------------------------------------------------------------
// Initialize clients
// ---------------------------------------------------------------------------

const openai = new OpenAI(); // reads OPENAI_API_KEY from env

const qdrant = new QdrantClient({
  url: QDRANT_URL,
  ...(QDRANT_API_KEY && { apiKey: QDRANT_API_KEY }),
});

// ---------------------------------------------------------------------------
// Helper: embed a single text
// ---------------------------------------------------------------------------

async function embed(text) {
  const response = await openai.embeddings.create({
    model: EMBEDDING_MODEL,
    input: text,
    dimensions: EMBEDDING_DIMS,
  });
  return response.data[0].embedding;
}

// ---------------------------------------------------------------------------
// Helper: search Qdrant and display results
// ---------------------------------------------------------------------------

async function searchAndDisplay(query) {
  console.log(`\n=======================================`);
  console.log(`Query: "${query}"`);
  console.log(`=======================================\n`);

  // Embed the query
  const vector = await embed(query);

  // Search Qdrant
  const results = await qdrant.search(COLLECTION, {
    vector,
    limit: TOP_K,
    with_payload: true,
  });

  if (results.length === 0) {
    console.log("  No results found.\n");
    return;
  }

  for (const [i, hit] of results.entries()) {
    const p = hit.payload || {};
    console.log(`  #${i + 1}  Score: ${hit.score.toFixed(4)}`);
    console.log(`      Rate Code     : ${p.rate_code ?? "N/A"}`);
    console.log(`      Name          : ${p.rate_final_name ?? p.rate_original_name ?? "N/A"}`);
    console.log(`      Unit          : ${p.rate_unit ?? "N/A"}`);
    console.log(`      Department    : ${p.department_name ?? "N/A"}`);
    console.log(`      Section       : ${p.section_name ?? "N/A"}`);
    console.log(`      Total Cost    : ${p.total_cost_per_position ?? "N/A"}`);
    console.log(`      Material Cost : ${p.total_material_cost_per_position ?? "N/A"}`);
    console.log(`      Resource      : ${p.resource_name ?? "N/A"}`);
    console.log(`      Labor Hours   : ${p.labor_hours_construction_workers ?? "N/A"}`);
    console.log();
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  // Verify collection exists
  const collections = await qdrant.getCollections();
  const names = collections.collections.map((c) => c.name);
  console.log("Available collections:", names.join(", "));

  if (!names.includes(COLLECTION)) {
    console.error(`\nCollection '${COLLECTION}' not found. Available: ${names.join(", ")}`);
    process.exit(1);
  }

  // Run searches sequentially to keep output readable
  for (const query of QUERIES) {
    await searchAndDisplay(query);
  }

  console.log("Done.");
}

main().catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});
