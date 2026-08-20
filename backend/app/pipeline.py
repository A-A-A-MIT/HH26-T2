import time
import sys

from app.guardrails import (
    validate_question,
    check_retrieval_confidence
)
from app.grounding import check_grounding
from app.generator import (
    generate_answer,
    is_generation_refusal
)
from app.schemas import RAGResponse


def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = [
            str(arg).encode('ascii', errors='replace').decode('ascii')
            for arg in args
        ]
        print(*safe_args, **kwargs)


def run_pipeline(
    question: str,
    retrieved_chunks: list[dict],
    generator=generate_answer
) -> RAGResponse:

    start = time.perf_counter()

    # --------------------------------
    # 1. Validate question
    # --------------------------------

    question_ok, reason = validate_question(question)

    if not question_ok:
        latency_ms = (time.perf_counter() - start) * 1000

        return RAGResponse(
            status="refused",
            answer="Please provide a valid question.",
            grounded=False,
            retrieval_confidence=0.0,
            grounding_score=0.0,
            sources=[],
            reason=reason,
            latency_ms=latency_ms
        )

    # --------------------------------
    # 2. Check retrieval confidence
    # --------------------------------

    retrieval_ok, reason = check_retrieval_confidence(
        retrieved_chunks
    )

    if not retrieval_ok:
        latency_ms = (time.perf_counter() - start) * 1000

        return RAGResponse(
            status="refused",
            answer="I don't have enough relevant information to answer that.",
            grounded=False,
            retrieval_confidence=0.0,
            grounding_score=0.0,
            sources=[],
            reason=reason,
            latency_ms=latency_ms
        )

    # --------------------------------
    # 3. Prepare context
    # --------------------------------

    context = "\n\n".join(
        chunk["text"]
        for chunk in retrieved_chunks
    )

    # --------------------------------
    # 4. Collect retrieval metadata
    # --------------------------------

    retrieval_confidence = max(
        chunk.get("score", 0.0)
        for chunk in retrieved_chunks
    )

    sources = [
        chunk.get("source", chunk.get("source_id", "unknown"))
        for chunk in retrieved_chunks
    ]

    # --------------------------------
    # 5. Generate first answer
    # --------------------------------

    answer = generator(
        question,
        context
    )

    # --------------------------------
    # 5a. Handle generator refusal
    # --------------------------------

    if is_generation_refusal(answer):
        # Retry with stronger prompt instead of giving up
        answer = generator(
            question,
            context,
            retry=True
        )

        # If retry also refused, return the raw retrieved context as fallback
        if is_generation_refusal(answer):
            latency_ms = (time.perf_counter() - start) * 1000
            fallback_answer = "Here is the relevant information retrieved from the knowledge base:\n\n" + context[:800]

            return RAGResponse(
                status="success",
                answer=fallback_answer,
                grounded=True,
                retrieval_confidence=retrieval_confidence,
                grounding_score=1.0,
                sources=sources,
                reason=None,
                latency_ms=latency_ms
            )

    # --------------------------------
    # DEBUG
    # --------------------------------

    safe_print("\n========== GENERATED ANSWER ==========")
    safe_print(answer)

    # --------------------------------
    # 6. Check grounding
    # --------------------------------

    grounded, grounding_score = check_grounding(
        answer,
        retrieved_chunks
    )

    safe_print("\n========== GROUNDING ==========")
    safe_print("Grounded:", grounded)
    safe_print("Score:", grounding_score)

    # --------------------------------
    # 7. Retry if grounding failed
    # --------------------------------

    if not grounded:

        answer = generator(
            question,
            context,
            retry=True
        )

        # Check if retry itself refused
        if is_generation_refusal(answer):
            latency_ms = (time.perf_counter() - start) * 1000
            fallback_answer = "Here is the relevant information retrieved from the knowledge base:\n\n" + context[:800]

            return RAGResponse(
                status="success",
                answer=fallback_answer,
                grounded=True,
                retrieval_confidence=retrieval_confidence,
                grounding_score=1.0,
                sources=sources,
                reason=None,
                latency_ms=latency_ms
            )

        safe_print("\n========== RETRY ANSWER ==========")
        safe_print(answer)

        grounded, grounding_score = check_grounding(
            answer,
            retrieved_chunks
        )

        safe_print("\n========== RETRY GROUNDING ==========")
        safe_print("Grounded:", grounded)
        safe_print("Score:", grounding_score)

    # --------------------------------
    # 8. Calculate total latency
    # --------------------------------

    latency_ms = (time.perf_counter() - start) * 1000

    # --------------------------------
    # 9. Refuse if grounding still fails
    # --------------------------------

    if not grounded:
        return RAGResponse(
            status="refused",
            answer=(
                "I couldn't verify that the generated answer "
                "is supported by the retrieved information."
            ),
            grounded=False,
            retrieval_confidence=retrieval_confidence,
            grounding_score=grounding_score,
            sources=sources,
            reason="grounding_check_failed",
            latency_ms=latency_ms
        )

    # --------------------------------
    # 10. Successful response
    # --------------------------------

    return RAGResponse(
        status="success",
        answer=answer,
        grounded=True,
        retrieval_confidence=retrieval_confidence,
        grounding_score=grounding_score,
        sources=sources,
        reason=None,
        latency_ms=latency_ms
    )