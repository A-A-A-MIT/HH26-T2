import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env")


response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    json={
        "model": "openai/gpt-oss-20b",
        "messages": [
            {
                "role": "user",
                "content": "Say hello in one short sentence."
            }
        ],
        "temperature": 0,
        "max_tokens": 20,
    },
    timeout=30,
)


print("========== HTTP STATUS ==========")
print(response.status_code)

print("\n========== GROQ REGION ==========")
print(response.headers.get("x-groq-region"))

print("\n========== CF-RAY ==========")
print(response.headers.get("cf-ray"))

print("\n========== ALL RELEVANT HEADERS ==========")

for key, value in response.headers.items():
    if (
        "groq" in key.lower()
        or "ray" in key.lower()
        or "colo" in key.lower()
    ):
        print(f"{key}: {value}")

print("\n========== RESPONSE BODY ==========")
print(response.text)