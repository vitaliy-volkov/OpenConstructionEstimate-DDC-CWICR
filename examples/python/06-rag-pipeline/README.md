# 06 - RAG Pipeline

Retrieval-Augmented Generation (RAG) examples that combine Qdrant vector search with LLM generation to answer construction cost questions grounded in CWICR data.

## Scripts

| Script | Description |
|---|---|
| `rag_basic.py` | RAG pipeline using the Anthropic (Claude) SDK directly with Qdrant retrieval |
| `rag_langchain.py` | RAG pipeline using LangChain + OpenAI with a Qdrant-backed retriever |

## How It Works

1. User asks a natural-language question about construction costs.
2. The question is embedded using OpenAI `text-embedding-3-large`.
3. Qdrant returns the top-k most relevant CWICR work items.
4. Retrieved items are injected as context into the LLM prompt.
5. The LLM generates an answer grounded in the retrieved data.

## Prerequisites

```bash
pip install openai anthropic qdrant-client python-dotenv langchain langchain-openai langchain-qdrant
```

Create a `.env` file (or export the variables):

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
QDRANT_URL=https://your-qdrant-instance.cloud
QDRANT_API_KEY=your-qdrant-api-key
```

## Usage

```bash
python rag_basic.py --query "What is the cost of reinforced concrete foundation work?"
python rag_langchain.py --query "List the most expensive excavation items"
```
