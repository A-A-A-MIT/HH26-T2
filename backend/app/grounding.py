import re
from fastembed import TextEmbedding
from fastembed.common.model_description import PoolingType, ModelSource

MODEL_NAME = "intfloat/multilingual-e5-small"

# Lightweight ONNX embedding model (same model as retrieve.py, ~10ms execution time)
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

embedding_model = TextEmbedding(model_name=MODEL_NAME)


def normalize_text(text: str) -> set[str]:
    # Support Unicode / Indic / Devanagari word extraction
    words = re.findall(
        r"\w+",
        text.lower(),
        flags=re.UNICODE
    )
    return set(words)


def lexical_overlap(
    answer: str,
    context: str
) -> float:

    answer_words = normalize_text(answer)
    context_words = normalize_text(context)

    if not answer_words:
        return 0.0

    overlap = answer_words.intersection(context_words)

    return len(overlap) / len(answer_words)


def split_sentences(text: str) -> list[str]:
    """
    Split generated answer into individual claims/sentences.
    """

    sentences = re.split(
        r"(?<=[.!?|।])\s+",
        text.strip()
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def semantic_similarity(
    answer: str,
    context: str
) -> float:

    # Use FastEmbed (ONNX) for sub-15ms execution instead of PyTorch SentenceTransformer
    embs = list(embedding_model.embed([
        f"query: {answer}",
        f"passage: {context}"
    ]))

    answer_vector = embs[0]
    context_vector = embs[1]

    return float(answer_vector @ context_vector)


def check_grounding(
    answer: str,
    retrieved_chunks: list[dict],
    min_overlap: float = 0.25,
    min_semantic_similarity: float = 0.50
) -> tuple[bool, float]:

    if not answer.strip():
        return False, 0.0

    if not retrieved_chunks:
        return False, 0.0

    # --------------------------------
    # 1. Split answer into claims
    # --------------------------------

    claims = split_sentences(answer)

    if not claims:
        return False, 0.0

    claim_scores = []

    # --------------------------------
    # 2. Check every claim
    # --------------------------------

    for claim in claims:

        best_score = 0.0
        claim_supported = False

        for chunk in retrieved_chunks:

            chunk_text = chunk.get("text", "")

            if not chunk_text.strip():
                continue

            # ----------------------------
            # Lexical evidence
            # ----------------------------

            overlap_score = lexical_overlap(
                claim,
                chunk_text
            )

            if overlap_score >= min_overlap:
                claim_supported = True
                best_score = max(
                    best_score,
                    overlap_score
                )
                continue

            # ----------------------------
            # Multilingual semantic evidence
            # ----------------------------

            semantic_score = semantic_similarity(
                claim,
                chunk_text
            )

            best_score = max(
                best_score,
                semantic_score
            )

            if semantic_score >= min_semantic_similarity:
                claim_supported = True

        # --------------------------------
        # Claim has no supporting evidence
        # --------------------------------

        if not claim_supported:
            return False, best_score

        claim_scores.append(best_score)

    # --------------------------------
    # 3. Overall grounding score
    # --------------------------------

    grounding_score = min(claim_scores) if claim_scores else 0.0

    return True, grounding_score