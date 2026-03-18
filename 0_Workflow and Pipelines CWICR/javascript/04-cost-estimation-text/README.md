# 04 - Cost Estimation from Text Description

## Description

Given a free-text description of a construction task (e.g., "build a 200 m2
concrete slab foundation"), this script uses OpenAI to decompose the task into
searchable work items, finds matching cost rates in the DDC-CWICR Qdrant
database, and produces a structured cost estimate.

**Pipeline:**
1. Text decomposition (OpenAI chat completion)
2. Semantic search per work item (OpenAI embeddings + Qdrant)
3. Cost aggregation and summary

## Prerequisites

- Node.js >= 18
- Install dependencies from the parent directory:
  ```bash
  cd examples/javascript
  npm install
  ```
- A running Qdrant instance with the `ddc_en_toronto` collection
- An OpenAI API key exported as `OPENAI_API_KEY`

## Usage

```bash
export OPENAI_API_KEY="sk-..."
node estimate_from_text.mjs
```

Edit the `TASK_DESCRIPTION` constant in the script to try different tasks.
