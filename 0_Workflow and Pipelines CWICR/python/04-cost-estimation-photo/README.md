# 04 - Cost Estimation from Photo

Upload a construction site photo and get a cost estimate. GPT-4o vision identifies
construction elements, which are then priced using the DDC CWICR database via Qdrant.

## How It Works

1. The photo is sent to GPT-4o with vision to identify visible construction elements.
2. Each identified element is searched in Qdrant for matching cost data.
3. Results are compiled into a priced Bill of Quantities.

## Prerequisites

- Python 3.9+
- `pip install -r ../requirements.txt`
- Qdrant running locally with indexed DDC data
- OpenAI API key in `.env`:
  ```
  OPENAI_API_KEY=sk-...
  ```

## Usage

```bash
python estimate_from_photo.py /path/to/construction_photo.jpg
python estimate_from_photo.py photo.png --collection ddc_de_berlin --top 3
```
