from generator import generate_answer


question = "What is the capital of France?"

context = """
Paris is the capital and largest city of France.
It is located along the Seine River.
"""

answer = generate_answer(question, context)

print("ANSWER:")
print(answer)