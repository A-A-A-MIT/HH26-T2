import json
import os
import time
import numpy as np
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import torch
from tqdm import tqdm

# 1. Matching project configuration
EMBED_MODEL_NAME = "intfloat/multilingual-e5-small"
COLLECTION_NAME ="fixed_128"  # Strategy selected for low latency
N_QUERIES = 100
K = 5

QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "https://364811d7-4171-4f47-85f9-2497e2e6c805.us-east-1-1.aws.cloud.qdrant.io",
)
QDRANT_API_KEY = os.getenv(
    "QDRANT_API_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6YTUyYzAyZDYtZDNiNC00NzBmLWI4M2MtNGUzOWRiYzU5ZGY3In0.b_4-okDtMYnVYTthdqpCNq1KbkSNxM5KGkWlDuSWJ48",
)

if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🚀 Using compute device: {device.upper()}")

    embed_model = SentenceTransformer(EMBED_MODEL_NAME, device=device)
    if device == "cuda":
        embed_model.half()

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60)

    test_queries = [
        "what are symptoms of diabetes",
        "how does photosynthesis work",
        "capital of india",
        "causes of climate change",
        "how to treat a fever",
        "history of the taj mahal",
        "benefits of exercise",
        "what is machine learning",
        "how do vaccines work",
        "population of mumbai",
    ] * (N_QUERIES // 10 + 1)
    test_queries = test_queries[:N_QUERIES]

    def timed_search(query):
        t0 = time.perf_counter()
        q_vec = embed_model.encode(
            f"query: {query}", normalize_embeddings=True, device=device
        ).tolist()
        t_embed = time.perf_counter()

        hits = client.query_points(
            collection_name=COLLECTION_NAME,
            query=q_vec,
            limit=K,
            with_vectors=False,
            with_payload=["window_text"],
        )
        t_search = time.perf_counter()

        return {
            "embed_ms": (t_embed - t0) * 1000.0,
            "search_ms": (t_search - t_embed) * 1000.0,
            "total_ms": (t_search - t0) * 1000.0,
        }

    print(f"Running {N_QUERIES} test queries against '{COLLECTION_NAME}'...")
    results = [timed_search(q) for q in tqdm(test_queries)]

    for stage in ["embed_ms", "search_ms", "total_ms"]:
        vals = [r[stage] for r in results]
        p50 = np.percentile(vals, 50)
        p70 = np.percentile(vals, 70)
        p100 = np.percentile(vals, 100)
        print(f"\n{stage}:")
        print(f"  P50:  {p50:.2f} ms")
        print(f"  P70:  {p70:.2f} ms")
        print(f"  P100: {p100:.2f} ms")

    summary = {
        stage: {
            "p50": float(np.percentile([r[stage] for r in results], 50)),
            "p70": float(np.percentile([r[stage] for r in results], 70)),
            "p100": float(np.percentile([r[stage] for r in results], 100)),
        }
        for stage in ["embed_ms", "search_ms", "total_ms"]
    }

    with open("latency_results.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\nSaved output to latency_results.json")
    client.close()