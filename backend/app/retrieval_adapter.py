def adapt_retrieval_results(results: list[dict]) -> list[dict]:
    """
    Convert Person B's retrieval output into
    the format expected by the Person C pipeline.
    """

    return [
        {
            "text": result.get("text", ""),
            "source": result.get("source_id", "unknown"),
            "score": float(result.get("score", 0.0)),
        }
        for result in results
    ]