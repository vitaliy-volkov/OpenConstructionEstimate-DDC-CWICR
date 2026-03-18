"""
Cost estimation from a construction site photo.

Sends an image to GPT-4o vision to identify construction elements,
then searches Qdrant for cost data and generates a priced BOQ.
"""

import argparse
import base64
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

VISION_PROMPT = """Analyze this construction site photo. Identify all visible construction
elements, materials, and work activities.

For each element, provide:
- description: a concise name suitable for cost database lookup
- quantity: estimated quantity (use 1 if uncertain)
- unit: measurement unit (m², m³, m, pcs, kg, etc.)

Return ONLY valid JSON as a list. Example:
[
  {"description": "reinforced concrete column", "quantity": 4, "unit": "pcs"},
  {"description": "brick wall construction", "quantity": 30, "unit": "m²"}
]"""


def encode_image(image_path: str) -> str:
    """Read and base64-encode an image file."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def detect_mime(path: str) -> str:
    """Detect image MIME type from extension."""
    ext = Path(path).suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                ".gif": "image/gif", ".webp": "image/webp"}
    return mime_map.get(ext, "image/jpeg")


def analyze_photo(client: OpenAI, image_path: str) -> list[dict]:
    """Send image to GPT-4o vision and extract construction elements."""
    b64 = encode_image(image_path)
    mime = detect_mime(image_path)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": VISION_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
            ],
        }],
        temperature=0.2,
        max_tokens=2048,
    )

    text = response.choices[0].message.content.strip().strip("```json").strip("```")
    return json.loads(text)


def embed_text(client: OpenAI, text: str) -> list[float]:
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def search_item(client: OpenAI, qdrant: QdrantClient, collection: str,
                description: str, top_k: int = 1) -> dict | None:
    vector = embed_text(client, description)
    results = qdrant.search(collection_name=collection, query_vector=vector, limit=top_k)
    return results[0].payload if results else None


def main():
    parser = argparse.ArgumentParser(description="Estimate construction cost from a photo.")
    parser.add_argument("image", type=str, help="Path to the construction photo.")
    parser.add_argument("--collection", type=str, default=DEFAULT_COLLECTION, help="Qdrant collection.")
    parser.add_argument("--top", type=int, default=1, help="Top K matches per element.")
    parser.add_argument("--qdrant-url", type=str, default=QDRANT_URL, help="Qdrant URL.")
    args = parser.parse_args()

    if not Path(args.image).exists():
        sys.exit(f"Image not found: {args.image}")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit("OPENAI_API_KEY not set. Add it to .env or export it.")

    openai_client = OpenAI(api_key=api_key)
    qdrant = QdrantClient(url=args.qdrant_url)

    # Step 1: Analyze photo
    print(f"Analyzing photo: {args.image}")
    print("Sending to GPT-4o vision...\n")

    elements = analyze_photo(openai_client, args.image)
    print(f"Detected {len(elements)} construction elements.\n")

    # Step 2: Search and price
    print(f"{'#':<4} {'Detected Element':<35} {'Matched Rate':<35} {'Qty':<8} {'Unit':<6} {'Rate':>12} {'Amount':>14}")
    print("-" * 120)

    total = 0.0
    boq_lines = []

    for i, elem in enumerate(elements, 1):
        desc = elem["description"]
        qty = float(elem.get("quantity", 1))
        unit = elem.get("unit", "pcs")

        match = search_item(openai_client, qdrant, args.collection, desc, args.top)

        if match:
            rate_name = match.get("rate_original_name", desc)[:35]
            rate_code = match.get("rate_code", "")
            unit_cost = float(match.get("total_cost_per_position", 0))
        else:
            rate_name = "(no match)"
            rate_code = ""
            unit_cost = 0

        amount = unit_cost * qty
        total += amount

        print(f"{i:<4} {desc[:35]:<35} {rate_name:<35} {qty:<8.1f} {unit:<6} {unit_cost:>12,.2f} {amount:>14,.2f}")

        boq_lines.append({
            "item": i,
            "detected": desc,
            "rate_code": rate_code,
            "matched": rate_name,
            "quantity": qty,
            "unit": unit,
            "unit_rate": unit_cost,
            "amount": amount,
        })

    print("-" * 120)
    print(f"{'':>100} {'TOTAL':>6} {total:>14,.2f} EUR")
    print()
    print("Note: Quantities are estimated from visual analysis. Verify before use.")


if __name__ == "__main__":
    main()
