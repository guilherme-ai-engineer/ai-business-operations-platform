from fastapi import FastAPI

from routers.microsoft import router as microsoft_router
from routers.auth import router as auth_router
from routers.conversations import router as conversations_router
from routers.knowledge import router as knowledge_router
from routers.support import router as support_router


TAGS_METADATA = [
    {
        "name": "System",
        "description": (
            "API health and system information."
        ),
    },
    {
        "name": "Authentication",
        "description": (
            "User registration, login, "
            "and JWT authentication."
        ),
    },
    {
        "name": "Support",
        "description": (
            "Customer support ticket creation, "
            "AI classification, ticket management, "
            "and two-way support replies."
        ),
    },
    {
        "name": "Knowledge Base",
        "description": (
            "Admin-managed company documents "
            "used by the RAG system."
        ),
    },
    {
        "name": "Conversations",
        "description": (
            "Create, list, rename, delete, "
            "and retrieve customer conversations."
        ),
    },
    {
        "name": "AI Agent",
        "description": (
            "AI customer support agent with RAG, "
            "persistent memory, and database tools."
        ),
    },
]


app = FastAPI(
    title="AI Business Operations Platform",
    description=(
        "AI-powered customer support platform with "
        "RAG, PostgreSQL, persistent conversation memory, "
        "document ingestion, AI tool calling, "
        "JWT authentication, and role-based access."
    ),
    version="0.6.0",
    openapi_tags=TAGS_METADATA,
)


app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(support_router)
app.include_router(knowledge_router)
app.include_router(microsoft_router)


@app.get(
    "/",
    tags=["System"],
    summary="Check API status",
)
def home():
    return {
        "app": "AI Business Operations Platform",
        "status": "running",
    }