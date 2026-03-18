"""
Cost estimation from a text description of construction work.

Uses an LLM to decompose a description into work items, searches each
in Qdrant, and produces a structured cost estimate.
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    sys.exit("python-dotenv is required. Install with: pip install python-dotenv")

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv()

try:
    from openai import OpenAI
except ImportError:
    sys.exit("openai is required. Install with: pip install openai")

try:
    from qdrant_client import QdrantClient
except ImportError:
    sys.exit("qdrant-client is required. Install with: pip install qdrant-client")

EMBEDDING_MODEL = "text-embedding-3-large"
DEFAULT_COLLECTION = "ddc_en_toronto"
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

DECOMPOSE_PROMPT = """You are a construction cost estimator. Given a project description,
decompose it into individual work items that would appear in a Bill of Quantities.

For each work item, provide:
- description: short name of the work item (suitable for database search)
- quantity: estimated quantity (number)
- unit: measurement unit (m², m³, m, pcs, kg, etc.)

Return ONLY valid JSON as a list of objects. Example:
[
  {"description": "ceramic floor tiling", "quantity": 50, "unit": "m²"},
  {"description": "wall waterproofing membrane", "quantity": 60, "unit": "m²"}
]

Project description: {description}"""


def decompose_with_openai(description: str) -> list[dict]:
    """Use GPT-4o to decompose the description into work items."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": DECOMPOSE_PROMPT.format(description=description)}],
        temperature=0.2,
    )
    return json.loads(response.choices[0].message.content.strip().strip("```json").strip("```"))


def decompose_with_anthropic(description: str) -> list[dict]:
    """Use Claude to decompose the description into work items."""
    try:
        import anthropic
    except ImportError:
        sys.exit("anthropic is required. Install with: pip install anthropic")

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{"role": "user", "content": DECOMPOSE_PROMPT.format(description=description)}],
    )
    text = response.content[0].text.strip().strip("```json").strip("```")
    return json.loads(text)


def embed_text(text: str) -> list[float]:
    """Embed text using OpenAI."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def search_work_item(qdrant: QdrantClient, collection: str, description: str, top_k: int = 1) -> dict | None:
    """Search Qdrant for the best matching work item."""
    vector = embed_text(description)
    results = qdrant.search(collection_name=collection, query_vector=vector, limit=top_k)
    if not results:
        return None
    return results[0].payload


def main():
    parser = argparse.ArgumentParser(description="Estimate construction cost from text description.")
    parser.add_argument("description", type=str, help="Project description in natural language.")
    parser.add_argument("--provider", choices=["anthropic", "openai"], default=None,
                        help="LLM provider. Auto-detects from available API keys.")
    parser.add_argument("--collection", type=str, default=DEFAULT_COLLECTION, help="Qdrant collection.")
    parser.add_argument("--qdrant-url", type=str, default=QDRANT_URL, help="Qdrant URL.")
    args = parser.parse_args()

    # Determine LLM provider
    provider = args.provider
    if not provider:
        if os.getenv("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        elif os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        else:
            sys.exit("Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env.")

    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY required for OpenAI provider and embeddings.")
    if provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY required for Anthropic provider.")
    # Embeddings always need OpenAI
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY is required for embeddings (text-embedding-3-large).")

    qdrant = QdrantClient(url=args.qdrant_url)

    # Step 1: Decompose
    print(f"Project: \"{args.description}\"")
    print(f"LLM provider: {provider}\n")
    print("Decomposing into work items...")

    if provider == "anthropic":
        work_items = decompose_with_anthropic(args.description)
    else:
        work_items = decompose_with_openai(args.description)

    print(f"Found {len(work_items)} work items.\n")

    # Step 2: Search and price each item
    estimate_lines = []
    total_material = 0.0
    total_labor = 0.0
    total_equipment = 0.0
    total_cost = 0.0

    print(f"{'#':<4} {'Description':<40} {'Qty':<8} {'Unit':<6} {'Unit Rate':>12} {'Amount':>14}")
    print("-" * 90)

    for i, item in enumerate(work_items, 1):
        desc = item["description"]
        qty = float(item.get("quantity", 1))
        unit = item.get("unit", "pcs")

        match = search_work_item(qdrant, args.collection, desc)

        if match:
            rate_name = match.get("rate_original_name", desc)
            unit_cost = float(match.get("total_cost_per_position", 0))
            material_cost = float(match.get("total_material_cost_per_position", 0))
            resource_cost = float(match.get("total_resource_cost_per_position", 0))
            equip_cost = float(match.get("total_value_machinery_equipment", 0))
            amount = unit_cost * qty
        else:
            rate_name = desc
            unit_cost = 0
            material_cost = 0
            resource_cost = 0
            equip_cost = 0
            amount = 0

        total_material += material_cost * qty
        total_labor += resource_cost * qty
        total_equipment += equip_cost * qty
        total_cost += amount

        print(f"{i:<4} {rate_name[:40]:<40} {qty:<8.1f} {unit:<6} {unit_cost:>12,.2f} {amount:>14,.2f}")

        estimate_lines.append({
            "item": i,
            "description": rate_name,
            "quantity": qty,
            "unit": unit,
            "unit_rate": unit_cost,
            "amount": amount,
        })

    # Summary
    print("-" * 90)
    print(f"{'':>60} {'TOTAL':>12} {total_cost:>14,.2f} EUR")
    print()
    print("=== Cost Breakdown ===")
    print(f"  Materials:  {total_material:>14,.2f} EUR")
    print(f"  Labor:      {total_labor:>14,.2f} EUR")
    print(f"  Equipment:  {total_equipment:>14,.2f} EUR")
    print(f"  Total:      {total_cost:>14,.2f} EUR")
    print()
    print("Note: Costs are based on DDC CWICR reference data. Actual costs may vary.")


if __name__ == "__main__":
    main()
