import json
import os
from rag_service import retrieve_relevant_chunks
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")


if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing from .env")


client = OpenAI(api_key=OPENAI_API_KEY)


def analyze_support_message(message: str) -> dict:
    relevant_chunks = retrieve_relevant_chunks(
        message,
        top_k=3,
    )

    if relevant_chunks:
        policy_context = "\n\n".join(
            (
                f"Source: {chunk['source']} "
                f"(chunk {chunk['chunk_index']})\n"
                f"{chunk['content']}"
            )
            for chunk in relevant_chunks
        )
    else:
        policy_context = (
            "No sufficiently relevant company policy was found."
        )


    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=(
            "You analyze customer support messages for an e-commerce company. "
            "Choose the best category and priority. "
            "Also write a short, professional suggested response to the customer. "
            "Categories: billing, refund, shipping, account, technical, general. "
            "Priorities: low, medium, high. "
            "Duplicate charges and serious payment problems should be high priority. "
            "Do not invent order, payment, refund, or account information. "
            "If the issue requires human review, say so clearly."
            'Base the suggested response on the provided company policy.'
            'Do not contradict the company policy.'
        ),
        input=(
            f"Customer message:\n{message}\n\n"
            f"Relevant company policy excerpts:\n\n"
            f"{policy_context}"
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": "support_analysis",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": [
                                "billing",
                                "refund",
                                "shipping",
                                "account",
                                "technical",
                                "general",
                            ],
                        },
                        "priority": {
                            "type": "string",
                            "enum": [
                                "low",
                                "medium",
                                "high",
                            ],
                        },
                        "suggested_response": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "category",
                        "priority",
                        "suggested_response",
                    ],
                    "additionalProperties": False,
                },
            }
        },
    )

    result = json.loads(response.output_text)

    source_details = []

    for chunk in relevant_chunks:
        source_details.append(
            (
                f"{chunk['source']} "
                f"[chunk {chunk['chunk_index']}, "
                f"score {chunk['score']:.3f}]"
            )
        )

    if source_details:
        result["knowledge_source"] = "; ".join(
            source_details
        )
    else:
        result["knowledge_source"] = (
            "No relevant policy found"
        )

    return result