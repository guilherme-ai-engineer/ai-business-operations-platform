from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Ticket


app = FastAPI(
    title="AI Business Operations Platform",
    description="AI-powered customer support and business operations platform.",
    version="0.3.0",
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
    ticket = Ticket(
        customer_name=request.customer_name,
        email=request.email,
        message=request.message,
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
        )
        for ticket in tickets
    ]