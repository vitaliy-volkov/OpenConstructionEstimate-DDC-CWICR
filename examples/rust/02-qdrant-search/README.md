# 02 - Qdrant Search (Rust)

## Description

Connect to a Qdrant instance and perform a vector similarity search against
the DDC-CWICR construction cost collection. The example uses a pre-computed
sample embedding vector (or you can supply your own) to find the closest
matching construction rate items.

## Prerequisites

- Rust toolchain (1.75+)
- A running Qdrant instance (default: `http://localhost:6334` for gRPC)
- The `ddc_en_toronto` collection loaded with CWICR embeddings

## Usage

```bash
# From the examples/rust directory:
cargo run -p qdrant-search

# With a custom Qdrant URL:
QDRANT_URL=http://my-server:6334 cargo run -p qdrant-search
```

The example uses a hardcoded sample embedding vector for demonstration.
In production, you would call the OpenAI Embeddings API first to generate
the vector from a text query.
