from sqlalchemy import select

from database import SessionLocal
from models import ConversationMessage


def add_conversation_message(
    customer_email: str,
    role: str,
    content: str,
) -> None:
    db = SessionLocal()

    try:
        message = ConversationMessage(
            customer_email=customer_email,
            role=role,
            content=content,
        )

        db.add(message)
        db.commit()

    finally:
        db.close()


def get_recent_conversation(
    customer_email: str,
    limit: int = 10,
) -> list[dict]:
    db = SessionLocal()

    try:
        messages = db.scalars(
            select(ConversationMessage)
            .where(
                ConversationMessage.customer_email
                == customer_email
            )
            .order_by(
                ConversationMessage.id.desc()
            )
            .limit(limit)
        ).all()

        messages.reverse()

        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in messages
        ]

    finally:
        db.close()