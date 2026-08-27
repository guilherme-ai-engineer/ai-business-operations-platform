from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(
    title="AI Business Operations Platform",
    description="AI-powered customer support and business operations platform.",
    version="0.1.0",
)


class SupportRequest(BaseModel):
    customer_name: str
    email: str
    message: str


class SupportResponse(BaseModel):
    ticket_id: int
    status: str
    customer_name: str
    message_received: str


@app.get("/")
def home():
    return {
        "app": "AI Business Operations Platform",
        "status": "running",
    }


@app.post("/support", response_model=SupportResponse)
def create_support_ticket(request: SupportRequest):
    return SupportResponse(
        ticket_id=1,
        status="received",
        customer_name=request.customer_name,
        message_received=request.message,
    )