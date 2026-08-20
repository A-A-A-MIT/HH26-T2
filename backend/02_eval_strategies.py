"""
Compares chunking strategies using recall@5 and MRR against ground truth.
Measures retrieval performance (Recall@K, MRR) and search latency (P50, P70, P100).
Saves outputs to chunking_eval_results.json for submission reporting.
"""

import json
import os
import time
import numpy as np
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import torch
from tqdm import tqdm

from dataset_utils import load_train_df

# ---------------------------------------------------------------------------
# CONFIG — Harmonized with 01_build_indexes.py
# ---------------------------------------------------------------------------
QUERY_FIELD = "query"
QUERY_ID_FIELD = "query_id"
PASSAGES_FIELD = "passages"

SUBSET_SIZE = None

QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "https://364811d7-4171-4f47-85f9-2497e2e6c805.us-east-1-1.aws.cloud.qdrant.io",
)
QDRANT_API_KEY = os.getenv(
    "QDRANT_API_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6YTUyYzAyZDYtZDNiNC00NzBmLWI4M2MtNGUzOWRiYzU5ZGY3In0.b_4-okDtMYnVYTthdqpCNq1KbkSNxM5KGkWlDuSWJ48",
)

EMBED_MODEL_NAME = "intfloat/multilingual-e5-small"
N_EVAL_QUERIES = 50
K = 5

STRATEGIES = ["sentence_window", "fixed_256", "fixed_128", "semantic"]


def search(query: str, collection: str, embed_model, client, device, k: int = K):
    """Executes dense vector search on Qdrant collection using query_points."""
    q_vec = embed_model.encode(
        f"query: {query}", normalize_embeddings=True, device=device
    ).tolist()

    response = client.query_points(
        collection_name=collection, query=q_vec, limit=k
    )
    return response.points


def evaluate_strategy(collection: str, eval_pairs, embed_model, client, device):
    """Evaluates Recall@K, MRR, and search latencies (P50, P70, P100)."""
    if not client.collection_exists(collection_name=collection):
        print(f"\n⚠️ Collection '{collection}' does not exist in Qdrant. Skipping...")
        return None

    recall_hits = 0
    reciprocal_ranks = []
    latencies_ms = []

    for pair in tqdm(eval_pairs, desc=f"Evaluating {collection}"):
        start_time = time.perf_counter()

        hits = search(pair["query"], collection, embed_model, client, device, k=K)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        latencies_ms.append(elapsed_ms)

        source_ids = [
            h.payload.get("source_id") or h.payload.get("doc_id") for h in hits
        ]

        rank = None
        for i, sid in enumerate(source_ids):
            if sid in pair["correct_source_ids"]:
                rank = i + 1
                break

        if rank is not None:
            recall_hits += 1
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)

    recall_at_k = recall_hits / len(eval_pairs) if eval_pairs else 0.0
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0

    p50 = np.percentile(latencies_ms, 50) if latencies_ms else 0.0
    p70 = np.percentile(latencies_ms, 70) if latencies_ms else 0.0
    p100 = np.percentile(latencies_ms, 100) if latencies_ms else 0.0

    return recall_at_k, mrr, p50, p70, p100


# ---------------------------------------------------------------------------
# EXECUTION PIPELINE
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🚀 Using compute device for queries: {device.upper()}")

    print("Loading dataset for strategy evaluation...")
    df = load_train_df()
    if SUBSET_SIZE is not None:
        df = df.iloc[:SUBSET_SIZE]

    eval_pairs = []
    sample = df.iloc[: min(N_EVAL_QUERIES, len(df))]

    for _, row in sample.iterrows():
        query_id = row[QUERY_ID_FIELD]
        q = row.get(QUERY_FIELD)
        passages = row[PASSAGES_FIELD]
        if not q or not isinstance(passages, dict):
            continue

        sel_list = passages.get("is_selected") or []
        correct_source_ids = {
            f"{query_id}_{idx}" for idx, sel in enumerate(sel_list) if int(sel) == 1
        }
        if not correct_source_ids:
            continue

        eval_pairs.append({"query": q, "correct_source_ids": correct_source_ids})

    print(
        f"Evaluating on {len(eval_pairs)} query/passage pairs "
        f"(sampled {len(sample)} rows, kept ones with >=1 selected passage)."
    )

    print(f"Loading embedding model ({EMBED_MODEL_NAME})...")
    embed_model = SentenceTransformer(EMBED_MODEL_NAME, device=device)
    if device == "cuda":
        embed_model.half()

    print("Connecting to Qdrant...")
    if QDRANT_URL == ":memory:":
        client = QdrantClient(":memory:")
    else:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60)

    print(
        f"\n{'Strategy':<18} {'Recall@' + str(K):<10} {'MRR':<8} {'P50 (ms)':<10} {'P70 (ms)':<10} {'P100 (ms)':<10}"
    )
    print("-" * 70)

    results = {}
    for strat in STRATEGIES:
        eval_res = evaluate_strategy(strat, eval_pairs, embed_model, client, device)
        if eval_res is None:
            continue

        recall, mrr, p50, p70, p100 = eval_res
        results[strat] = {
            "recall": recall,
            "mrr": mrr,
            "p50_ms": round(float(p50), 2),
            "p70_ms": round(float(p70), 2),
            "p100_ms": round(float(p100), 2),
        }
        print(
            f"{strat:<18} {recall:<10.3f} {mrr:<8.3f} {p50:<10.2f} {p70:<10.2f} {p100:<10.2f}"
        )

    if results:
        best = max(results, key=lambda s: results[s]["mrr"])
        print(f"\n>>> Best strategy by MRR: {best}")
        print(f">>> Set strategy='{best}' in your retrieve.py module.")

        with open("chunking_eval_results.json", "w") as f:
            json.dump(results, f, indent=2)

        print("\nSaved evaluation results to chunking_eval_results.json")
    else:
        print("\n⚠️ No existing collections were evaluated. Run 01_build_indexes.py first.")

    client.close()