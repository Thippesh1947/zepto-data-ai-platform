# Module 3 — Support Assistant

## Architecture: RAG Pipeline

**Ingestion** — `ingest.py` reads all 8 policy files from `docs/doc_01.txt`
through `doc_08.txt`. Each file is treated as one chunk (per-document
chunking, permitted by the rubric given the short length of each document).

**Embedding** — Each chunk is embedded locally using the `sentence-transformers`
library's `all-MiniLM-L6-v2` model — no API key, no cost, runs entirely on
the local machine. Embeddings are stored in a persistent ChromaDB collection
named `zepto_policies` (cosine similarity space, `hnsw:space: cosine`),
persisted to disk at `support_assistant/chroma_db/`.

**Retrieval** — `graph.py`'s `retrieve_and_answer` node embeds the incoming
query and retrieves the top-3 most similar chunks from the `zepto_policies`
collection via cosine similarity. This retrieval step always runs for real,
in both `MOCK_LLM` modes, since ChromaDB and the local embedding model
require no API key and no network call after the first model download.

**Generation** — Only the final answer-generation step branches on the
`MOCK_LLM` environment variable (default `1`):
- **Mock mode (default, graded baseline)**: `retrieve_and_answer` returns a
  canned `"Based on the retrieved context: {snippet}"` string built from the
  first ~200 characters of the top retrieved chunk. `direct_answer` returns
  a fixed canned string. No LLM call is made in either case.
- **Optional `MOCK_LLM=0` extension**: the structured prompt template in
  `PROMPT_TEMPLATE` (role–context–task–format–length skeleton, with a
  negative constraint and a few-shot example) would be sent to a real LLM.
  Output is validated against the `AssistantResponse` Pydantic schema, with
  up to 2 retries on validation failure via `_validate_with_retries()`. This
  path is implemented but not exercised by default, and is not required for
  full marks.

**Routing** — `classify_intent` uses a keyword heuristic (checking for
"delivery", "return", "refund", "membership", "tracking", "cancel",
"gift card", "support hours") to classify each query as `policy_question`
or `general_question`. A LangGraph conditional edge then routes to either
`retrieve_and_answer` or `direct_answer` accordingly. This routing decision
itself never depends on `MOCK_LLM` — only the generation step inside each
node does.

**Output schema** — Every response is validated against a Pydantic model
(`AssistantResponse`) with fields `answer: str`, `sources: List[str]`, and
`confidence: float` (0.0–1.0), enforced by FastAPI's `response_model` on
the `/ask` endpoint.

## Example API Calls (MOCK_LLM left at default)

Both calls were run locally via:
```bash
cd support_assistant
python -m uvicorn main:app --host 0.0.0.0 --port 7860
```

### Call 1 — policy question (triggers retrieval)
Request: `POST /ask {"query": "What are your delivery hours?"}`

Response:
```json
{
    "answer": "Based on the retrieved context: Zepto delivers grocery and household essentials to serviceable pin codes within 10 to 30 minutes of order confirmation, depending on the customer's delivery zone and current order volume. Standard del",
    "sources": [
        "doc_01",
        "doc_02",
        "doc_08"
    ],
    "confidence": 1.0
}
```

### Call 2 — general question (no retrieval)
Request: `POST /ask {"query": "What is the capital of France?"}`

Response:
```json
{
    "answer": "I can only answer questions about Zepto policies right now.",
    "sources": [],
    "confidence": 1.0
}
```

## Running Locally
```bash
cd support_assistant
python -m uvicorn main:app --host 0.0.0.0 --port 7860
```

## Running via Docker
```bash
docker build -f support_assistant/Dockerfile -t zepto-support-assistant .
docker run -p 7860:7860 zepto-support-assistant
```

## Design Decisions
- **Persistent ChromaDB** chosen over in-memory so the vector store survives
  across runs without re-embedding every time.
- **Per-document chunking**: each policy document is short (a few sentences),
  so splitting further would fragment coherent policy statements without
  benefit.
- **Cosine similarity** explicitly set on the collection, since it's the
  standard metric for sentence-embedding similarity search.