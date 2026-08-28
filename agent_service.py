import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from rag_service import retrieve_relevant_chunks

from order_service import (
    get_customer_orders,
    get_order_status,
)


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")


if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is missing from .env"
    )

if not OPENAI_MODEL:
    raise RuntimeError(
        "OPENAI_MODEL is missing from .env"
    )


client = OpenAI(
    api_key=OPENAI_API_KEY
)


ORDER_STATUS_TOOL = {
    "type": "function",
    "name": "get_order_status",
    "description": (
        "Get the current status, total amount, "
        "and estimated delivery date of a specific order."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "integer",
                "description": "The order ID.",
            },
        },
        "required": [
            "order_id",
        ],
        "additionalProperties": False,
    },
    "strict": True,
}


CUSTOMER_ORDERS_TOOL = {
    "type": "function",
    "name": "get_customer_orders",
    "description": (
        "Get all orders that belong to the current customer."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
    "strict": True,
}

COMPANY_KNOWLEDGE_TOOL = {
    "type": "function",
    "name": "search_company_knowledge",
    "description": (
        "Search company policies and documentation. "
        "Use this for questions about refunds, shipping, "
        "billing policies, warranties, and company rules."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "The customer's question to search "
                    "against company documentation."
                ),
            },
        },
        "required": [
            "query",
        ],
        "additionalProperties": False,
    },
    "strict": True,
}


TOOLS = [
    ORDER_STATUS_TOOL,
    CUSTOMER_ORDERS_TOOL,
    COMPANY_KNOWLEDGE_TOOL,
]


def run_order_agent(
    message: str,
    customer_email: str,
) -> str:
    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=(
            "You are a customer support AI agent. "
            "Use get_order_status when the customer asks "
            "about a specific order number. "
            "Use get_customer_orders when the customer asks "
            "which orders they have. "
            "Use search_company_knowledge for questions about "
            "refunds, shipping policies, billing policies, "
            "warranties, and company rules. "
            "Never invent order information or company policies. "
            "The authenticated customer email is supplied by "
            "the application and must be used for customer data."
        ),
        input=(
            f"Authenticated customer email: {customer_email}\n"
            f"Customer message: {message}"
        ),
        tools=TOOLS,
        tool_choice="auto",
    )

    for _ in range(5):
        tool_outputs = []

        for item in response.output:
            if item.type != "function_call":
                continue

            arguments = json.loads(
                item.arguments
            )

            if item.name == "get_order_status":
                tool_result = get_order_status(
                    order_id=arguments["order_id"],
                    customer_email=customer_email,
                )

            elif item.name == "get_customer_orders":
                tool_result = get_customer_orders(
                    customer_email=customer_email,
                )

            elif item.name == "search_company_knowledge":
                chunks = retrieve_relevant_chunks(
                    query=arguments["query"],
                    top_k=3,
                )

                if chunks:
                    tool_result = {
                        "found": True,
                        "results": [
                            {
                                "source": chunk["source"],
                                "chunk_index": chunk["chunk_index"],
                                "content": chunk["content"],
                                "score": chunk["score"],
                            }
                            for chunk in chunks
                        ],
                    }

                else:
                    tool_result = {
                        "found": False,
                        "message": (
                            "No relevant company documentation "
                            "was found."
                        ),
                    }

            else:
                tool_result = {
                    "error": "Unknown tool."
                }

            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps(
                        tool_result
                    ),
                }
            )

        if not tool_outputs:
            return response.output_text

        response = client.responses.create(
            model=OPENAI_MODEL,
            previous_response_id=response.id,
            input=tool_outputs,
            tools=TOOLS,
        )

    return (
        "I could not complete the request "
        "after several tool calls."
    )


