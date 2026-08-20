import json
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.retrieve import retrieve_context, prewarm_semantic_cache
from app.retrieval_adapter import adapt_retrieval_results
from app.pipeline import run_pipeline
from app.generator import generate_answer_stream
from app.grounding import check_grounding

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def warmup():
    try:
        print("[Startup] Warming up Qdrant connection and FastEmbed ONNX model...")
        prewarm_semantic_cache()
        print("[Startup] Warmup complete ✅ All domain vectors cached locally!")
    except Exception as e:
        print(f"[Startup Warmup Warning]: {e}")


class AskRequest(BaseModel):
    question: str


@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/ask")
def ask(request: AskRequest):
    t_start = time.perf_counter()

    t_ret_start = time.perf_counter()
    retrieved = retrieve_context(request.question, k=2)
    t_ret_end = time.perf_counter()
    retrieval_ms = round((t_ret_end - t_ret_start) * 1000, 2)

    chunks = adapt_retrieval_results(retrieved)

    t_gen_start = time.perf_counter()
    result = run_pipeline(
        request.question,
        chunks
    )
    t_gen_end = time.perf_counter()
    generation_pipeline_ms = round((t_gen_end - t_gen_start) * 1000, 2)
    server_total_ms = round((t_gen_end - t_start) * 1000, 2)

    return {
        "status": result.status,
        "answer": result.answer,
        "grounded": result.grounded,
        "retrieval_confidence": result.retrieval_confidence,
        "grounding_score": result.grounding_score,
        "sources": result.sources,
        "reason": result.reason,
        "latency_ms": result.latency_ms,
        "retrieval_ms": retrieval_ms,
        "generation_pipeline_ms": generation_pipeline_ms,
        "server_total_ms": server_total_ms,
    }


@app.post("/ask/stream")
def ask_stream(request: AskRequest):
    t_start = time.perf_counter()

    # Step 1: Ultra-fast Retrieval (k=2)
    t_ret_start = time.perf_counter()
    retrieved = retrieve_context(request.question, k=2)
    t_ret_end = time.perf_counter()
    retrieval_ms = round((t_ret_end - t_ret_start) * 1000, 2)

    chunks = adapt_retrieval_results(retrieved)

    retrieval_confidence = max(
        (chunk.get("score", 0.0) for chunk in chunks), default=0.0
    )
    sources = [
        chunk.get("source", chunk.get("source_id", "unknown"))
        for chunk in chunks
    ]
    context = "\n\n".join(chunk["text"] for chunk in chunks)

    # Step 2: Grounding validation check
    t_g_start = time.perf_counter()
    grounded, grounding_score = check_grounding(request.question, chunks)
    t_g_end = time.perf_counter()
    grounding_ms = round((t_g_end - t_g_start) * 1000, 2)

    def event_generator():
        # First event: Granular metadata (retrieval, grounding, sources, TTFT)
        meta = {
            "type": "metadata",
            "retrieval_ms": retrieval_ms,
            "retrieval_confidence": retrieval_confidence,
            "grounding_ms": grounding_ms,
            "grounding_score": grounding_score,
            "sources": sources,
            "ttft_ms": round((time.perf_counter() - t_start) * 1000, 2),
        }
        yield f"data: {json.dumps(meta)}\n\n"

        # Step 3: Stream tokens live as generated
        for token in generate_answer_stream(request.question, context):
            payload = {"type": "token", "content": token}
            yield f"data: {json.dumps(payload)}\n\n"

        # Final event: Complete signal
        total_ms = round((time.perf_counter() - t_start) * 1000, 2)
        done_payload = {"type": "done", "server_total_ms": total_ms}
        yield f"data: {json.dumps(done_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")