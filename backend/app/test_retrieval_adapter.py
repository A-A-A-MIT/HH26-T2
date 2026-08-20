from retrieval_adapter import adapt_retrieval_results


person_b_results = [
    {
        "score": 0.94,
        "sentence": "Paris is the capital of France.",
        "window_text": "Paris is the capital and largest city of France.",
        "doc_id": "doc_001",
    },
    {
        "score": 0.88,
        "sentence": "The Seine is a river in France.",
        "window_text": "The Seine River runs through Paris.",
        "doc_id": "doc_002",
    },
    {
        "score": 0.82,
        "sentence": "Paris is the capital of France.",
        "doc_id": "doc_003",
    },
]


adapted_results = adapt_retrieval_results(
    person_b_results
)


print("ADAPTED RESULTS:")

for result in adapted_results:
    print(result)