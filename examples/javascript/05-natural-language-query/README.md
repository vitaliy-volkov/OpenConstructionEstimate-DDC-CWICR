# 05 - Natural Language Query

## Description

Convert natural language questions about construction costs into structured
Qdrant queries using OpenAI function calling. The LLM decides which filters
(department, section, unit, cost range) to apply and generates the search
query, which is then executed against the DDC-CWICR vector database.

**Examples of supported questions:**
- "What are the cheapest flooring options?"
- "Show me plumbing rates in the mechanical department under EUR 500"
- "Find exterior wall insulation materials"

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
node nl_query.mjs
```
