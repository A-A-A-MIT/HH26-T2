from sentence_transformers import SentenceTransformer
import torch


MODEL_NAME = "intfloat/multilingual-e5-small"

device = "cuda" if torch.cuda.is_available() else "cpu"

model = SentenceTransformer(
    MODEL_NAME,
    device=device
)


context = (
    "मधुमेह के सबसे आम लक्षणों में बार-बार पेशाब आना, "
    "तेज प्यास, भूख लगना और थकान शामिल हैं।"
)

answer = (
    "The symptoms of diabetes include frequent urination, "
    "excessive thirst, increased hunger, and fatigue."
)


context_vector = model.encode(
    f"passage: {context}",
    normalize_embeddings=True
)

answer_vector = model.encode(
    f"query: {answer}",
    normalize_embeddings=True
)


similarity = float(
    context_vector @ answer_vector
)


print("DEVICE:", device)
print("CROSS-LANGUAGE SIMILARITY:", similarity)