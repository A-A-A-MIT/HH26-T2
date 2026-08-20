MIN_RETRIEVAL_SCORE = 0.35
def validate_question(question: str) -> tuple[bool, str]:
    """
    Validate the basic structure of the user's question.
    """

    if not question or not question.strip():
        return False, "empty_question"

    if len(question.strip()) < 2:
        return False, "question_too_short"

    return True, "ok"

def check_retrieval_confidence(retrieved_chunks: list[dict]) -> tuple[bool, str]:
    """
    Decide whether the retrieved context is strong enough
    to send to the generation model.
    """

    if not retrieved_chunks:
        return False, "no_retrieved_context"

    best_score = max(
        chunk.get("score", 0.0)
        for chunk in retrieved_chunks
    )

    if best_score < MIN_RETRIEVAL_SCORE:
        return False, "insufficient_retrieval_confidence"

    return True, "ok"