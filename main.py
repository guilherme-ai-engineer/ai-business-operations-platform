from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(
    title="AI Business Operations Platform",
    description="AI-powered customer support and business operations platform.",
    version="0.2.0",
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


tickets = []


@app.get("/")
def home():
    return {
        "app": "AI Business Operations Platform",
        "status": "running",
    }


@app.post("/support", response_model=SupportResponse)
def create_support_ticket(request: SupportRequest):
    ticket_id = len(tickets) + 1

    ticket = SupportResponse(
        ticket_id=ticket_id,
        status="received",
        customer_name=request.customer_name,
        email=request.email,
        message_received=request.message,
    )

    tickets.append(ticket)

    return ticket


@app.get("/tickets")
def get_tickets():
    return tickets