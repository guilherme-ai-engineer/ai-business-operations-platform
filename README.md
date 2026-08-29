# AI Business Operations Platform

An AI-powered B2B backend platform for customer support, business operations, and enterprise integrations.

Built with FastAPI, PostgreSQL, OpenAI, RAG, Microsoft Graph, OAuth 2.0, JWT authentication, Docker, and automated testing.

The project simulates a real business software platform where customers can interact with an AI support agent, access order information, maintain persistent conversations, create support tickets, connect external business accounts, and communicate with administrators.

## Live Demo

The API is publicly deployed on Render.

**Interactive Swagger documentation:**

https://ai-business-operations-platform.onrender.com/docs

> The free Render instance may take about one minute to wake up after a period of inactivity.

---

## Features

### AI Support Agent

- OpenAI-powered customer support agent
- AI tool calling for business operations
- Order status lookup
- Customer order lookup
- Company knowledge search
- Persistent conversation memory
- Automatic AI-generated conversation titles

### RAG Knowledge Base

- Retrieval-Augmented Generation
- Company policy document retrieval
- TXT and PDF support
- Admin-only document uploads
- Automatic knowledge index refresh
- Source metadata in AI responses

### Microsoft Graph Integration

The platform includes a real Microsoft enterprise integration using OAuth 2.0 and Microsoft Graph.

Features include:

- Microsoft OAuth 2.0 authorization-code flow
- Microsoft Entra ID application registration
- MSAL authentication
- Delegated `User.Read` permission
- Secure OAuth `state` validation
- Microsoft Graph `/me` API integration
- Microsoft account connection persistence
- Microsoft connection status endpoint
- Microsoft account disconnect endpoint
- Local and production OAuth redirect URIs
- Production integration deployed on Render

OAuth flow:

```text
Authenticated Platform User
           |
           v
Connect Microsoft
           |
           v
Microsoft Entra ID
           |
           v
Microsoft Login / Consent
           |
           v
Authorization Code
           |
           v
FastAPI OAuth Callback
           |
           v
Access Token
           |
           v
Microsoft Graph
           |
           v
GET /me
           |
           v
PostgreSQL Connection Record
```

The platform stores Microsoft account connection metadata but does not persist the temporary Microsoft access token in plaintext.

### Authentication and Authorization

- User registration and login
- JWT bearer authentication
- Argon2 password hashing
- Customer and administrator roles
- Role-based API permissions
- Conversation ownership protection
- Support ticket ownership protection

### Persistent Conversations

- Create conversations
- List previous conversations
- Rename conversations
- Delete conversations
- Retrieve message history
- Store AI conversation memory in PostgreSQL

### Customer Support System

- AI-classified support tickets
- Ticket categories and priorities
- AI-generated suggested responses
- Customer-to-admin replies
- Admin-to-customer replies

Ticket workflow:

```text
received
   |
   v
in_progress
   |
   v
resolved
   |
   v
closed
```

Closed tickets cannot receive new replies unless they are reopened by an administrator.

### Automated Testing

The project includes automated API tests using `pytest` and FastAPI `TestClient`.

The current suite contains **13 automated API tests**.

Tests cover:

- API health
- Authentication
- JWT-protected routes
- Administrator permissions
- Document upload permissions
- Conversation creation
- Conversation ownership
- AI agent mocking
- Support ticket creation
- Closed-ticket workflow
- Microsoft connection status
- Microsoft OAuth callback persistence
- Microsoft account disconnection

External OpenAI and Microsoft API operations are mocked where appropriate during automated testing.

This keeps the suite:

- fast
- deterministic
- independent from external API availability
- free from unnecessary API usage

---

## Tech Stack

### Backend

- Python 3.12
- FastAPI
- Pydantic
- SQLAlchemy
- HTTPX

### Database

- PostgreSQL
- Psycopg 3

### Artificial Intelligence

- OpenAI API
- AI Agents
- Tool Calling
- Retrieval-Augmented Generation (RAG)

### Enterprise Integrations

- Microsoft Graph
- Microsoft Entra ID
- OAuth 2.0
- MSAL

### Authentication

- JWT
- Argon2 password hashing
- OAuth state validation
- Role-based authorization

### Testing

- pytest
- FastAPI TestClient
- API mocking

### Infrastructure

- Docker
- Docker Compose
- Git
- GitHub
- Render

---

## Architecture

```text
                         Client
                           |
                           v
                       FastAPI
                           |
       +-------------------+-------------------+
       |                   |                   |
       v                   v                   v
 Authentication        AI Agent       Microsoft Integration
       |                   |                   |
       |            +------+-------+           v
       |            |              |       Microsoft Entra ID
       |            v              v             |
       |          OpenAI          RAG            v
       |                            |       Microsoft Graph
       |                            |             |
       +----------------------------+-------------+
                                    |
                                    v
                                PostgreSQL
```

Production architecture:

