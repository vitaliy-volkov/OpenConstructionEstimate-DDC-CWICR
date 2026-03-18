# Workflow 2: Photo-Based Cost Estimation

**File:** `2_n8n_Pipelines_Cost_Calculation/n8n_2_Photo_Cost_Estimate_DDC_CWICR.json`
**Workflow name:** Photo Cost Estimate Pro v2.0

A web-form-based workflow that accepts construction site photos and generates detailed cost estimates using AI vision and the DDC CWICR database.

---

## What It Does

1. User uploads a construction photo via an n8n web form
2. User selects a region/language and work type (new construction, renovation, repair, or auto-detect)
3. AI vision analyzes the photo to identify visible construction work items
4. Each identified work item is searched against the DDC CWICR Qdrant collection
5. A formatted cost estimate is returned in the browser

---

## Prerequisites

- n8n instance (self-hosted)
- OpenAI API key (for GPT-4 Vision and embeddings)
- Qdrant with DDC CWICR collections loaded

No Telegram bot is needed -- this workflow uses an n8n Form Trigger (web form).

---

## Required Credentials

Configure in the workflow's credential nodes:

| Credential | Purpose | Source |
|-----------|---------|--------|
| OpenAI API | Vision analysis + embeddings | platform.openai.com |
| Qdrant (optional) | If using n8n Qdrant node | Your Qdrant instance |

---

## Node Flow

```
Form Trigger (Photo Upload)
  --> Extract Input (parse form data, decode photo)
  --> AI Vision Analysis (identify work items from photo)
  --> Multi-Stage Decomposition
  |     --> Stage 1: Identify major work categories
  |     --> Stage 2: Break down into individual work items
  |     --> Stage 3: Estimate quantities from visual cues
  |
  --> OpenAI Embeddings (text-embedding-3-large)
  --> Qdrant Vector Search (regional collection)
  --> Cost Matching & Calculation
  --> Format HTML Response
  --> Return to Form (display in browser)
```

---

## Key Nodes

### Photo Upload Form
An n8n Form Trigger that creates a web page with:
- **Photo upload** -- accepts JPG, PNG, WEBP
- **Region & Language** -- dropdown with 9 regions (German/Berlin, English/Toronto, Russian/St. Petersburg, Spanish/Barcelona, French/Paris, Portuguese/Sao Paulo, Chinese/Shanghai, Arabic/Dubai, Hindi/Mumbai)
- **Work Type** -- New Construction, Renovation/Remodel, Repair, or Auto-detect
- **Description** -- optional text field for additional context

### Extract Input
JavaScript Code node that:
- Parses form fields
- Maps region selection to language code (DE, EN, RU, ES, FR, PT, ZH, AR, HI)
- Extracts photo as base64
- Detects work type

### AI Vision Analysis
Sends the photo to GPT-4 Vision (or Gemini Flash) with a specialized construction prompt. The model identifies:
- Visible construction elements
- Materials used
- Approximate dimensions and quantities
- Work type classification

### Multi-Stage Decomposition
Breaks the vision output into granular work items suitable for database matching. This multi-stage approach improves accuracy over single-pass analysis.

### Qdrant Vector Search
Searches the DDC CWICR collection for the user's selected region. Returns the closest matching work items with unit costs.

---

## Supported Regions

| Selection | Language Code | Collection | Currency |
|-----------|:------------:|-----------|----------|
| German - Berlin | DE | `ddc_de_berlin` | EUR |
| English - Toronto | EN | `ddc_en_toronto` | CAD $ |
| Russian - St. Petersburg | RU | `ddc_ru_stpetersburg` | RUB |
| Spanish - Barcelona | ES | `ddc_sp_barcelona` | EUR |
| French - Paris | FR | `ddc_fr_paris` | EUR |
| Portuguese - Sao Paulo | PT | `ddc_pt_saopaulo` | BRL |
| Chinese - Shanghai | ZH | `ddc_zh_shanghai` | CNY |
| Arabic - Dubai | AR | `ddc_ar_dubai` | AED |
| Hindi - Mumbai | HI | `ddc_hi_mumbai` | INR |

---

## Customization

### Changing the Vision Model
The workflow supports switching between OpenAI GPT-4 Vision and Google Gemini Flash for photo analysis. Edit the AI vision node to change the model.

### Adjusting Decomposition Depth
Modify the system prompts in the decomposition stages to control how granularly the photo is broken down into work items.

### Adding More Regions
Add new dropdown options in the Form Trigger node and extend the language mapping in the Extract Input code node.

---

## Testing

1. Import the workflow JSON into n8n
2. Configure OpenAI credentials
3. Activate the workflow
4. Open the form URL shown in the Form Trigger node
5. Upload a construction photo, select a region, and submit
6. Verify the cost estimate appears in the browser
