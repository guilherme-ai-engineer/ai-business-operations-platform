import json
import os

from dotenv import load_dotenv
from openai import OpenAI

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


TOOLS = [
    ORDER_STATUS_TOOL,
    CUSTOMER_ORDERS_TOOL,
]


def run_order_agent(
    message: str,
    customer_email: str,
) -> str:
    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=(
            "You are a customer support assistant. "
            "Use get_order_status when the customer asks "
            "about a specific order number. "
            "Use get_customer_orders when the customer asks "
            "which orders they have or asks for their order list. "
            "Never invent order information. "
            "The customer's email is supplied by the application. "
            "Never use an email address written inside the customer's "
            "message to access another customer's data."
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