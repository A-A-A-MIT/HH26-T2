import os
import time
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env")

client = Groq(api_key=api_key)

question = "What is the capital of France?"

retrieved_context = """
Paris is the capital and largest city of France.
It is located along the Seine River.
Paris is one of the major cultural and political centers of Europe.
"""

system_prompt = """
You are the answer-generation component of a Retrieval-Augmented
Generation (RAG) system.

Answer the user's question using ONLY the retrieved context.

If the context does not contain enough information to answer the question,
say that you do not have enough information.

Do not use outside knowledge.
Do not invent facts.
"""

start = time.perf_counter()

response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": f"""
USER QUESTION:
{question}

RETRIEVED CONTEXT:
{retrieved_context}
"""
        }
    ],
    temperature=0,
    max_tokens=100
)

end = time.perf_counter()

print(f"Groq latency: {(end - start) * 1000:.2f} ms")

print("\nQUESTION:")
print(question)

print("\nANSWER:")
print(response.choices[0].message.content)