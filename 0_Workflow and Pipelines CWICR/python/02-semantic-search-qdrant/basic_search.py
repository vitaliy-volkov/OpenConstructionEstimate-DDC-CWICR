"""
Semantic search over DDC CWICR data stored in Qdrant.

Embeds a text query using OpenAI text-embedding-3-large (3072 dims),
searches the ddc_en_toronto collection, and displays the top results.
"""

import argparse
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    sys.exit("python-dotenv is required. Install with: pip install python-dotenv")

import os

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv()  # also check cwd

try:
    from openai import OpenAI
except ImportError:
    sys.exit("openai is required. Install with: pip install openai")

try:
    from qdrant_client import QdrantClient
except ImportError:
    sys.exit("qdrant-client is required. Install with: pip install qdrant-client")


EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMS = 3072
DEFAULT_COLLECTION = "ddc_en_toronto"
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

# Key fields to display in results
DISPLAY_FIELDS = [
    "rate_code",
    "rate_original_name",
    "rate_unit",
    "total_cost_per_position",
    "department_name",
    "section_name",
]


def get_embedding(client: OpenAI, text: str) -> list[float]:
    """Generate an embedding vector for the given text."""
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def main():
    parser = argparse.ArgumentParser(description="Semantic search in DDC CWICR via Qdrant.")
    parser.add_argument("query", type=str, help="Natural language search query.")
    parser.add_argument("--collection", type=str, default=DEFAULT_COLLECTION, help="Qdrant collection name.")
    parser.add_argument("--top", type=int, default=5, help="Number of results to return.")
    parser.add_argument("--qdrant-url", type=str, default=QDRANT_URL, help="Qdrant server URL.")
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit("OPENAI_API_KEY not set. Add it to .env or export it.")

    openai_client = OpenAI(api_key=api_key)
    qdrant = QdrantClient(url=args.qdrant_url)

    # Embed the query
    print(f"Query: \"{args.query}\"")
    print(f"Collection: {args.collection}\n")

    query_vector = get_embedding(openai_client, args.query)

    # Search Qdrant
    results = qdrant.search(
        collection_name=args.collection,
        query_vector=query_vector,
        limit=args.top,
    )

    if not results:
        print("No results found.")
        return

    # Display results
    print(f"Top {len(results)} results:\n")
    for i, hit in enumerate(results, 1):
        payload = hit.payload or {}
        score = hit.score

        print(f"--- Result {i} (score: {score:.4f}) ---")
        for field in DISPLAY_FIELDS:
            value = payload.get(field, "N/A")
            if field == "total_cost_per_position" and isinstance(value, (int, float)):
                value = f"{value:,.2f} EUR"
            print(f"  {field:<30} {value}")
        print()

    print("Done.")


if __name__ == "__main__":
    main()
