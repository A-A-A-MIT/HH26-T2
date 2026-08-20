from grounding import check_grounding


context = """
Paris is the capital and largest city of France.
It is located along the Seine River.
"""


# Simulate what the generator might return.
bad_answer = "Paris has a population of 2 million people."

good_answer = "Paris is the capital of France."


print("FIRST ATTEMPT:")

grounded, score = check_grounding(
    bad_answer,
    context
)

print("Answer:", bad_answer)
print("Grounded:", grounded)
print("Score:", score)


print("\nRETRY ATTEMPT:")

grounded, score = check_grounding(
    good_answer,
    context
)

print("Answer:", good_answer)
print("Grounded:", grounded)
print("Score:", score)