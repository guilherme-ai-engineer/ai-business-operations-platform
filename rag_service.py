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
MAX_CHUNK_SIZE = 500

_knowledge_index = None


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


def split_into_chunks(text: str) -> list[str]:
    paragraphs = [
        paragraph.strip()
        for paragraph in text.split("\n")
        if paragraph.strip()
    ]

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        candidate = (
            f"{current_chunk}\n{paragraph}".strip()
        )

        if len(candidate) <= MAX_CHUNK_SIZE:
            current_chunk = candidate
        else:
            if current_chunk:
                chunks.append(current_chunk)

            current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def load_chunks() -> list[dict]:
    chunks = []

    for file_path in KNOWLEDGE_BASE_DIR.glob("*.txt"):
        content = file_path.read_text(
            encoding="utf-8"
        )

        document_chunks = split_into_chunks(content)

        for index, chunk in enumerate(
            document_chunks,
            start=1,
        ):
            chunks.append(
                {
                    "source": file_path.name,
                    "chunk_index": index,
                    "content": chunk,
                }
            )

    return chunks


def build_knowledge_index() -> list[dict]:
    chunks = load_chunks()

    for chunk in chunks:
        chunk["embedding"] = get_embedding(
            chunk["content"]
        )

    return chunks


def get_knowledge_index() -> list[dict]:
    global _knowledge_index

    if _knowledge_index is None:
        _knowledge_index = build_knowledge_index()

    return _knowledge_index


def retrieve_relevant_document(query: str) -> dict:
    query_embedding = get_embedding(query)

    knowledge_index = get_knowledge_index()

    best_chunk = None
    best_score = -1.0

    for chunk in knowledge_index:
        score = cosine_similarity(
            query_embedding,
            chunk["embedding"],
        )

        if score > best_score:
            best_score = score
            best_chunk = chunk

    return {
        "source": best_chunk["source"],
        "chunk_index": best_chunk["chunk_index"],
        "content": best_chunk["content"],
        "score": best_score,
    }


if __name__ == "__main__":
    result = retrieve_relevant_document(
        "How long does a refund take?"
    )

    print("Source:", result["source"])
    print("Chunk:", result["chunk_index"])
    print("Score:", result["score"])
    print()
    print(result["content"])