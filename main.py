from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from pathlib import Path
from uuid import uuid4
from datetime import datetime

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile

from ai_service import analyze_support_message
from database import get_db
from rag_service import invalidate_knowledge_index
from agent_service import run_order_agent
from models import Conversation, Ticket


KNOWLEDGE_BASE_DIR = Path("knowledge_base")
KNOWLEDGE_BASE_DIR.mkdir(exist_ok=True)

MAX_DOCUMENT_SIZE = 10_000_000

app = FastAPI(
    title="AI Business Operations Platform",
    description="AI-powered customer support and business operations platform.",
    version="0.4.0",
)

class ConversationListItem(BaseModel):
    conversation_id: str
    title: str
    created_at: datetime

class ConversationCreateRequest(BaseModel):
    customer_email: str

class AgentRequest(BaseModel):
    customer_email: str
    conversation_id: str
    message: str

class AgentResponse(BaseModel):
        response: str

class ConversationResponse(BaseModel):
    conversation_id: str

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

@app.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
):
    filename = Path(file.filename or "").name

    extension = Path(filename).suffix.lower()

    if extension not in {".txt", ".pdf"}:
        raise HTTPException(
            status_code=400,
            detail="Only .txt and .pdf files are supported.",
        )

    content = await file.read()

    if len(content) > MAX_DOCUMENT_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File is too large.",
        )

    if extension == ".txt":
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="The text file must use UTF-8 encoding.",
            )


    file_path = KNOWLEDGE_BASE_DIR / filename
    file_path.write_bytes(content)

    invalidate_knowledge_index()

    return {
        "filename": filename,
        "status": "uploaded",
        "rag_index": "will rebuild on next query",
    }


@app.post(
    "/conversations",
    response_model=ConversationResponse,
)
def create_conversation(
    request: ConversationCreateRequest,
    db: Session = Depends(get_db),
):
    conversation_id = str(uuid4())

    conversation = Conversation(
        id=conversation_id,
        customer_email=request.customer_email,
        title="New conversation",
    )

    db.add(conversation)
    db.commit()

    return ConversationResponse(
        conversation_id=conversation_id,
    )


@app.post(
    "/agent/chat",
    response_model=AgentResponse,
)
def agent_chat(
    request: AgentRequest,
    db: Session = Depends(get_db),
):
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == request.conversation_id,
            Conversation.customer_email == request.customer_email,
        )
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found for this customer.",
        )

    response = run_order_agent(
        message=request.message,
        customer_email=request.customer_email,
        conversation_id=request.conversation_id,
    )

    return AgentResponse(
        response=response,
    )


@app.get(
    "/conversations",
    response_model=list[ConversationListItem],
)
def get_conversations(
    customer_email: str,
    db: Session = Depends(get_db),
):
    conversations = db.scalars(
        select(Conversation)
        .where(
            Conversation.customer_email
            == customer_email
        )
        .order_by(
            Conversation.created_at.desc()
        )
    ).all()

    return [
        ConversationListItem(
            conversation_id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
        )
        for conversation in conversations
    ]