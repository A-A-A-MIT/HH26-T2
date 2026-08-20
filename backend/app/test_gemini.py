import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)

question = "What is the capital of France?"

retrieved_context = """
Paris is the capital and largest city of France.
It is located along the Seine River.
Paris is one of the major cultural and political centers of Europe.
"""

prompt = f"""
You are the answer-generation component of a Retrieval-Augmented
Generation (RAG) system.

Answer the user's question using ONLY the retrieved context below.

If the context does not contain enough information to answer the question,
say that you do not have enough information.

Do not use outside knowledge.
Do not invent facts.

USER QUESTION:
{question}

RETRIEVED CONTEXT:
{retrieved_context}

ANSWER:
"""

import time

start = time.perf_counter()

response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=prompt
)

end = time.perf_counter()

print(f"\nGemini latency: {(end - start) * 1000:.2f} ms")

print("QUESTION:")
print(question)

print("\nANSWER:")
print(response.text)