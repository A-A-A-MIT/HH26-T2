from grounding import check_grounding


context = """
Paris is the capital and largest city of France.
It is located along the Seine River.
"""


answers = [
    "Paris is the capital of France.",
    "Paris has a population of 2 million people.",
    "The Seine River is located in Paris."
]


for answer in answers:

    grounded, score = check_grounding(
        answer,
        retrieved_chunks
    )

    print("\nANSWER:")
    print(answer)

    print("GROUNDED:", grounded)
    print("OVERLAP SCORE:", round(score, 2))