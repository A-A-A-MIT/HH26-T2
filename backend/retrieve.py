"""
retrieve.py - Optimized Context Retrieval Module
"""

import os
from functools import lru_cache

import torch
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

load_dotenv()

# =========================================================
# Configuration
# =========================================================

COLLECTION_NAME = "fixed_128"
MODEL_NAME = "intfloat/multilingual-e5-small"
DEFAULT_K = 3

QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "https://364811d7-4171-4f47-85f9-2497e2e6c805.us-east-1-1.aws.cloud.qdrant.io",
)

QDRANT_API_KEY = os.getenv(
    "QDRANT_API_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6YTUyYzAyZDYtZDNiNC00NzBmLWI4M2MtNGUzOWRiYzU5ZGY3In0.b_4-okDtMYnVYTthdqpCNq1KbkSNxM5KGkWlDuSWJ48",
)

# =========================================================
# Model Initialization
# =========================================================

device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading embedding model on {device}...")

embed_model = SentenceTransformer(
    MODEL_NAME,
    device=device,
)

if device == "cuda":
    embed_model.half()

# Warm up once
_ = embed_model.encode(
    "query: warmup",
    normalize_embeddings=True,
    device=device,
)

print("Embedding model loaded.")

# =========================================================
# Qdrant Client
# =========================================================

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    prefer_grpc=True,
    timeout=60,
)


# =========================================================
# Cached Query Embeddings
# =========================================================

@lru_cache(maxsize=1024)
def _get_query_embedding(query: str) -> list[float]:
    return embed_model.encode(
        f"query: {query}",
        normalize_embeddings=True,
        device=device,
    ).tolist()


# =========================================================
# Retrieval
# =========================================================

def retrieve_context(
    query: str,
    k: int = DEFAULT_K,
) -> list[dict]:
    """
    Retrieve top-k context passages from Qdrant.

    Returns:
        [
            {
                "text": "...",
                "source_id": "...",
                "score": 0.82
            }
        ]
    """

    q_vec = _get_query_embedding(query)

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=q_vec,
        limit=k,
        with_vectors=False,
        with_payload=["window_text", "source_id"],
        search_params=models.SearchParams(
            hnsw_ef=32,
        ),
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

    return results


def retrieve_text_only(
    query: str,
    k: int = DEFAULT_K,
) -> list[str]:
    """Return only retrieved text."""

    contexts = retrieve_context(query, k=k)

    return [
        context["text"]
        for context in contexts
    ]


def close_connection():
    """Close Qdrant connection."""

    client.close()


# =========================================================
# Local Test
# =========================================================

if __name__ == "__main__":
    try:
        test_q = "what are symptoms of diabetes"

        print(
            f"\nTesting retrieval for: '{test_q}'\n"
        )

        hits = retrieve_context(
            test_q,
            k=3,
        )

        for i, hit in enumerate(hits, 1):
            print(
                f"[{i}] "
                f"Score: {hit['score']:.4f} | "
                f"Source: {hit['source_id']}"
            )

            print(
                f"    Text: "
                f"{hit['text'][:120]}...\n"
            )

    finally:
        close_connection()