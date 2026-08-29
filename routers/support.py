from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_service import analyze_support_message
from database import get_db
from dependencies import (
    get_current_admin,
    get_current_user,
)
from models import (
    Ticket,
    TicketReply,
    User,
)


router = APIRouter(
    tags=["Support"],
)


class TicketReplyRequest(BaseModel):
    message: str


class TicketReplyResponse(BaseModel):
    reply_id: int
    ticket_id: int
    author_email: str
    author_role: str
    message: str
    created_at: datetime


class TicketStatusUpdateRequest(BaseModel):
    status: str


class SupportRequest(BaseModel):
    customer_name: str
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


@router.post(
    "/support",
    response_model=SupportResponse,
    summary="Create an AI support ticket",
)
def create_support_ticket(
    request: SupportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analysis = analyze_support_message(
        request.message
    )

    ticket = Ticket(
        customer_name=request.customer_name,
        email=current_user.email,
        message=request.message,
        category=analysis["category"],
        priority=analysis["priority"],
        suggested_response=analysis[
            "suggested_response"
        ],
        knowledge_source=analysis[
            "knowledge_source"
        ],
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


@router.get(
    "/tickets",
    response_model=list[SupportResponse],
    summary="List current user's support tickets",
)
def get_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tickets = db.scalars(
        select(Ticket)
        .where(
            Ticket.email == current_user.email
        )
        .order_by(
            Ticket.id.desc()
        )
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


@router.get(
    "/tickets/{ticket_id}/replies",
    response_model=list[TicketReplyResponse],
    summary="Get replies for a support ticket",
)
def get_ticket_replies(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = db.scalar(
        select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.email == current_user.email,
        )
    )

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found for this customer.",
        )

    replies = db.scalars(
        select(TicketReply)
        .where(
            TicketReply.ticket_id == ticket_id
        )
        .order_by(
            TicketReply.id
        )
    ).all()

    return [
        TicketReplyResponse(
            reply_id=reply.id,
            ticket_id=reply.ticket_id,
            author_email=reply.author_email,
            author_role=reply.author_role,
            message=reply.message,
            created_at=reply.created_at,
        )
        for reply in replies
    ]


@router.post(
    "/tickets/{ticket_id}/replies",
    response_model=TicketReplyResponse,
    summary="Reply to your support ticket",
)
def create_customer_ticket_reply(
    ticket_id: int,
    request: TicketReplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = db.scalar(
        select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.email == current_user.email,
        )
    )

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found for this customer.",
        )

    if ticket.status == "closed":
        raise HTTPException(
            status_code=400,
            detail=(
                "Closed tickets cannot receive new replies."
            ),
        )

    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Reply cannot be empty.",
        )

    ticket.status = "in_progress"

    reply = TicketReply(
        ticket_id=ticket.id,
        author_email=current_user.email,
        author_role="customer",
        message=message,
    )

    db.add(reply)
    db.commit()
    db.refresh(reply)

    return TicketReplyResponse(
        reply_id=reply.id,
        ticket_id=reply.ticket_id,
        author_email=reply.author_email,
        author_role=reply.author_role,
        message=reply.message,
        created_at=reply.created_at,
    )


@router.get(
    "/admin/tickets",
    response_model=list[SupportResponse],
    summary="List all support tickets",
)
def get_all_tickets(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    tickets = db.scalars(
        select(Ticket)
        .order_by(
            Ticket.id.desc()
        )
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


@router.patch(
    "/admin/tickets/{ticket_id}",
    response_model=SupportResponse,
    summary="Update support ticket status",
)
def update_ticket_status(
    ticket_id: int,
    request: TicketStatusUpdateRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    allowed_statuses = {
        "received",
        "in_progress",
        "resolved",
        "closed",
    }

    status = request.status.strip().lower()

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid status. Allowed values: "
                "received, in_progress, resolved, closed."
            ),
        )

    ticket = db.scalar(
        select(Ticket).where(
            Ticket.id == ticket_id
        )
    )

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found.",
        )

    ticket.status = status

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


@router.post(
    "/admin/tickets/{ticket_id}/replies",
    response_model=TicketReplyResponse,
    summary="Reply to a support ticket",
)
def create_admin_ticket_reply(
    ticket_id: int,
    request: TicketReplyRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    ticket = db.scalar(
        select(Ticket).where(
            Ticket.id == ticket_id
        )
    )

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found.",
        )

    if ticket.status == "closed":
        raise HTTPException(
            status_code=400,
            detail=(
                "Closed tickets cannot receive new replies. "
                "Reopen the ticket first."
            ),
        )

    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Reply cannot be empty.",
        )

    ticket.status = "in_progress"

    reply = TicketReply(
        ticket_id=ticket.id,
        author_email=current_admin.email,
        author_role="admin",
        message=message,
    )

    db.add(reply)
    db.commit()
    db.refresh(reply)

    return TicketReplyResponse(
        reply_id=reply.id,
        ticket_id=reply.ticket_id,
        author_email=reply.author_email,
        author_role=reply.author_role,
        message=reply.message,
        created_at=reply.created_at,
    )


@router.get(
    "/admin/tickets/{ticket_id}/replies",
    response_model=list[TicketReplyResponse],
    summary="Get all replies for a support ticket",
)
def get_admin_ticket_replies(
    ticket_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    ticket = db.scalar(
        select(Ticket).where(
            Ticket.id == ticket_id
        )
    )

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found.",
        )

    replies = db.scalars(
        select(TicketReply)
        .where(
            TicketReply.ticket_id == ticket_id
        )
        .order_by(
            TicketReply.id
        )
    ).all()

    return [
        TicketReplyResponse(
            reply_id=reply.id,
            ticket_id=reply.ticket_id,
            author_email=reply.author_email,
            author_role=reply.author_role,
            message=reply.message,
            created_at=reply.created_at,
        )
        for reply in replies
    ]