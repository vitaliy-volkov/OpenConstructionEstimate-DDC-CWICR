# Workflow 3: Universal Telegram Bot (Text + Photo + PDF)

**File:** `2_n8n_Pipelines_Cost_Calculation/n8n_3_Telegram_Bot_Cost_Estimates_and_Rate_Finder_TEXT_PHOTO_PDF_DDC_CWICR.json`
**Workflow name:** DDC CWICR v10.9 - Construction Cost Estimator Bot

A full-featured Telegram bot that accepts text descriptions, construction photos, and PDF documents to produce cost estimates. This is the most comprehensive of the four workflows.

---

## What It Does

1. User interacts with the Telegram bot via `/start`
2. User selects a language (11 options)
3. User sends input in one of three formats:
   - **Text** -- free-form description of construction work
   - **Photo** -- image of a construction site or element
   - **PDF** -- document with project specifications
4. AI processes the input, searches the DDC CWICR database, and returns a cost estimate
5. User can edit quantities, add work items, or export results as Excel/PDF

---

## Prerequisites

- n8n instance (self-hosted)
- Telegram Bot token (from @BotFather)
- OpenAI API key (embeddings + LLM)
- Google Gemini API key (recommended for vision processing)
- Qdrant with DDC CWICR collections loaded

---

## Required Credentials

### TOKEN Node

| Field | Value | Source |
|-------|-------|--------|
| `bot_token` | Telegram Bot API token | @BotFather |
| `AI_PROVIDER` | `"gemini"` or `"openai"` | Vision provider selection |
| `GEMINI_API_KEY` | Google Gemini API key | aistudio.google.com |
| `OPENAI_API_KEY` | OpenAI API key | platform.openai.com |
| `QDRANT_URL` | Qdrant server URL | Default: `http://localhost:6333` |
| `QDRANT_API_KEY` | Qdrant API key | Leave empty for local |

### n8n Credentials (Settings > Credentials)
- **Telegram API** -- for sending/receiving messages
- **OpenAI API** -- for embeddings and LLM

---

## Node Flow

```
Telegram Trigger
  --> TOKEN (credentials + AI provider selection)
  --> Main Router (parse message/callback, session management)
  --> Config & Localization (11 languages, UI messages, currency mapping)
  --> Route Switch (17 actions)
      |
      |--> Action 0: show_lang       -- Language selection menu
      |--> Action 1: ask_photo       -- Request photo from user
      |--> Action 2: lang_selected   -- Save language preference
      |--> Action 3: show_analyze    -- Photo analysis options
      |--> Action 4: analyze         -- AI vision processing
      |--> Action 5: show_edit_menu  -- Edit work items
      |--> Action 6: works_updated   -- Quantity changed
      |--> Action 7: ask_new_work    -- Add new work item
      |--> Action 8: start_calc      -- Calculate costs
      |--> Action 9: show_help       -- Help text
      |--> Action 10: view_details   -- Work item details
      |--> Action 11: export_excel   -- CSV/Excel export
      |--> Action 12: export_pdf     -- PDF report export
      |--> Action 13: process_pdf    -- PDF document analysis
      |--> Action 14: analyze_text   -- Text input processing
      |--> Action 15: refine         -- Re-analyze with adjustments
      |--> Action 16: fallback       -- Unknown input handler
  --> Telegram Send Response
```

---

## Key Nodes

### Main Router
Central message handler that:
- Parses Telegram updates (messages, callback queries, documents)
- Detects content type (text, photo, PDF)
- Manages per-user session state (language, work items, current action)
- Routes to the appropriate action

### Config & Localization
Contains all UI strings, button labels, currency symbols, and database mappings for 11 languages. Auto-selects the correct database and currency based on user language.

### Route Switch
A 17-way switch that dispatches to specialized processing branches. Each action is self-contained with its own processing logic and Telegram response.

### Vision Processing (Action 4)
Supports two AI providers for photo analysis:
- **Gemini 2.0 Flash** -- set `AI_PROVIDER` to `"gemini"`
- **GPT-4 Vision** -- set `AI_PROVIDER` to `"openai"`

### PDF Processing (Action 13)
Extracts text from uploaded PDF documents, identifies construction work items, and runs them through the standard estimation pipeline.

### Export Nodes (Actions 11-12)
Generate downloadable reports:
- **Excel** -- CSV with all work items, quantities, unit costs, and totals
- **PDF** -- Formatted report with project summary and cost breakdown

---

## Supported Languages

| Language | Collection | City | Currency |
|----------|-----------|------|----------|
| German (DE) | `ddc_de_berlin` | Berlin | EUR |
| English (EN) | `ddc_en_toronto` | Toronto | CAD $ |
| Russian (RU) | `ddc_ru_stpetersburg` | St. Petersburg | RUB |
| Spanish (ES) | `ddc_sp_barcelona` | Barcelona | EUR |
| French (FR) | `ddc_fr_paris` | Paris | EUR |
| Portuguese (PT) | `ddc_pt_saopaulo` | Sao Paulo | BRL |
| Chinese (ZH) | `ddc_zh_shanghai` | Shanghai | CNY |
| Arabic (AR) | `ddc_ar_dubai` | Dubai | AED |
| Hindi (HI) | `ddc_hi_mumbai` | Mumbai | INR |
| US English (US) | `ddc_usa_usd` | USA | USD |
| UK English (UK) | `ddc_uk_gbp` | UK | GBP |

---

## Customization

### Switching Vision Provider
In the TOKEN node, change `AI_PROVIDER`:
- `"gemini"` -- uses Gemini 2.0 Flash (faster, good accuracy)
- `"openai"` -- uses GPT-4 Vision (higher accuracy, slower)

### Editing UI Messages
All user-facing text is in the Config & Localization node. Modify button labels, help text, error messages, and system prompts per language.

### Adding Export Formats
The export nodes generate HTML that is converted to Excel/PDF. Modify the HTML templates in the export code nodes to change report layout.

---

## Testing

1. Import the workflow JSON into n8n
2. Fill in all fields in the TOKEN node
3. Set up n8n credentials for Telegram and OpenAI
4. Activate the workflow
5. In Telegram, send `/start` to your bot
6. Select a language
7. Test each input type:
   - Send a text description (e.g., "paint 100 sqm of walls")
   - Send a construction photo
   - Send a PDF document
8. Verify cost estimates are returned for each input type
9. Test export functions (Excel, PDF)
