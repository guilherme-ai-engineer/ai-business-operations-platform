# AI Business Operations Platform

An AI-powered backend platform for customer support and business operations, built with FastAPI, PostgreSQL, OpenAI, RAG, JWT authentication, and Docker.

The project simulates a real B2B software platform where customers can interact with an AI support agent, access order information, manage persistent conversations, create support tickets, and communicate with administrators.

## Live Demo

The API is publicly deployed on Render.

**Interactive API documentation:**

https://ai-business-operations-platform.onrender.com/docs

> The free Render instance may take up to about one minute to wake up after a period of inactivity.

## Features

### AI Support Agent

- OpenAI-powered customer support agent
- Tool calling for business operations
- Order status lookup
- Customer order lookup
- Company knowledge search
- Automatic conversation title generation

### RAG Knowledge Base

- Retrieval-Augmented Generation
- Company policy documents
- TXT and PDF document support
- Admin-only document uploads
- Automatic knowledge index refresh

### Authentication and Authorization

- User registration and login
- JWT bearer authentication
- Argon2 password hashing
- Customer and administrator roles
- Role-based API permissions
- Conversation and ticket ownership protection

### Persistent Conversations

- Create conversations
- List previous conversations
- Rename conversations
- Delete conversations
- Retrieve message history
- AI conversation memory stored in the database

### Customer Support System

- AI-classified support tickets
- Ticket categories and priorities
- Suggested AI responses
- Customer-to-admin replies
- Admin-to-customer replies
- Ticket workflow:
  - received
  - in_progress
  - resolved
  - closed
- Closed-ticket reply protection

### Automated Testing

The project includes automated API tests using pytest and FastAPI TestClient.

Tests cover:

- API health
- Authentication
- JWT-protected routes
- Admin permissions
- Document uploads
- Conversation creation
- Conversation ownership
- AI agent mocking
- Support ticket creation
- Closed-ticket workflow

External AI calls are mocked during tests to keep the test suite fast and deterministic.

## Tech Stack

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy
- OpenAI API
- RAG
- JWT
- Argon2
- Pydantic
- pytest
- Docker
- Docker Compose

## Architecture

```text
Client / Swagger
       |
       v
    FastAPI
       |
       +-------------------+
       |                   |
       v                   v
Authentication        AI Agent
       |                   |
       v                   +------> OpenAI
 PostgreSQL                |
                           +------> RAG Knowledge Base
                           |
                           +------> Business Tools
                                      |
                                      v
                                  PostgreSQL
```

## Project Structure

```text
ai-business-operations-platform/
|
├── routers/
│   ├── auth.py
│   ├── conversations.py
│   ├── support.py
│   └── knowledge.py
|
├── tests/
│   ├── conftest.py
│   └── test_api.py
|
├── knowledge_base/
|
├── agent_service.py
├── ai_service.py
├── auth_service.py
├── conversation_service.py
├── order_service.py
├── rag_service.py
├── database.py
├── dependencies.py
├── models.py
├── main.py
|
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Running with Docker

Docker Compose starts both the FastAPI backend and PostgreSQL database.

Create a `.env` file with the required secrets:

```env
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

Then run:

```bash
docker compose up --build
```

Open the API documentation:

```text
http://127.0.0.1:8000/docs
```

Docker runs:

```text
FastAPI container
        |
        v
PostgreSQL container
```

PostgreSQL data is persisted using a Docker volume.

## Running Tests

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python -m pytest -v
```

The current test suite contains 10 automated API tests.

## Example API Endpoints

### Authentication

```text
POST /auth/register
POST /auth/login
GET  /auth/me
```

### Conversations

```text
POST   /conversations
GET    /conversations
PATCH  /conversations/{conversation_id}
DELETE /conversations/{conversation_id}
GET    /conversations/{conversation_id}/messages
```

### AI Agent

```text
POST /agent/chat
```

### Support

```text
POST /support
GET  /tickets
GET  /tickets/{ticket_id}/replies
POST /tickets/{ticket_id}/replies
```

### Administration

```text
GET   /admin/tickets
PATCH /admin/tickets/{ticket_id}
POST  /admin/tickets/{ticket_id}/replies
GET   /admin/tickets/{ticket_id}/replies
```

### Knowledge Base

```text
POST /documents
```

## Security

- Passwords are never stored in plaintext.
- Passwords are hashed using Argon2.
- Protected routes require JWT authentication.
- Administrative routes enforce role-based authorization.
- Customers can access only their own conversations and support tickets.
- Environment secrets are excluded from Git through `.gitignore`.

## Purpose

This project was built as a practical backend and AI engineering portfolio project.

It demonstrates how an AI-enabled business application can combine:

- REST APIs
- authentication
- authorization
- relational databases
- AI agents
- RAG
- business workflows
- automated testing
- containerized deployment