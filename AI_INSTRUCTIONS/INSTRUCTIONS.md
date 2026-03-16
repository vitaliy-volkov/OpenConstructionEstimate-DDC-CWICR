# DDC CWICR - AI Assistant Instructions

> **DDC CWICR** (Construction Work Items, Components & Resources) is an open-source multilingual construction cost database with 55,719 work items and 27,672 resources across 11 languages, powered by pre-computed OpenAI embeddings for semantic search.

## Quick Start

```python
import pandas as pd
from qdrant_client import QdrantClient

# Load data
df = pd.read_parquet("DDC_CWICR_EN.parquet")

# Semantic search
client = QdrantClient("localhost", port=6333)
results = client.search(
    collection_name="ddc_en_toronto",
    query_vector=embedding,
    limit=10
)
```

## What This Repository Is

**DDC CWICR** is a comprehensive construction cost database designed for:
- **Automated cost estimation** from BIM models, photos, or text descriptions
- **Semantic search** via Qdrant vector database with pre-computed embeddings
- **AI/LLM integration** for intelligent material matching and price lookup
- **Multi-language support** with region-specific pricing

## Database Statistics

| Metric | Value |
|--------|-------|
| Work Items | 55,719 |
| Resources | 27,672 |
| Languages | 11 |
| Data Fields | 85 |
| Embedding Dimensions | 3,072 (OpenAI text-embedding-3-large) |

## Available Formats

| Format | Size | Best For |
|--------|------|----------|
| **Excel** (.xlsx) | 150-400 MB | Manual analysis, pivot tables |
| **Parquet** (.parquet) | 55 MB | ETL pipelines, ML training, Python |
| **CSV** (.csv) | 1.3 GB | Database imports, legacy systems |
| **Qdrant** (.snapshot) | 1 GB | Semantic search, RAG systems |

## Languages & Regional Pricing

| Code | Language | Region | Currency | Collection | Snapshot Path |
|------|----------|--------|----------|------------|---------------|
| `AR` | Arabic | Dubai | AED | `ddc_ar_dubai` | `AR___DDC_CWICR/AR_DUBAI_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| `ZH` | Chinese | Shanghai | CNY | `ddc_zh_shanghai` | `ZH___DDC_CWICR/ZH_SHANGHAI_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| `DE` | German | Berlin | EUR | `ddc_de_berlin` | `DE___DDC_CWICR/DE_BERLIN_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| `EN` | English | Toronto | CAD | `ddc_en_toronto` | `EN___DDC_CWICR/EN_TORONTO_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| `ES` | Spanish | Barcelona | EUR | `ddc_sp_barcelona` | `ES___DDC_CWICR/ES_BARCELONA_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| `FR` | French | Paris | EUR | `ddc_fr_paris` | `FR___DDC_CWICR/FR_PARIS_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| `HI` | Hindi | Mumbai | INR | `ddc_hi_mumbai` | `HI___DDC_CWICR/HI_MUMBAI_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| `PT` | Portuguese | São Paulo | BRL | `ddc_pt_saopaulo` | `PT___DDC_CWICR/PT_SAOPAULO_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| `RU` | Russian | St. Petersburg | RUB | `ddc_ru_stpetersburg` | `RU___DDC_CWICR/RU_STPETERSBURG_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| `US` | English | USA | USD | `ddc_usa_usd` | `US___DDC_CWICR/US_USD_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| `UK` | English | UK | GBP | `ddc_uk_gbp` | `UK___DDC_CWICR/UK_GBP_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |

## Core Methodology

**Resource-Based Costing**: Separates unchanging production norms from volatile pricing.

```
Cost = Technology Norm × Regional Price
```

Each work item breaks down into:
- **Materials** - quantities and specifications
- **Labor** - worker hours by qualification
- **Equipment** - machine hours and fuel consumption

## Key Data Fields

### Work Item Identification
- `rate_code` - Unique identifier
- `rate_original_name` - Full description
- `rate_unit_of_measure` - Unit (m², m³, kg, etc.)

### Cost Breakdown
- `total_cost_per_position` - Total cost
- `total_material_cost` - Material costs
- `total_labor_cost` - Labor costs
- `total_machinery_cost` - Equipment costs

### Resources
- `material_*` - Material specifications
- `labor_*` - Labor hours and rates
- `machinery_*` - Equipment requirements

## n8n Workflows

The repository includes production-ready automation workflows:

1. **Text Estimator Bot** - Telegram interface for natural language descriptions
2. **Photo Analyzer** - GPT-4 Vision extracts elements from construction photos
3. **Universal Bot** - Combined text/photo/PDF input
4. **CAD/BIM Pipeline** - 10-stage pipeline for Revit/IFC/DWG → 4D/5D estimates

> **Important for AI Assistants**: These n8n workflows are **examples and templates** that demonstrate cost estimation logic. They can be:
> - Used as-is for quick deployment
> - Partially adapted for specific business requirements
> - Studied to understand the cost calculation methodology
> - Referenced when building custom integrations in any platform
>
> The workflows show how to: query the database, match work items, apply regional pricing, calculate totals, and generate reports. AI can analyze these workflows to understand the complete estimation logic and apply it to any business case.

## Integration Examples

### Python + Pandas
```python
import pandas as pd

df = pd.read_parquet("DDC_CWICR_EN.parquet")

# Find concrete work items
concrete = df[df['rate_original_name'].str.contains('concrete', case=False)]
print(concrete[['rate_code', 'rate_original_name', 'total_cost_per_position']])
```

### Qdrant Semantic Search
```python
from qdrant_client import QdrantClient
import openai

# Get embedding
response = openai.embeddings.create(
    model="text-embedding-3-large",
    input="reinforced concrete foundation"
)
embedding = response.data[0].embedding

# Search
client = QdrantClient("localhost", port=6333)
results = client.search(
    collection_name="ddc_en_toronto",
    query_vector=embedding,
    limit=5
)
```

## License

- **Database**: CC BY 4.0 (free commercial use with attribution)
- **Code**: MIT (unrestricted use)

## Related Repository

For CAD/BIM conversion tools (Revit, IFC, DWG, DGN → Excel), see:
[cad2data-Revit-IFC-DWG-DGN-pipeline](https://github.com/datadrivenconstruction/cad2data-Revit-IFC-DWG-DGN-pipeline-with-conversion-validation-qto)

---

*"The resource-based approach separates the unchanging laws of physics (labor hours, material consumption) from volatile economics (regional prices, inflation)."*
