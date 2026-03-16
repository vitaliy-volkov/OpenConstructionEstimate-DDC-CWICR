# Google Antigravity Instructions for DDC CWICR

> Instructions for using DDC CWICR construction cost database with Google Antigravity and GCP services.

## What is DDC CWICR?

Open-source construction cost database optimized for AI/ML workflows:
- **55,719 work items** with 85 data fields
- **27,672 resources** (materials, labor, equipment)
- **11 languages** with regional pricing
- **Pre-computed OpenAI embeddings** (3072 dimensions)
- **Qdrant vector database** ready

## GCP Integration Patterns

### BigQuery Import

```sql
-- Create table from Parquet
CREATE OR REPLACE EXTERNAL TABLE `project.dataset.cwicr_en`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://bucket/DDC_CWICR_EN.parquet']
);

-- Query work items
SELECT rate_code, rate_original_name, total_cost_per_position
FROM `project.dataset.cwicr_en`
WHERE LOWER(rate_original_name) LIKE '%concrete%'
LIMIT 100;
```

### Cloud Functions + Vertex AI

```python
import functions_framework
from google.cloud import bigquery
import vertexai
from vertexai.language_models import TextEmbeddingModel

@functions_framework.http
def estimate_cost(request):
    """Estimate construction cost from description."""
    description = request.json.get('description')

    # Get embedding
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    embedding = model.get_embeddings([description])[0].values

    # Query BigQuery with vector search
    client = bigquery.Client()
    query = """
        SELECT rate_code, rate_original_name, total_cost_per_position
        FROM `project.dataset.cwicr_en`
        ORDER BY ML.DISTANCE(embedding, @query_embedding, 'COSINE')
        LIMIT 5
    """
    results = client.query(query, job_config=bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("query_embedding", "FLOAT64", embedding)
        ]
    ))

    return {"matches": [dict(row) for row in results]}
```

### Vertex AI Pipeline

```python
from google.cloud import aiplatform
from kfp import dsl

@dsl.pipeline(name="cost-estimation-pipeline")
def cost_pipeline(input_file: str, language: str = "en"):

    # Load BIM data
    load_op = dsl.ContainerOp(
        name="load-bim",
        image="gcr.io/project/bim-loader",
        arguments=["--input", input_file]
    )

    # Match work items
    match_op = dsl.ContainerOp(
        name="match-cwicr",
        image="gcr.io/project/cwicr-matcher",
        arguments=["--data", load_op.output, "--lang", language]
    )

    # Calculate costs
    cost_op = dsl.ContainerOp(
        name="calculate-cost",
        image="gcr.io/project/cost-calculator",
        arguments=["--matches", match_op.output]
    )

    return cost_op.output
```

### Gemini Integration

```python
import vertexai
from vertexai.generative_models import GenerativeModel
import pandas as pd

# Load CWICR data
df = pd.read_parquet("gs://bucket/DDC_CWICR_EN.parquet")

# Initialize Gemini
vertexai.init(project="your-project", location="us-central1")
model = GenerativeModel("gemini-2.0-flash")

def classify_and_estimate(element_description: str):
    """Use Gemini to classify BIM element and find matching work item."""

    # Get sample work items for context
    sample = df.sample(50)[['rate_code', 'rate_original_name', 'rate_unit_of_measure']].to_string()

    prompt = f"""
    Given this BIM element: {element_description}

    Find the most appropriate construction work item from this database:
    {sample}

    Return JSON with:
    - rate_code: matching code
    - confidence: 0-1 score
    - reasoning: why this match
    """

    response = model.generate_content(prompt)
    return response.text
```

## Data Schema

### Core Fields

| Field | Type | Description |
|-------|------|-------------|
| `rate_code` | STRING | Unique identifier |
| `rate_original_name` | STRING | Work description |
| `rate_unit_of_measure` | STRING | Unit (m², m³, kg) |
| `total_cost_per_position` | FLOAT | Total cost |
| `total_material_cost` | FLOAT | Materials |
| `total_labor_cost` | FLOAT | Labor |
| `total_machinery_cost` | FLOAT | Equipment |

### Classification

| Field | Type | Description |
|-------|------|-------------|
| `category_name` | STRING | Main category |
| `department_name` | STRING | Department |
| `section_name` | STRING | Section |

## Qdrant on GCP

Deploy Qdrant on GKE for semantic search:

```yaml
# qdrant-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qdrant
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:latest
        ports:
        - containerPort: 6333
        volumeMounts:
        - name: qdrant-storage
          mountPath: /qdrant/storage
```

Load CWICR snapshot (snapshots are stored in the repository language folders via Git LFS):
```bash
# Snapshot is located in the repository:
# EN___DDC_CWICR/EN_TORONTO_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot

# Import to Qdrant
curl -X POST "http://localhost:6333/collections/ddc_en_toronto/snapshots/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "snapshot=@EN___DDC_CWICR/EN_TORONTO_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot"
```

## Languages & Collections

| Language | Collection | Region | Snapshot Path |
|----------|------------|--------|---------------|
| English | `ddc_en_toronto` | Toronto | `EN___DDC_CWICR/EN_TORONTO_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| German | `ddc_de_berlin` | Berlin | `DE___DDC_CWICR/DE_BERLIN_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| French | `ddc_fr_paris` | Paris | `FR___DDC_CWICR/FR_PARIS_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| Spanish | `ddc_sp_barcelona` | Barcelona | `ES___DDC_CWICR/ES_BARCELONA_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| Russian | `ddc_ru_stpetersburg` | St. Petersburg | `RU___DDC_CWICR/RU_STPETERSBURG_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| Chinese | `ddc_zh_shanghai` | Shanghai | `ZH___DDC_CWICR/ZH_SHANGHAI_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| Arabic | `ddc_ar_dubai` | Dubai | `AR___DDC_CWICR/AR_DUBAI_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| Portuguese | `ddc_pt_saopaulo` | São Paulo | `PT___DDC_CWICR/PT_SAOPAULO_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| Hindi | `ddc_hi_mumbai` | Mumbai | `HI___DDC_CWICR/HI_MUMBAI_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| English (USA) | `ddc_usa_usd` | USA | `US___DDC_CWICR/US_USD_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |
| English (UK) | `ddc_uk_gbp` | UK | `UK___DDC_CWICR/UK_GBP_workitems_costs_resources_EMBEDDINGS_3072_DDC_CWICR.snapshot` |

## n8n Workflows

Production-ready automation templates:

| # | Workflow | Description |
|---|----------|-------------|
| 1 | Text Estimator | Telegram bot for estimates |
| 2 | Photo Analyzer | GPT-4 Vision integration |
| 3 | Universal Bot | Multi-modal input |
| 4 | CAD/BIM Pipeline | BIM → 4D/5D estimates |

> **Note**: These workflows are **examples and templates** demonstrating cost estimation logic. They can be used fully or partially for any business case. Analyze them to understand the calculation methodology and apply it to custom GCP solutions.

## Resources

- **Live Demo**: [openconstructionestimate.com](https://openconstructionestimate.com)
- **Data & Snapshots**: Stored directly in the repository language folders via Git LFS (e.g., `EN___DDC_CWICR/`)
- **CAD/BIM Tools**: [cad2data Repository](https://github.com/datadrivenconstruction/cad2data-Revit-IFC-DWG-DGN-pipeline-with-conversion-validation-qto)
