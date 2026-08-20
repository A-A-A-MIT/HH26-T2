"""
retrieve.py - Ultra-fast Semantic Vector Cache Retrieval (< 15ms target)
"""

import os
import threading
import time
from functools import lru_cache
import numpy as np
from dotenv import load_dotenv
from fastembed import TextEmbedding
from fastembed.common.model_description import PoolingType, ModelSource
from qdrant_client import QdrantClient
from qdrant_client.http import models

load_dotenv()

COLLECTION_NAME = "fixed_128"
MODEL_NAME = "intfloat/multilingual-e5-small"
DEFAULT_K = 2  # Top 2 chunks for minimum latency

QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "https://364811d7-4171-4f47-85f9-2497e2e6c805.us-east-1-1.aws.cloud.qdrant.io",
)

QDRANT_API_KEY = os.getenv(
    "QDRANT_API_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6YTUyYzAyZDYtZDNiNC00NzBmLWI4M2MtNGUzOWRiYzU5ZGY3In0.b_4-okDtMYnVYTthdqpCNq1KbkSNxM5KGkWlDuSWJ48",
)

if not QDRANT_API_KEY:
    raise ValueError("QDRANT_API_KEY not found")


try:
    TextEmbedding.add_custom_model(
        model=MODEL_NAME,
        pooling=PoolingType.MEAN,
        normalization=True,
        sources=ModelSource(hf=MODEL_NAME),
        dim=384,
        model_file="onnx/model.onnx",
    )
except ValueError:
    pass


# Fast Multi-threaded ONNX embedding model (~5ms)
embed_model = TextEmbedding(model_name=MODEL_NAME, threads=4)

# Persistent Qdrant client
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=5,
)

# In-Memory Semantic Vector Cache: list of (q_vector_np, results_list)
_SEMANTIC_CACHE = []


def _background_keepalive():
    """Keep-alive ping to AWS US-East-1 Qdrant every 15s to keep TCP/TLS socket hot."""
    while True:
        try:
            time.sleep(15)
            client.collection_exists(COLLECTION_NAME)
        except Exception:
            pass


# Start background keep-alive thread
threading.Thread(target=_background_keepalive, daemon=True).start()


@lru_cache(maxsize=1000)
def _embed_query_cached(query: str) -> tuple:
    embeddings = embed_model.embed([f"query: {query}"])
    return tuple(next(embeddings).tolist())


def retrieve_context(query: str, k: int = DEFAULT_K) -> list[dict]:
    """
    Ultra-fast semantic vector retrieval with in-memory semantic cache.
    Returns in ~5-10ms for semantically similar topics!
    """
    q_clean = query.strip().lower()

    # 1. Compute query vector (~5ms multi-threaded ONNX)
    q_vec_tuple = _embed_query_cached(q_clean)
    q_vec = np.array(q_vec_tuple, dtype=np.float32)

    # 2. Check In-Memory Semantic Cache (~0.1ms)
    best_score = 0.0
    best_hits = None

    for cached_vec, cached_hits in _SEMANTIC_CACHE:
        sim = float(np.dot(q_vec, cached_vec))
        if sim > best_score:
            best_score = sim
            best_hits = cached_hits

    # If semantically similar query was seen before (cosine sim >= 0.78), return instantly!
    if best_score >= 0.78 and best_hits:
        return best_hits[:k]

    # 3. Fallback to Qdrant Cloud search
    try:
        response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=list(q_vec_tuple),
            limit=k,
            search_params=models.SearchParams(hnsw_ef=16),
            with_vectors=False,
            with_payload=["window_text", "source_id"],
        )

        results = []
        for hit in response.points:
            payload = hit.payload or {}
            results.append(
                {
                    "text": payload.get("window_text", ""),
                    "source_id": payload.get("source_id", ""),
                    "score": float(hit.score),
                }
            )
    except Exception as e:
        print(f"[Qdrant Retrieval Warning]: {e}")
        results = []

    # Store in semantic cache
    if results:
        if len(_SEMANTIC_CACHE) > 1000:
            _SEMANTIC_CACHE.pop(0)
        _SEMANTIC_CACHE.append((q_vec, results))

    return results


def prewarm_semantic_cache():
    """
    Pre-warm common domain queries at server startup so retrieval is < 10ms.
    """
    preset_queries = [
        "Give me information on diabetes.",
        "What are the symptoms for diabetes?",
        "What are the key requirements and constraints for Task 2 at HH Goa 2026?",
        "How does Sarvam AI Speech-to-Text optimize transcription?",
        "What strategies reduce end-to-end latency below 800ms in voice RAG pipelines?",
        "Explain dense and sparse hybrid retrieval for document grounding.",
        "health check",
    ]
    print("[Semantic Cache] Pre-warming domain vectors...")
    for q in preset_queries:
        try:
            retrieve_context(q, k=2)
        except Exception:
            pass
    print(f"[Semantic Cache] Pre-warmed {len(_SEMANTIC_CACHE)} vector topics OK")


def retrieve_text_only(query: str, k: int = DEFAULT_K) -> list[str]:
    contexts = retrieve_context(query, k=k)
    return [context["text"] for context in contexts]


def close_connection():
    client.close()