import math
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing from .env")

client = OpenAI(api_key=OPENAI_API_KEY)

KNOWLEDGE_BASE_DIR = Path("knowledge_base")
EMBEDDING_MODEL = "text-embedding-3-small"


def get_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )

    return response.data[0].embedding


def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    dot_product = sum(
        a * b
        for a, b in zip(vector_a, vector_b)
    )

    magnitude_a = math.sqrt(
        sum(a * a for a in vector_a)
    )

    magnitude_b = math.sqrt(
        sum(b * b for b in vector_b)
    )

    return dot_product / (magnitude_a * magnitude_b)


def load_documents() -> list[dict]:
    documents = []

    for file_path in KNOWLEDGE_BASE_DIR.glob("*.txt"):
        content = file_path.read_text(encoding="utf-8")

        documents.append(
            {
                "source": file_path.name,
                "content": content,
            }
        )

    return documents


def retrieve_relevant_document(query: str) -> dict:
    query_embedding = get_embedding(query)

    documents = load_documents()

    best_document = None
    best_score = -1.0

    for document in documents:
        document_embedding = get_embedding(
            document["content"]
        )

        score = cosine_similarity(
            query_embedding,
            document_embedding,
        )

        if score > best_score:
            best_score = score
            best_document = document

    return {
        "source": best_document["source"],
        "content": best_document["content"],
        "score": best_score,
    }


if __name__ == "__main__":
    result = retrieve_relevant_document(
        "I want my money back for a product."
    )

    print("Source:", result["source"])
    print("Score:", result["score"])
    print()
    print(result["content"])