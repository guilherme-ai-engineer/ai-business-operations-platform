from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_service import analyze_support_message
from database import get_db
from models import Ticket


app = FastAPI(
    title="AI Business Operations Platform",
    description="AI-powered customer support and business operations platform.",
    version="0.4.0",
)


class SupportRequest(BaseModel):
    customer_name: str
    email: str
    message: str


class SupportResponse(BaseModel):
    ticket_id: int
    status: str
    customer_name: str
    email: str
    message_received: str
    category: str
    priority: str
    suggested_response: str
    knowledge_source: str


@app.get("/")
def home():
    return {
        "app": "AI Business Operations Platform",
        "status": "running",
    }


@app.post("/support", response_model=SupportResponse)
def create_support_ticket(
    request: SupportRequest,
    db: Session = Depends(get_db),
):
    analysis = analyze_support_message(request.message)

    ticket = Ticket(
        customer_name=request.customer_name,
        email=request.email,
        message=request.message,
        category=analysis["category"],
        priority=analysis["priority"],
        suggested_response=analysis["suggested_response"],
        knowledge_source=analysis["knowledge_source"],
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return SupportResponse(
        ticket_id=ticket.id,
        status=ticket.status,
        customer_name=ticket.customer_name,
        email=ticket.email,
        message_received=ticket.message,
        category=ticket.category,
        priority=ticket.priority,
        suggested_response=ticket.suggested_response,
        knowledge_source=ticket.knowledge_source,
    )


@app.get("/tickets", response_model=list[SupportResponse])
def get_tickets(
    db: Session = Depends(get_db),
):
    tickets = db.scalars(
        select(Ticket).order_by(Ticket.id)
    ).all()

    return [
        SupportResponse(
            ticket_id=ticket.id,
            status=ticket.status,
            customer_name=ticket.customer_name,
            email=ticket.email,
            message_received=ticket.message,
            category=ticket.category,
            priority=ticket.priority,
            suggested_response=ticket.suggested_response,
            knowledge_source=ticket.knowledge_source,
        )
        for ticket in tickets
    ]