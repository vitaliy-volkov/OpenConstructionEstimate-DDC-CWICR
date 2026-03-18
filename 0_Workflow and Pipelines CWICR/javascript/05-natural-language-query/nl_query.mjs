/**
 * 05 - Natural Language Query
 *
 * Uses OpenAI function calling to convert natural language questions into
 * structured Qdrant filter queries against the DDC-CWICR database.
 *
 * Usage:
 *   export OPENAI_API_KEY="sk-..."
 *   node nl_query.mjs
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

// Sample natural language queries to demonstrate
const QUESTIONS = [
  "What are the cheapest flooring options under EUR 100?",
  "Show me plumbing installation rates in the mechanical department",
  "Find exterior painting work items measured in m2",
];

// ---------------------------------------------------------------------------
// Initialize clients
// ---------------------------------------------------------------------------

const openai = new OpenAI();

const qdrant = new QdrantClient({
  url: QDRANT_URL,
  ...(QDRANT_API_KEY && { apiKey: QDRANT_API_KEY }),
});

// ---------------------------------------------------------------------------
// Function calling tool definition
// ---------------------------------------------------------------------------

const searchTool = {
  type: "function",
  function: {
    name: "search_construction_rates",
    description:
      "Search the DDC-CWICR construction cost database using semantic search with optional filters.",
    parameters: {
      type: "object",
      properties: {
        search_query: {
          type: "string",
          description:
            "The semantic search query describing the construction work item to find.",
        },
        department_filter: {
          type: "string",
          description:
            "Optional filter for department_name (e.g., 'Mechanical', 'Electrical', 'Structural').",
        },
        section_filter: {
          type: "string",
          description:
            "Optional filter for section_name.",
        },
        unit_filter: {
          type: "string",
          description:
            "Optional filter for rate_unit (e.g., 'm2', 'm3', 'kg', 'pcs', 'lm').",
        },
        max_cost: {
          type: "number",
          description:
            "Optional maximum total_cost_per_position in EUR.",
        },
        min_cost: {
          type: "number",
          description:
            "Optional minimum total_cost_per_position in EUR.",
        },
        limit: {
          type: "integer",
          description: "Number of results to return (default 5).",
        },
      },
      required: ["search_query"],
    },
  },
};

// ---------------------------------------------------------------------------
// Execute the structured search
// ---------------------------------------------------------------------------

async function executeSearch(args) {
  // Build the Qdrant filter
  const mustConditions = [];

  if (args.department_filter) {
    mustConditions.push({
      key: "department_name",
      match: { text: args.department_filter },
    });
  }

  if (args.section_filter) {
    mustConditions.push({
      key: "section_name",
      match: { text: args.section_filter },
    });
  }

  if (args.unit_filter) {
    mustConditions.push({
      key: "rate_unit",
      match: { value: args.unit_filter },
    });
  }

  if (args.max_cost !== undefined) {
    mustConditions.push({
      key: "total_cost_per_position",
      range: { lte: args.max_cost },
    });
  }

  if (args.min_cost !== undefined) {
    mustConditions.push({
      key: "total_cost_per_position",
      range: { gte: args.min_cost },
    });
  }

  // Embed the search query
  const embResponse = await openai.embeddings.create({
    model: EMBEDDING_MODEL,
    input: args.search_query,
    dimensions: EMBEDDING_DIMS,
  });
  const vector = embResponse.data[0].embedding;

  // Build search parameters
  const searchParams = {
    vector,
    limit: args.limit || TOP_K,
    with_payload: true,
  };

  if (mustConditions.length > 0) {
    searchParams.filter = { must: mustConditions };
  }

  // Execute search
  const results = await qdrant.search(COLLECTION, searchParams);
  return results;
}

// ---------------------------------------------------------------------------
// Process a natural language question
// ---------------------------------------------------------------------------

async function processQuestion(question) {
  console.log(`\n${"=".repeat(70)}`);
  console.log(`Question: "${question}"`);
  console.log(`${"=".repeat(70)}\n`);

  // Step 1: Use OpenAI function calling to parse the question
  const response = await openai.chat.completions.create({
    model: "gpt-4o",
    temperature: 0,
    messages: [
      {
        role: "system",
        content: `You are a construction cost database assistant. Convert user questions
into structured search queries against a construction cost database.
The database contains columns: rate_code, rate_original_name, rate_final_name,
rate_unit, department_name, section_name, total_cost_per_position,
total_material_cost_per_position, resource_name, resource_quantity,
resource_price_per_unit_eur_current, labor_hours_construction_workers.
Always call the search_construction_rates function.`,
      },
      {
        role: "user",
        content: question,
      },
    ],
    tools: [searchTool],
    tool_choice: { type: "function", function: { name: "search_construction_rates" } },
  });

  const toolCall = response.choices[0].message.tool_calls?.[0];
  if (!toolCall) {
    console.log("  The model did not produce a function call.\n");
    return;
  }

  const args = JSON.parse(toolCall.function.arguments);
  console.log("  Parsed query parameters:");
  console.log(`    Search query : ${args.search_query}`);
  if (args.department_filter) console.log(`    Department   : ${args.department_filter}`);
  if (args.section_filter) console.log(`    Section      : ${args.section_filter}`);
  if (args.unit_filter) console.log(`    Unit         : ${args.unit_filter}`);
  if (args.max_cost !== undefined) console.log(`    Max cost     : EUR ${args.max_cost}`);
  if (args.min_cost !== undefined) console.log(`    Min cost     : EUR ${args.min_cost}`);
  console.log();

  // Step 2: Execute the search
  const results = await executeSearch(args);

  // Step 3: Display results
  if (results.length === 0) {
    console.log("  No results found.\n");
    return;
  }

  for (const [i, hit] of results.entries()) {
    const p = hit.payload || {};
    console.log(`  #${i + 1}  Score: ${hit.score.toFixed(4)}`);
    console.log(`      Rate Code   : ${p.rate_code ?? "N/A"}`);
    console.log(`      Name        : ${p.rate_final_name ?? p.rate_original_name ?? "N/A"}`);
    console.log(`      Unit        : ${p.rate_unit ?? "N/A"}`);
    console.log(`      Department  : ${p.department_name ?? "N/A"}`);
    console.log(`      Total Cost  : EUR ${p.total_cost_per_position ?? "N/A"}`);
    console.log(`      Material    : EUR ${p.total_material_cost_per_position ?? "N/A"}`);
    console.log();
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  console.log("Natural Language Query — DDC-CWICR Database\n");

  for (const question of QUESTIONS) {
    await processQuestion(question);
  }

  console.log("Done.");
}

main().catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});
