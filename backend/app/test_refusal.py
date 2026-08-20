from retrieve import retrieve_context
from retrieval_adapter import adapt_retrieval_results
from pipeline import run_pipeline


questions = [
    "What is the capital of France?",
    "What is the population of Mars?",
    "Who won the 2026 FIFA World Cup?",
    "What is the recipe for chocolate cake?"
]


for question in questions:

    print("\n" + "=" * 70)
    print("QUESTION:")
    print(question)

    raw_results = retrieve_context(
        question,
        k=5
    )

    retrieved_chunks = adapt_retrieval_results(
        raw_results
    )

    print("\nTOP RETRIEVAL SCORES:")

    for i, result in enumerate(retrieved_chunks, 1):
        print(
            f"[{i}] "
            f"{result['score']:.4f} "
            f"{result['source']}"
        )

    result = run_pipeline(
        question,
        retrieved_chunks
    )

    print("\nFINAL:")
    print(result)