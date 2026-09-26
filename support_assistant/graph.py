import os
import json
from typing import TypedDict, List

import chromadb
from chromadb.utils import embedding_functions
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, ValidationError, Field

# ---------------------------------------------------------------------------
# Task 4: Pydantic response schema
# ---------------------------------------------------------------------------
class AssistantResponse(BaseModel):
    answer: str
    sources: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)

# ---------------------------------------------------------------------------
# LangGraph state (TypedDict)
# ---------------------------------------------------------------------------
class AgentState(TypedDict):
    query: str
    intent: str
    retrieved_chunks: List[str]
    retrieved_ids: List[str]
    answer: str
    sources: List[str]
    confidence: float

# MOCK_LLM toggle: unset or "1" -> mock (graded baseline). "0" -> real LLM (optional extension)
MOCK_LLM = os.environ.get("MOCK_LLM", "1") == "1"

# ---------------------------------------------------------------------------
# Task 2: Structured prompt template (role-context-task-format-length,
# negative constraint, few-shot example) -- used by the optional MOCK_LLM=0 path
# ---------------------------------------------------------------------------
PROMPT_TEMPLATE = """ROLE: You are Zepto's official customer support assistant. You answer
customer questions about Zepto's delivery, returns, membership, tracking,
cancellation, damaged items, gift card, and support policies.

CONTEXT: The following are the most relevant policy excerpts retrieved for
this question:
{context}

TASK: Answer the customer's question using ONLY the information present in
the CONTEXT above.

CONSTRAINT (negative): Do not answer using any information that is not
explicitly present in the provided context. If the context does not
contain the answer, say so plainly rather than guessing.

FEW-SHOT EXAMPLE:
Q: "What are your delivery hours?"
A: "Zepto delivers grocery and household essentials within 10 to 30
minutes of order confirmation, depending on your delivery zone."

FORMAT: Return a direct, plain-language answer. Do not restate the
question. Do not use bullet points.

LENGTH: Keep the answer to 2-3 sentences.

QUESTION: {query}
ANSWER:"""

# ---------------------------------------------------------------------------
# ChromaDB connection -- retrieval always runs "for real" in both modes;
# only the generation step branches on MOCK_LLM
# ---------------------------------------------------------------------------
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DB_DIR = os.path.join(_BASE_DIR, "chroma_db")

_client = chromadb.PersistentClient(path=_DB_DIR)
_embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
_collection = _client.get_or_create_collection(
    name="zepto_policies",
    embedding_function=_embed_fn,
    metadata={"hnsw:space": "cosine"},
)

POLICY_KEYWORDS = [
    "delivery", "return", "refund", "membership",
    "tracking", "cancel", "gift card", "support hours",
]

# ---------------------------------------------------------------------------
# Optional MOCK_LLM=0 extension stub. Left unwired by default -- plug in a
# free-tier provider (e.g. Groq) here only if attempting the optional
# extension. Never hardcode an API key; read it from an environment variable.
# ---------------------------------------------------------------------------
def call_real_llm(prompt: str) -> str:
    raise NotImplementedError(
        "Real LLM call not configured. Leave MOCK_LLM unset (or =1) "
        "to use the graded mock baseline."
    )


def _validate_with_retries(raw_output_fn, max_retries: int = 2) -> AssistantResponse:
    """Retries up to max_retries times with a corrective instruction before
    giving up and returning a clearly marked error response. Only ever
    exercised in the optional MOCK_LLM=0 path."""
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            raw = raw_output_fn(corrective=attempt > 0, last_error=last_error)
            data = json.loads(raw)
            return AssistantResponse(**data)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = str(exc)
            continue
    return AssistantResponse(
        answer="[ERROR] Failed to produce a schema-valid response after retries.",
        sources=[], confidence=0.0,
    )


