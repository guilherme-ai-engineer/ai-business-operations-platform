import json
import os
from rag_service import retrieve_relevant_document
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")


if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing from .env")


client = OpenAI(api_key=OPENAI_API_KEY)


def analyze_support_message(message: str) -> dict:
    relevant_document = retrieve_relevant_document(message)
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
            f"Company policy source:\n{relevant_document['source']}\n\n"
            f"Company policy:\n{relevant_document['content']}"
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

    result["knowledge_source"] = relevant_document["source"]

    return result