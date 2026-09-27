from fastapi import FastAPI
from graph import app_graph, AssistantResponse
from pydantic import BaseModel

app = FastAPI(title="Zepto Support Assistant")


class AskRequest(BaseModel):
    query: str


@app.get("/")
def root():
    return {"status": "ok", "service": "Zepto Support Assistant"}


@app.post("/ask", response_model=AssistantResponse)
def ask(request: AskRequest) -> AssistantResponse:
    result = app_graph.invoke({"query": request.query})
    return AssistantResponse(
        answer=result["answer"],
        sources=result.get("sources", []),
        confidence=result.get("confidence", 1.0),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)