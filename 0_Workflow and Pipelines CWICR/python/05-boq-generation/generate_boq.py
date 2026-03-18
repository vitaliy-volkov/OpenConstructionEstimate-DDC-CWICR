"""
Generate a Bill of Quantities (BOQ) from a CSV of work items.

Reads work items from CSV, searches each in Qdrant for matching DDC CWICR
entries, and exports a priced BOQ to Excel.
"""

import argparse
import csv
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
    import pandas as pd
except ImportError:
    sys.exit("pandas is required. Install with: pip install pandas openpyxl")

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


def embed_text(client: OpenAI, text: str) -> list[float]:
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def search_rate(openai_client: OpenAI, qdrant: QdrantClient,
                collection: str, description: str) -> dict | None:
    """Find the best matching rate in Qdrant."""
    vector = embed_text(openai_client, description)
    results = qdrant.search(collection_name=collection, query_vector=vector, limit=1)
    return results[0].payload if results else None


def read_input_csv(csv_path: str) -> list[dict]:
    """Read work items from CSV. Expected columns: description, quantity, unit."""
    items = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"description", "quantity", "unit"}
        if not required.issubset(set(reader.fieldnames or [])):
            sys.exit(f"CSV must have columns: {required}. Found: {reader.fieldnames}")
        for row in reader:
            items.append({
                "description": row["description"].strip(),
                "quantity": float(row["quantity"]),
                "unit": row["unit"].strip(),
            })
    return items


def main():
    parser = argparse.ArgumentParser(description="Generate a BOQ from CSV work items.")
    parser.add_argument("csv_file", type=str, help="Path to input CSV file.")
    parser.add_argument("--output", type=str, default="boq_output.xlsx", help="Output Excel file path.")
    parser.add_argument("--collection", type=str, default=DEFAULT_COLLECTION, help="Qdrant collection.")
    parser.add_argument("--qdrant-url", type=str, default=QDRANT_URL, help="Qdrant URL.")
    args = parser.parse_args()

    if not Path(args.csv_file).exists():
        sys.exit(f"CSV file not found: {args.csv_file}")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit("OPENAI_API_KEY not set. Add it to .env or export it.")

    openai_client = OpenAI(api_key=api_key)
    qdrant = QdrantClient(url=args.qdrant_url)

    # Read input
    items = read_input_csv(args.csv_file)
    print(f"Loaded {len(items)} work items from {args.csv_file}\n")

    # Build BOQ
    boq_rows = []
    total = 0.0

    print(f"{'No.':<5} {'Description':<45} {'Unit':<6} {'Qty':>8} {'Rate':>12} {'Amount':>14}")
    print("-" * 95)

    for i, item in enumerate(items, 1):
        match = search_rate(openai_client, qdrant, args.collection, item["description"])

        if match:
            rate_code = match.get("rate_code", "")
            rate_name = match.get("rate_original_name", item["description"])
            unit_rate = float(match.get("total_cost_per_position", 0))
            matched_unit = match.get("rate_unit", item["unit"])
        else:
            rate_code = ""
            rate_name = item["description"]
            unit_rate = 0.0
            matched_unit = item["unit"]

        amount = unit_rate * item["quantity"]
        total += amount

        print(f"{i:<5} {rate_name[:45]:<45} {item['unit']:<6} {item['quantity']:>8.2f} {unit_rate:>12,.2f} {amount:>14,.2f}")

        boq_rows.append({
            "Item No.": i,
            "Rate Code": rate_code,
            "Description": rate_name,
            "Unit": matched_unit,
            "Quantity": item["quantity"],
            "Rate (EUR)": round(unit_rate, 2),
            "Amount (EUR)": round(amount, 2),
        })

    print("-" * 95)
    print(f"{'':>76} {'TOTAL':>6} {total:>14,.2f} EUR")

    # Add total row
    boq_rows.append({
        "Item No.": "",
        "Rate Code": "",
        "Description": "TOTAL",
        "Unit": "",
        "Quantity": "",
        "Rate (EUR)": "",
        "Amount (EUR)": round(total, 2),
    })

    # Export to Excel
    df = pd.DataFrame(boq_rows)
    df.to_excel(args.output, index=False, sheet_name="BOQ")
    print(f"\nBOQ exported to: {args.output}")


if __name__ == "__main__":
    main()
