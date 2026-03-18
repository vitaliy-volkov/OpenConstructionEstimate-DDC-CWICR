/**
 * 02 - Qdrant REST API Quickstart
 *
 * Shows how to search the DDC-CWICR Qdrant collection using raw HTTP requests
 * (no Qdrant client library). The query text is embedded via the OpenAI
 * Embeddings API, and the resulting vector is sent to Qdrant's REST search
 * endpoint.
 *
 * Usage:
 *   export OPENAI_API_KEY="sk-..."
 *   node search_api.mjs
 */

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const QDRANT_URL = process.env.QDRANT_URL || "http://localhost:6333";
const QDRANT_API_KEY = process.env.QDRANT_API_KEY || "";
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const COLLECTION = "ddc_en_toronto";
const EMBEDDING_MODEL = "text-embedding-3-large";
const EMBEDDING_DIMS = 3072;
const TOP_K = 5;

const QUERY = "reinforced concrete foundation for a residential building";

if (!OPENAI_API_KEY) {
  console.error("Error: OPENAI_API_KEY environment variable is not set.");
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Step 1 — Embed the query with OpenAI
// ---------------------------------------------------------------------------

console.log(`\nEmbedding query: "${QUERY}"\n`);

const embeddingResponse = await fetch(
  "https://api.openai.com/v1/embeddings",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${OPENAI_API_KEY}`,
    },
    body: JSON.stringify({
      model: EMBEDDING_MODEL,
      input: QUERY,
      dimensions: EMBEDDING_DIMS,
    }),
  }
);

if (!embeddingResponse.ok) {
  const err = await embeddingResponse.text();
  console.error("OpenAI API error:", err);
  process.exit(1);
}

const embeddingData = await embeddingResponse.json();
const queryVector = embeddingData.data[0].embedding;

console.log(`Received embedding vector (${queryVector.length} dimensions)\n`);

// ---------------------------------------------------------------------------
// Step 2 — Search Qdrant via REST API
// ---------------------------------------------------------------------------

console.log(`Searching collection '${COLLECTION}' for top ${TOP_K} results...\n`);

const qdrantHeaders = { "Content-Type": "application/json" };
if (QDRANT_API_KEY) {
  qdrantHeaders["api-key"] = QDRANT_API_KEY;
}

const searchResponse = await fetch(
  `${QDRANT_URL}/collections/${COLLECTION}/points/search`,
  {
    method: "POST",
    headers: qdrantHeaders,
    body: JSON.stringify({
      vector: queryVector,
      limit: TOP_K,
      with_payload: true,
    }),
  }
);

if (!searchResponse.ok) {
  const err = await searchResponse.text();
  console.error("Qdrant search error:", err);
  process.exit(1);
}

const searchData = await searchResponse.json();

// ---------------------------------------------------------------------------
// Step 3 — Display results
// ---------------------------------------------------------------------------

console.log("=== Search Results ===\n");

for (const [i, result] of searchData.result.entries()) {
  const p = result.payload || {};
  console.log(`--- Result ${i + 1} (score: ${result.score.toFixed(4)}) ---`);
  console.log(`  Rate Code       : ${p.rate_code ?? "N/A"}`);
  console.log(`  Original Name   : ${p.rate_original_name ?? "N/A"}`);
  console.log(`  Final Name      : ${p.rate_final_name ?? "N/A"}`);
  console.log(`  Unit            : ${p.rate_unit ?? "N/A"}`);
  console.log(`  Department      : ${p.department_name ?? "N/A"}`);
  console.log(`  Section         : ${p.section_name ?? "N/A"}`);
  console.log(`  Total Cost      : ${p.total_cost_per_position ?? "N/A"}`);
  console.log(`  Material Cost   : ${p.total_material_cost_per_position ?? "N/A"}`);
  console.log();
}

console.log("Done.");
