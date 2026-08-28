import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from order_service import get_order_status


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.6-luna",
)


if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is missing from .env"
    )


client = OpenAI(
    api_key=OPENAI_API_KEY
)


ORDER_TOOL = {
    "type": "function",
    "name": "get_order_status",
    "description": (
        "Get the current status and estimated delivery "
        "date of a customer's order."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "integer",
                "description": "The order ID.",
            },
            "customer_email": {
                "type": "string",
                "description": (
                    "The email address of the customer."
                ),
            },
        },
        "required": [
            "order_id",
            "customer_email",
        ],
        "additionalProperties": False,
    },
    "strict": True,
}


def run_order_agent(
    message: str,
    customer_email: str,
) -> str:
    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=(
            "You are a customer support assistant. "
            "Use the get_order_status tool when the "
            "customer asks about a specific order. "
            "Never invent order information. "
            "Only use the customer's provided email."
        ),
        input=(
            f"Customer email: {customer_email}\n"
            f"Customer message: {message}"
        ),
        tools=[ORDER_TOOL],
        tool_choice="auto",
    )

    for item in response.output:
        if (
            item.type == "function_call"
            and item.name == "get_order_status"
        ):
            arguments = json.loads(
                item.arguments
            )

            arguments["customer_email"] = (
                customer_email
            )

            tool_result = get_order_status(
                order_id=arguments["order_id"],
                customer_email=(
                    arguments["customer_email"]
                ),
            )

            final_response = client.responses.create(
                model=OPENAI_MODEL,
                previous_response_id=response.id,
                input=[
                    {
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps(
                            tool_result
                        ),
                    }
                ],
                tools=[ORDER_TOOL],
            )

            return final_response.output_text

    return response.output_text


if __name__ == "__main__":
    result = run_order_agent(
        message="Where is my order 1042?",
        customer_email="john@example.com",
    )

    print(result)