import os
import re
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY", "")
client = Groq(api_key=api_key) if api_key else None

MODEL = "openai/gpt-oss-20b"


def generate_answer(
    question: str,
    retrieved_context: str,
    retry: bool = False
) -> str:
    global client
    if not client:
        api_key_check = os.getenv("GROQ_API_KEY", "")
        if api_key_check:
            client = Groq(api_key=api_key_check)
        else:
            if retrieved_context.strip():
                return f"Based on retrieved context:\n{retrieved_context[:500]}"
            return "I do not have enough information to answer."

    system_prompt = """
You are an intelligent Multilingual Voice RAG assistant.

Your task is to answer the user's question clearly, accurately, and completely using the RETRIEVED CONTEXT.

CRITICAL INSTRUCTIONS:
1. Complete every sentence cleanly. Never cut off mid-sentence.
2. Answer in the EXACT SAME LANGUAGE as the USER QUESTION (translate from context if needed).
3. State facts directly without apologies or refusals.
4. Keep the answer clear, informative, and complete (2-4 full sentences).
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"USER QUESTION:\n{question}\n\n"
                        f"RETRIEVED CONTEXT:\n{retrieved_context}"
                    )
                }
            ],
            temperature=0.1,
            max_tokens=250
        )

        answer = response.choices[0].message.content
        return answer.strip() if answer else ""
    except Exception as e:
        print(f"[Groq Generator Error]: {e}")
        if retrieved_context.strip():
            return f"Retrieved context summary:\n{retrieved_context[:500]}"
        return "I do not have enough information to answer."


def generate_answer_stream(
    question: str,
    retrieved_context: str
):
    global client
    if not client:
        api_key_check = os.getenv("GROQ_API_KEY", "")
        if api_key_check:
            client = Groq(api_key=api_key_check)
        else:
            if retrieved_context.strip():
                yield f"Based on retrieved context:\n{retrieved_context[:500]}"
            else:
                yield "I do not have enough information to answer."
            return

    system_prompt = """
You are an intelligent Multilingual Voice RAG assistant.

Your task is to answer the user's question clearly, accurately, and completely using the RETRIEVED CONTEXT.

CRITICAL INSTRUCTIONS:
1. Complete every sentence cleanly. Never cut off mid-sentence.
2. Answer in the EXACT SAME LANGUAGE as the USER QUESTION (translate from context if needed).
3. State facts directly without apologies or refusals.
4. Keep the answer clear, informative, and complete (2-4 full sentences).
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"USER QUESTION:\n{question}\n\n"
                        f"RETRIEVED CONTEXT:\n{retrieved_context}"
                    )
                }
            ],
            temperature=0.1,
            max_tokens=250,
            stream=True
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        print(f"[Groq Stream Error]: {e}")
        if retrieved_context.strip():
            yield f"Retrieved context summary:\n{retrieved_context[:500]}"
        else:
            yield "I do not have enough information to answer."


def is_generation_refusal(answer: str) -> bool:
    if not answer:
        return True

    normalized = answer.lower().strip()
    refusal_phrases = [
        "i don't have enough information",
        "i do not have enough information",
        "not enough information",
        "i can't provide",
        "i cannot provide",
        "i'm sorry",
        "unable to provide",
    ]
    return any(phrase in normalized for phrase in refusal_phrases)