from guardrails import validate_question


questions = [
    "What is the capital of France?",
    "",
    "   ",
    "?"
]


for question in questions:

    valid, reason = validate_question(question)

    print("\nQUESTION:")
    print(repr(question))

    print("VALID:", valid)
    print("REASON:", reason)