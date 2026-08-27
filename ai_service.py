def analyze_support_message(message: str) -> dict:
    text = message.lower()

    if "charged" in text or "payment" in text or "billing" in text:
        category = "billing"
        priority = "high"

    elif "refund" in text:
        category = "refund"
        priority = "medium"

    elif "order" in text or "delivery" in text or "arrived" in text:
        category = "shipping"
        priority = "medium"

    elif "password" in text or "login" in text or "account" in text:
        category = "account"
        priority = "medium"

    else:
        category = "general"
        priority = "low"

    return {
        "category": category,
        "priority": priority,
    }

