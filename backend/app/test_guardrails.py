from guardrails import check_retrieval_confidence


good_results = [
    {
        "text": "Paris is the capital of France.",
        "source": "doc_001",
        "score": 0.94
    },
    {
        "text": "Paris lies along the Seine River.",
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


empty_results = []


print("GOOD RESULTS:")
print(check_retrieval_confidence(good_results))

print("\nBAD RESULTS:")
print(check_retrieval_confidence(bad_results))

print("\nEMPTY RESULTS:")
print(check_retrieval_confidence(empty_results))