"""
Filtered semantic search over DDC CWICR in Qdrant.

Combines vector similarity with payload filters such as department name
and cost range on total_cost_per_position.
"""

import argparse
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
    from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
except ImportError:
    sys.exit("qdrant-client is required. Install with: pip install qdrant-client")


EMBEDDING_MODEL = "text-embedding-3-large"
DEFAULT_COLLECTION = "ddc_en_toronto"
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

DISPLAY_FIELDS = [
    "rate_code",
    "rate_original_name",
    "rate_unit",
    "total_cost_per_position",
    "department_name",
    "section_name",
    "resource_name",
    "resource_price_per_unit_eur_current",
]


def get_embedding(client: OpenAI, text: str) -> list[float]:
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def build_filter(department: str | None, min_cost: float | None, max_cost: float | None) -> Filter | None:
    """Build a Qdrant filter from the provided criteria."""
    conditions = []

    if department:
        conditions.append(
            FieldCondition(key="department_name", match=MatchValue(value=department))
        )

    if min_cost is not None or max_cost is not None:
        range_params = {}
        if min_cost is not None:
            range_params["gte"] = min_cost
        if max_cost is not None:
            range_params["lte"] = max_cost
        conditions.append(
            FieldCondition(key="total_cost_per_position", range=Range(**range_params))
        )

    if not conditions:
        return None

    return Filter(must=conditions)


def main():
    parser = argparse.ArgumentParser(description="Filtered semantic search in DDC CWICR via Qdrant.")
    parser.add_argument("query", type=str, help="Natural language search query.")
    parser.add_argument("--department", type=str, default=None, help="Filter by department_name (exact match).")
    parser.add_argument("--min-cost", type=float, default=None, help="Minimum total_cost_per_position (EUR).")
    parser.add_argument("--max-cost", type=float, default=None, help="Maximum total_cost_per_position (EUR).")
    parser.add_argument("--collection", type=str, default=DEFAULT_COLLECTION, help="Qdrant collection name.")
    parser.add_argument("--top", type=int, default=5, help="Number of results.")
    parser.add_argument("--qdrant-url", type=str, default=QDRANT_URL, help="Qdrant server URL.")
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit("OPENAI_API_KEY not set. Add it to .env or export it.")

    openai_client = OpenAI(api_key=api_key)
    qdrant = QdrantClient(url=args.qdrant_url)

    # Build filter
    query_filter = build_filter(args.department, args.min_cost, args.max_cost)

    print(f"Query: \"{args.query}\"")
    print(f"Collection: {args.collection}")
    if args.department:
        print(f"Filter department: {args.department}")
    if args.min_cost is not None or args.max_cost is not None:
        cost_range = f"{args.min_cost or '...'} - {args.max_cost or '...'} EUR"
        print(f"Filter cost range: {cost_range}")
    print()

    # Embed and search
    query_vector = get_embedding(openai_client, args.query)

    results = qdrant.search(
        collection_name=args.collection,
        query_vector=query_vector,
        query_filter=query_filter,
        limit=args.top,
    )

    if not results:
        print("No results found. Try relaxing the filters.")
        return

    print(f"Top {len(results)} results:\n")
    for i, hit in enumerate(results, 1):
        payload = hit.payload or {}
        print(f"--- Result {i} (score: {hit.score:.4f}) ---")
        for field in DISPLAY_FIELDS:
            value = payload.get(field, "N/A")
            if "cost" in field or "price" in field:
                if isinstance(value, (int, float)):
                    value = f"{value:,.2f} EUR"
            print(f"  {field:<45} {value}")
        print()

    print("Done.")


if __name__ == "__main__":
    main()
