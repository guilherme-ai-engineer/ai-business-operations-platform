from sqlalchemy import select

from database import SessionLocal
from models import ConversationMessage


def add_conversation_message(
    customer_email: str,
    conversation_id: str,
    role: str,
    content: str,
) -> None:
    db = SessionLocal()

    try:
        message = ConversationMessage(
            customer_email=customer_email,
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

        db.add(message)
        db.commit()

    finally:
        db.close()


def get_recent_conversation(
    customer_email: str,
    conversation_id: str,
    limit: int = 10,
) -> list[dict]:
    db = SessionLocal()

    try:
        messages = db.scalars(
            select(ConversationMessage)
            .where(
                ConversationMessage.customer_email
                == customer_email,
                ConversationMessage.conversation_id
                == conversation_id,
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