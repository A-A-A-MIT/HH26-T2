import os
import re
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer
import torch

from dataset_utils import load_train_df

# =========================================================
# 1. Configuration
# =========================================================
SUBSET_SIZE = 15000  # Safe subset size to keep all 4 collections under 4GB RAM
MODEL_NAME = "intfloat/multilingual-e5-small"
VECTOR_SIZE = 384
BATCH_SIZE = 512

STRATEGIES = ["fixed_256", "fixed_128", "semantic", "sentence_window"]

QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "https://364811d7-4171-4f47-85f9-2497e2e6c805.us-east-1-1.aws.cloud.qdrant.io",
)
QDRANT_API_KEY = os.getenv(
    "QDRANT_API_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6YTUyYzAyZDYtZDNiNC00NzBmLWI4M2MtNGUzOWRiYzU5ZGY3In0.b_4-okDtMYnVYTthdqpCNq1KbkSNxM5KGkWlDuSWJ48",
)

# =========================================================
# 2. Chunking Implementations
# =========================================================
sentence_regex = re.compile(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+")

def chunk_passage(source_id, passage_text, strategy):
    chunks = []
    
    if strategy == "fixed_256":
        words = passage_text.split()
        for i in range(0, len(words), 200):  # ~256 tokens with overlap
            chunk_str = " ".join(words[i : i + 256])
            if chunk_str.strip():
                chunks.append({"source_id": source_id, "text": chunk_str})

    elif strategy == "fixed_128":
        words = passage_text.split()
        for i in range(0, len(words), 100):  # ~128 tokens with overlap
            chunk_str = " ".join(words[i : i + 128])
            if chunk_str.strip():
                chunks.append({"source_id": source_id, "text": chunk_str})

    elif strategy == "semantic":
        paragraphs = [p.strip() for p in passage_text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [passage_text]
        for p in paragraphs:
            chunks.append({"source_id": source_id, "text": p})

    elif strategy == "sentence_window":
        sentences = [s.strip() for s in sentence_regex.split(passage_text) if s.strip()]
        if not sentences:
            sentences = [passage_text]
        for i, sentence in enumerate(sentences):
            start_idx = max(0, i - 1)
            end_idx = min(len(sentences), i + 2)
            window_text = " ".join(sentences[start_idx:end_idx])
            chunks.append({"source_id": source_id, "text": window_text, "sentence": sentence})

    return chunks

# =========================================================
# 3. Execution Pipeline
# =========================================================
if __name__ == "__main__":
    # Hardware acceleration setup
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🚀 Using compute device: {device.upper()}")

    embed_model = SentenceTransformer(MODEL_NAME, device=device)
    if device == "cuda":
        embed_model.half()
        print("⚡ FP16 Half-Precision enabled.")

    # Added timeout=60 to prevent network retry warnings
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60)

    print("Loading dataset...")
    df = load_train_df().iloc[:SUBSET_SIZE]

    # Pre-extract passages
    passages_data = []
    for _, row in df.iterrows():
        q_id = row.get("query_id")
        p_dict = row.get("passages")
        if not q_id or not isinstance(p_dict, dict):
            continue
            
        translated = p_dict.get("Translated_passages") or p_dict.get("English_passages") or []
        for p_idx, text in enumerate(translated):
            t_str = str(text).strip()
            if t_str:
                passages_data.append({"source_id": f"{q_id}_{p_idx}", "text": t_str})

    print(f"Extracted {len(passages_data)} ground-truth passage texts.")

    # Process and build each collection strategy
    for strat in STRATEGIES:
        print(f"\n=========================================")
        print(f"Building Strategy Collection: '{strat}'")
        print(f"=========================================")

        if client.collection_exists(strat):
            client.delete_collection(strat)

        client.create_collection(
            collection_name=strat,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            on_disk_payload=True,
        )

        strategy_chunks = []
        for item in passages_data:
            strategy_chunks.extend(chunk_passage(item["source_id"], item["text"], strat))

        total_chunks = len(strategy_chunks)
        print(f"Total chunks created for '{strat}': {total_chunks}")

        processed_count = 0
        for i in range(0, total_chunks, BATCH_SIZE):
            batch = strategy_chunks[i : i + BATCH_SIZE]
            texts_to_embed = [f"passage: {c['text']}" for c in batch]

            embeddings = embed_model.encode(
                texts_to_embed,
                batch_size=len(batch),
                show_progress_bar=False,
                convert_to_numpy=True,
                device=device,
            )

            points = []
            for idx_b, (chunk_data, vector) in enumerate(zip(batch, embeddings)):
                point_id = processed_count + idx_b + 1
                payload = {
                    "source_id": chunk_data["source_id"],
                    "window_text": chunk_data["text"],
                }
                if "sentence" in chunk_data:
                    payload["sentence"] = chunk_data["sentence"]

                points.append(
                    PointStruct(id=point_id, vector=vector.tolist(), payload=payload)
                )

            client.upload_points(
                collection_name=strat,
                points=points,
                batch_size=32,  # Reduced batch size eliminates network drops
                parallel=1,
            )
            processed_count += len(batch)

        print(f"Successfully uploaded collection: '{strat}'")

    print("\n All 4 Strategy Collections Indexed Successfully!")
    client.close()