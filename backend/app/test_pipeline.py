from pipeline import run_pipeline


good_results = [
    {
        "text": "Paris is the capital and largest city of France.",
        "source": "doc_001",
        "score": 0.94
    },
    {
        "text": "Paris is located along the Seine River.",
        "source": "doc_002",
        "score": 0.88
    }
]


bad_results = [
    {
        "text": "The Seine is a river.",
        "source": "doc_893",
        "score": 0.31
    }
]


print("========== GOOD RETRIEVAL ==========")

result = run_pipeline(
    "What is the capital of France?",
    good_results
)

print(result)


print("\n========== BAD RETRIEVAL ==========")

result = run_pipeline(
    "What is the capital of France?",
    bad_results
)

print(result)

print("\n========== EMPTY QUESTION ==========")

result = run_pipeline(
    "",
    good_results
)

print(result)


print("\n========== INVALID QUESTION ==========")

result = run_pipeline(
    "?",
    good_results
)

print(result)