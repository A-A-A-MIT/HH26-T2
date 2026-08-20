from retrieval_adapter import adapt_retrieval_results
from pipeline import run_pipeline


# Mimics Person B's current retrieval output
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
]


# Convert Person B's format to Person C's format
retrieved_chunks = adapt_retrieval_results(
    person_b_results
)


# Run the complete Person C pipeline
result = run_pipeline(
    question="What is the capital of France?",
    retrieved_chunks=retrieved_chunks
)


print("========== END-TO-END TEST ==========")
print(result)