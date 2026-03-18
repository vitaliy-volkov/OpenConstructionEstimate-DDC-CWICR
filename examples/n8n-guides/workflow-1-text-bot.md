# Workflow 1: Text-Based Telegram Bot

**File:** `2_n8n_Pipelines_Cost_Calculation/n8n_1_Telegram_Bot_Cost_Estimates_and_Rate_Finder_TEXT_DDC_CWICR.json`
**Workflow name:** DDC CWICR - Text Estimator v11 (AI Nodes)

A Telegram bot that accepts text descriptions of construction work and returns detailed cost estimates using the DDC CWICR database.

---

## What It Does

1. User sends a text message to the Telegram bot (e.g., "install 50 sqm of ceramic floor tiles")
2. The bot selects the appropriate regional database based on user language preference
3. AI parses the input into structured work items with quantities
4. Each work item is embedded and searched against Qdrant for matching DDC CWICR entries
5. Results are reranked by relevance, costs are calculated, and a formatted estimate is returned

---

## Prerequisites

- n8n instance (self-hosted)
- Telegram Bot token (from @BotFather)
- OpenAI API key
- Qdrant with DDC CWICR collections loaded

---

## Required Credentials

Configure in the `TOKEN` node:

| Field | Value | Source |
|-------|-------|--------|
| `bot_token` | Telegram Bot API token | @BotFather |
| `OPENAI_API_KEY` | OpenAI API key | platform.openai.com |
| `QDRANT_URL` | Qdrant server URL | Default: `http://localhost:6333` |
| `QDRANT_API_KEY` | Qdrant API key | Leave empty for local |

n8n Credentials (Settings > Credentials):
- **OpenAI API** -- linked to LLM and Embedding nodes
- **Anthropic API** -- optional, for Claude as alternative model
- **Google Gemini API** -- optional, for Gemini as alternative model

---

## Node Flow

```
Telegram Trigger
  --> TOKEN (credentials)
  --> Main Router (parse message/callback, manage sessions)
  --> Route Switch (17 actions)
      |
      |--> Language Selection (11 languages)
      |--> Text Analysis
      |      --> AI Parse Text (extract work items)
      |      --> Transform Query (optimize for search)
      |      --> OpenAI Embeddings (text-embedding-3-large)
      |      --> Qdrant Vector Search
      |      --> AI Rerank Results
      |      --> Cost Calculation
      |      --> Format Response (HTML)
      |
      |--> Export Excel
      |--> Export PDF
      |--> Help / Start
      |--> Fallback
  --> Telegram Send Response
```

---

## Key Nodes

### TOKEN
Sets all API credentials and configuration. This is the only node you need to edit.

### Main Router
Central message handler. Parses incoming Telegram updates (messages and callback queries), manages user session state, detects content type, and routes to the appropriate action.

### Route Switch
Dispatches to one of 17 action branches based on the router output. Key actions include:
- `show_lang` -- Display language selection menu
- `lang_selected` -- Save user language preference
- `analyze_text` -- Process text input for cost estimation
- `start_calc` -- Calculate and return the cost estimate
- `export_excel` / `export_pdf` -- Generate downloadable reports

### AI Parse Text
Uses OpenAI (or Claude/Gemini) to extract structured work items from free-form text. Outputs a JSON array of items with descriptions and quantities.

### Qdrant Vector Search
Searches the selected DDC CWICR collection for matching work items. Uses OpenAI `text-embedding-3-large` embeddings (3072 dimensions).

### AI Rerank Results
Post-processes search results using an LLM to select the most relevant matches and filter out noise.

---

## Supported Languages

The bot supports 11 languages, each mapped to a regional Qdrant collection:

| Language | Collection | Currency |
|----------|-----------|----------|
| English | `ddc_en_toronto` | CAD $ |
| German | `ddc_de_berlin` | EUR |
| Russian | `ddc_ru_stpetersburg` | RUB |
| French | `ddc_fr_paris` | EUR |
| Spanish | `ddc_sp_barcelona` | EUR |
| Portuguese | `ddc_pt_saopaulo` | BRL |
| Chinese | `ddc_zh_shanghai` | CNY |
| Arabic | `ddc_ar_dubai` | AED |
| Hindi | `ddc_hi_mumbai` | INR |
| US English | `ddc_usa_usd` | USD |
| UK English | `ddc_uk_gbp` | GBP |

---

## Customization

### Switching AI Models
1. In the workflow editor, locate the AI model nodes (OpenAI, Claude, Gemini)
2. Disable the current active model node
3. Enable the alternative model node
4. Models auto-connect to the processing chain via n8n AI nodes

### Adding Custom Prompts
Edit the system prompt in the AI Parse Text and AI Rerank nodes to adjust how work items are extracted and ranked.

### Adjusting Search Parameters
In the Qdrant search node, modify:
- `limit` -- Number of results returned (default: 5 per work item)
- `score_threshold` -- Minimum similarity score (default: 0.7)

---

## Testing

1. Import the workflow JSON into n8n
2. Fill in credentials in the TOKEN node
3. Set up n8n credentials for OpenAI and Telegram
4. Activate the workflow
5. Send `/start` to your bot in Telegram
6. Select a language
7. Enter a construction work description
8. Verify you receive a formatted cost estimate
