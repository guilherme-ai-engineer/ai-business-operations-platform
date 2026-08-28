from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func

from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    knowledge_source: Mapped[str] = mapped_column(
        String(255),
        default="",
        nullable=False,
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    customer_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="received",
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        default="general",
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        default="low",
        nullable=False,
    )

    suggested_response: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        default="general",
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        default="low",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )