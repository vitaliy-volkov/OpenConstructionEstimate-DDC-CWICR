# 02 - Semantic Search with Qdrant

Search the DDC CWICR construction cost database using natural language queries via Qdrant vector database.

## Scripts

- **basic_search.py** - Embed a text query and find the top-5 matching work items.
- **filtered_search.py** - Combine vector similarity with payload filters (department, price range).

## Prerequisites

- Python 3.9+
- `pip install -r ../requirements.txt`
- Qdrant running locally (default: `localhost:6333`). Start with Docker:
  ```bash
  docker-compose -f ../../docker-compose.yml up -d
  ```
- OpenAI API key in a `.env` file:
  ```
  OPENAI_API_KEY=sk-...
  ```

## Available Collections

| Collection | Language | City |
|---|---|---|
| ddc_en_toronto | English | Toronto |
| ddc_de_berlin | German | Berlin |
| ddc_ru_stpetersburg | Russian | St. Petersburg |
| ddc_fr_paris | French | Paris |
| ddc_sp_barcelona | Spanish | Barcelona |
| ddc_ar_dubai | Arabic | Dubai |
| ddc_zh_shanghai | Chinese | Shanghai |
| ddc_hi_mumbai | Hindi | Mumbai |
| ddc_pt_saopaulo | Portuguese | Sao Paulo |
| ddc_usa_usd | English (USA) | USD pricing |
| ddc_uk_gbp | English (UK) | GBP pricing |

## Usage

```bash
python basic_search.py "concrete foundation slab"
python basic_search.py "waterproofing membrane for roof" --top 10

python filtered_search.py "wall plastering" --department "Finishing works"
python filtered_search.py "excavation" --min-cost 100 --max-cost 5000
```
