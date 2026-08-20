from retrieve import retrieve_context
from retrieval_adapter import adapt_retrieval_results
from pipeline import run_pipeline


questions = [
    "What are the symptoms of diabetes?",
    "What causes high blood pressure?",
    "What is the capital of France?",
]


for question in questions:

    print("\n" + "=" * 60)
    print("QUESTION:")
    print(question)

    # 1. Real retrieval
    raw_results = retrieve_context(
        question,
        k=5
    )

    print(f"\nRETRIEVED: {len(raw_results)} chunks")

    for i, result in enumerate(raw_results, 1):
        print(
            f"[{i}] "
            f"score={result['score']:.4f} "
            f"source={result['source_id']}"
        )

    # 2. Adapt retrieval output
    retrieved_chunks = adapt_retrieval_results(
        raw_results
    )
    print("\n========== RETRIEVED TEXT ==========")

for i, chunk in enumerate(retrieved_chunks, 1):
    print(f"\n--- CHUNK {i} ---")
    print(chunk["text"])
    # 3. Run complete pipeline
    result = run_pipeline(
        question=question,
        retrieved_chunks=retrieved_chunks
    )

    print("\nRESULT:")
    print(result)