```text
GitHub
   |
   v
Render Web Service
   |
   v
Dockerized FastAPI
   |
   +--------> OpenAI API
   |
   +--------> Microsoft Entra ID
   |                |
   |                v
   |          Microsoft Graph
   |
   +--------> RAG Knowledge Base
   |
   v
Render PostgreSQL
```

---

## Project Structure

```text
ai-business-operations-platform/
|
├── integrations/
│   ├── __init__.py
│   └── microsoft_graph.py
|
├── routers/
│   ├── __init__.py
│   ├── auth.py
│   ├── conversations.py
│   ├── knowledge.py
│   ├── microsoft.py
│   └── support.py
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
|
├── database.py
├── dependencies.py
├── models.py
├── main.py
|
├── create_tables.py
├── seed_orders.py
|
├── .env.example
├── .gitignore
├── .dockerignore
|
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Environment Configuration

The repository contains:

```text
.env.example
```

Copy it to create a local environment file.

Example:

```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/database_name

OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=your_openai_model

JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
MICROSOFT_REDIRECT_URI=your_microsoft_redirect_uri
MICROSOFT_TENANT=common
```

The real `.env` file is excluded from Git and must never be committed.

### OAuth Redirect URIs

Local development:

```text
http://localhost:8000/integrations/microsoft/callback
```

Production:

```text
https://ai-business-operations-platform.onrender.com/integrations/microsoft/callback
```

---

## Running with Docker

Docker Compose starts both FastAPI and PostgreSQL.

```bash
docker compose up --build
```

Architecture:

```text
Docker Compose
|
├── FastAPI container
|
└── PostgreSQL container
```

PostgreSQL data is persisted using a Docker volume.

Open Swagger:

```text
http://localhost:8000/docs
```

Stop the containers:

```bash
docker compose down
```

---

## Running Without Docker

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure `.env` and ensure PostgreSQL is running.

Create database tables:

```bash
python create_tables.py
```

Start FastAPI:

```bash
uvicorn main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

---

## Running Tests

Run:

```bash
python -m pytest -v
```

Expected current result:

```text
13 passed
```

Tests use an isolated temporary database so development data is not modified.

External AI and Microsoft operations are mocked where appropriate.

---

## API Endpoints

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

### Customer Support

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

### Microsoft Integration

```text
GET    /integrations/microsoft/connect
GET    /integrations/microsoft/callback
GET    /integrations/microsoft/status
DELETE /integrations/microsoft
```

---

## Microsoft OAuth Flow

The integration uses the OAuth 2.0 authorization-code flow.

```text
1. User authenticates with the platform

2. User requests:
   GET /integrations/microsoft/connect

3. FastAPI generates a signed OAuth state.

4. User is sent to Microsoft.

5. Microsoft authenticates the user.

6. User grants delegated User.Read permission.

7. Microsoft redirects to:
   /integrations/microsoft/callback

8. FastAPI validates the OAuth state.

9. Authorization code is exchanged for an access token.

10. FastAPI calls:
    GET https://graph.microsoft.com/v1.0/me

11. Microsoft returns the user's profile.

12. Connection metadata is persisted in PostgreSQL.
```

This demonstrates integration with an external enterprise identity and API platform rather than a simulated external service.

---

## Security

The platform includes several security controls:

- Passwords are never stored in plaintext
- Passwords are hashed using Argon2
- Protected routes require JWT authentication
- Administrator routes enforce role-based authorization
- Customers can access only their own conversations
- Customers can access only their own support tickets
- Knowledge-base uploads require administrator access
- OAuth state is cryptographically signed and expires
- Microsoft client credentials remain server-side
- Environment secrets are excluded from Git
- API keys remain server-side
- Microsoft access tokens are not exposed through the public API

---

## Deployment

Production uses:

```text
GitHub
   |
   v
Render
   |
   ├── Dockerized FastAPI Web Service
   |
   └── Managed PostgreSQL Database
```

Every push to the main branch can trigger a new deployment.

The Docker startup process creates missing database tables before FastAPI starts.

### Live API

https://ai-business-operations-platform.onrender.com/docs

---

## Portfolio Skills Demonstrated

This project demonstrates practical experience with:

- Python backend development
- FastAPI
- REST APIs
- PostgreSQL
- SQLAlchemy
- Authentication
- Authorization
- JWT
- OAuth 2.0
- Microsoft Graph
- Microsoft Entra ID
- Third-party API integration
- JSON APIs
- AI agents
- OpenAI tool calling
- RAG
- Business workflows
- Automated testing
- API mocking
- Docker
- Git
- GitHub
- Cloud deployment
- Environment configuration
- Secret management

---

## Purpose

This project was built as a practical backend, AI engineering, and enterprise integration portfolio project.

It demonstrates how a modern AI-enabled B2B application can combine:

```text
Backend Engineering
        +
Artificial Intelligence
        +
Business Workflows
        +
Enterprise APIs
        +
Authentication
        +
Database Persistence
        +
Automated Testing
        +
Cloud Deployment
```

The goal is to represent the type of architecture and engineering work used in real AI-enabled business software.