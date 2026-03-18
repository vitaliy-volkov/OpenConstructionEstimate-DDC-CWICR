# 03 - Cost Estimation from Text Description

Provide a natural language description of construction work (e.g., "renovate a 50m2 bathroom")
and get a structured cost estimate with labor, material, and equipment breakdown.

## How It Works

1. An LLM (Claude or GPT-4o) decomposes the text into individual work items.
2. Each work item is vector-searched in Qdrant to find matching DDC CWICR entries.
3. Costs are aggregated into a structured estimate.

## Prerequisites

- Python 3.9+
- `pip install -r ../requirements.txt`
- Qdrant running locally with indexed DDC data
- API key in `.env`:
  ```
  ANTHROPIC_API_KEY=sk-ant-...
  # or
  OPENAI_API_KEY=sk-...
  ```

## Usage

```bash
python estimate_from_text.py "renovate a 50m² bathroom with new tiles and plumbing"
python estimate_from_text.py "build a 200m² concrete foundation slab" --provider openai
python estimate_from_text.py "install electrical wiring in a 3-bedroom apartment" --collection ddc_de_berlin
```
