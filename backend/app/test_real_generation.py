from retrieve import retrieve_context
from retrieval_adapter import adapt_retrieval_results
from generator import generate_answer


question = "What are the symptoms of diabetes?"

# Real retrieval
raw_results = retrieve_context(question, k=5)

# Adapt to our pipeline format
retrieved_chunks = adapt_retrieval_results(raw_results)

# Build context exactly like pipeline.py
context = "\n\n".join(
    chunk["text"]
    for chunk in retrieved_chunks
)

print("========== CONTEXT ==========")

for i, chunk in enumerate(retrieved_chunks, 1):
    print(f"\n--- CHUNK {i} ---")
    print(chunk["text"])


# Generate answer
answer = generate_answer(
    question,
    context
)

print("\n========== GENERATED ANSWER ==========")
print(answer)