# ---------------------------------------------------------------------------
# Task 3: Node 1 -- classify_intent
# ---------------------------------------------------------------------------
def classify_intent(state: AgentState) -> AgentState:
    query_lower = state["query"].lower()
    if MOCK_LLM:
        is_policy = any(kw in query_lower for kw in POLICY_KEYWORDS)
        state["intent"] = "policy_question" if is_policy else "general_question"
    else:
        try:
            prompt = f"Classify this query as 'policy_question' or 'general_question': {state['query']}"
            state["intent"] = call_real_llm(prompt).strip().lower()
        except NotImplementedError:
            is_policy = any(kw in query_lower for kw in POLICY_KEYWORDS)
            state["intent"] = "policy_question" if is_policy else "general_question"
    return state


# ---------------------------------------------------------------------------
# Task 3: Node 2 -- retrieve_and_answer
# ---------------------------------------------------------------------------
def retrieve_and_answer(state: AgentState) -> AgentState:
    results = _collection.query(query_texts=[state["query"]], n_results=3)
    retrieved_docs = results["documents"][0]
    retrieved_ids = results["ids"][0]
    state["retrieved_chunks"] = retrieved_docs
    state["retrieved_ids"] = retrieved_ids

    top_chunk_snippet = (retrieved_docs[0] if retrieved_docs else "")[:200]

    if MOCK_LLM:
        state["answer"] = f"Based on the retrieved context: {top_chunk_snippet}"
        state["sources"] = retrieved_ids
        state["confidence"] = 1.0
    else:
        context = "\n\n".join(retrieved_docs)
        prompt = PROMPT_TEMPLATE.format(context=context, query=state["query"])

        def _raw_output_fn(corrective, last_error):
            p = prompt
            if corrective:
                p += f"\n\nPrevious output failed validation ({last_error}). Return ONLY valid JSON: {{'answer': str, 'sources': list[str], 'confidence': float}}."
            return call_real_llm(p)

        try:
            validated = _validate_with_retries(_raw_output_fn)
            state["answer"] = validated.answer
            state["sources"] = validated.sources or retrieved_ids
            state["confidence"] = validated.confidence
        except NotImplementedError:
            state["answer"] = f"Based on the retrieved context: {top_chunk_snippet}"
            state["sources"] = retrieved_ids
            state["confidence"] = 1.0
    return state


# ---------------------------------------------------------------------------
# Task 3: Node 3 -- direct_answer
# ---------------------------------------------------------------------------
def direct_answer(state: AgentState) -> AgentState:
    if MOCK_LLM:
        state["answer"] = "I can only answer questions about Zepto policies right now."
        state["sources"] = []
        state["confidence"] = 1.0
    else:
        try:
            state["answer"] = call_real_llm(f"Answer directly (no retrieval): {state['query']}")
        except NotImplementedError:
            state["answer"] = "I can only answer questions about Zepto policies right now."
        state["sources"] = []
        state["confidence"] = 1.0
    return state


def route_by_intent(state: AgentState) -> str:
    return state["intent"]


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("retrieve_and_answer", retrieve_and_answer)
    graph.add_node("direct_answer", direct_answer)
    graph.set_entry_point("classify_intent")
    graph.add_conditional_edges(
        "classify_intent", route_by_intent,
        {"policy_question": "retrieve_and_answer", "general_question": "direct_answer"},
    )
    graph.add_edge("retrieve_and_answer", END)
    graph.add_edge("direct_answer", END)
    return graph.compile()


app_graph = build_graph()


if __name__ == "__main__":
    print(f"=== Testing LangGraph (MOCK_LLM={'1/default' if MOCK_LLM else '0'}) ===\n")
    test_queries = [
        "What are your delivery hours?",   # should route to retrieve_and_answer
        "What's the capital of France?",   # should route to direct_answer
    ]
    for q in test_queries:
        result = app_graph.invoke({"query": q})
        response = AssistantResponse(
            answer=result["answer"], sources=result.get("sources", []),
            confidence=result.get("confidence", 1.0),
        )
        print(f"Query: {q}\nIntent: {result['intent']}")
        print(json.dumps(response.model_dump(), indent=2))
        print("-" * 60)