from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from agent_service import (
    generate_conversation_title,
    run_order_agent,
)
from conversation_service import get_conversation_messages
from database import get_db
from dependencies import get_current_user
from models import (
    Conversation,
    ConversationMessage,
    User,
)


router = APIRouter()


class ConversationRenameRequest(BaseModel):
    title: str


class ConversationMessageResponse(BaseModel):
    role: str
    content: str
    created_at: datetime


class ConversationListItem(BaseModel):
    conversation_id: str
    title: str
    created_at: datetime


class ConversationResponse(BaseModel):
    conversation_id: str


class AgentRequest(BaseModel):
    conversation_id: str
    message: str


class AgentResponse(BaseModel):
    response: str


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    tags=["Conversations"],
    summary="Create a new conversation",
)
def create_conversation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation_id = str(
        uuid4()
    )

    conversation = Conversation(
        id=conversation_id,
        customer_email=current_user.email,
        title="New conversation",
    )

    db.add(conversation)
    db.commit()

    return ConversationResponse(
        conversation_id=conversation_id,
    )


@router.get(
    "/conversations",
    response_model=list[ConversationListItem],
    tags=["Conversations"],
    summary="List customer conversations",
)
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversations = db.scalars(
        select(Conversation)
        .where(
            Conversation.customer_email
            == current_user.email
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


@router.patch(
    "/conversations/{conversation_id}",
    tags=["Conversations"],
    summary="Rename a conversation",
)
def rename_conversation(
    conversation_id: str,
    request: ConversationRenameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.customer_email
            == current_user.email,
        )
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Conversation not found "
                "for this customer."
            ),
        )

    title = request.title.strip()

    if not title:
        raise HTTPException(
            status_code=400,
            detail="Title cannot be empty.",
        )

    conversation.title = title[:200]

    db.commit()

    return {
        "conversation_id": conversation.id,
        "title": conversation.title,
        "status": "renamed",
    }


@router.delete(
    "/conversations/{conversation_id}",
    tags=["Conversations"],
    summary="Delete a conversation",
)
def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.customer_email
            == current_user.email,
        )
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Conversation not found "
                "for this customer."
            ),
        )

    db.execute(
        delete(ConversationMessage).where(
            ConversationMessage.conversation_id
            == conversation_id,
            ConversationMessage.customer_email
            == current_user.email,
        )
    )

    db.delete(conversation)
    db.commit()

    return {
        "conversation_id": conversation_id,
        "status": "deleted",
    }


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[ConversationMessageResponse],
    tags=["Conversations"],
    summary="Get conversation message history",
)
def get_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.customer_email
            == current_user.email,
        )
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Conversation not found "
                "for this customer."
            ),
        )

    return get_conversation_messages(
        customer_email=current_user.email,
        conversation_id=conversation_id,
    )


@router.post(
    "/agent/chat",
    response_model=AgentResponse,
    tags=["AI Agent"],
    summary="Chat with the AI support agent",
)
def agent_chat(
    request: AgentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id
            == request.conversation_id,
            Conversation.customer_email
            == current_user.email,
        )
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Conversation not found "
                "for this customer."
            ),
        )

    response = run_order_agent(
        message=request.message,
        customer_email=current_user.email,
        conversation_id=request.conversation_id,
    )

    if conversation.title == "New conversation":
        conversation.title = (
            generate_conversation_title(
                request.message
            )
        )

        db.commit()

    return AgentResponse(
        response=response,
    )