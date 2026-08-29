# AI Business Operations Platform

An AI-powered backend platform for customer support and business operations, built with FastAPI, PostgreSQL, OpenAI, RAG, JWT authentication, automated testing, and Docker.

The project simulates a real B2B software platform where customers can interact with an AI support agent, access business data, maintain persistent conversations, create support tickets, and communicate with administrators.

## Live Demo

The API is publicly deployed on Render.

**Interactive Swagger documentation:**

https://ai-business-operations-platform.onrender.com/docs

> The free Render instance can take up to about one minute to wake up after a period of inactivity.

---

## Features

### AI Support Agent

- OpenAI-powered customer support agent
- AI tool calling for business operations
- Order status lookup
- Customer order lookup
- Company knowledge search
- Automatic conversation title generation

### RAG Knowledge Base

- Retrieval-Augmented Generation
- Company policy document retrieval
- TXT and PDF document support
- Admin-only document uploads
- Automatic knowledge index refresh

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
- Store AI conversation memory in the database

### Customer Support System

- AI-classified support tickets
- Ticket categories and priorities
- AI-generated suggested responses
- Customer-to-admin replies
- Admin-to-customer replies

Ticket workflow:

```text
received
   ↓
in_progress
   ↓
resolved
   ↓
closed
```

Closed tickets cannot receive new replies unless they are reopened by an administrator.

### Automated Testing

The project includes automated API tests using `pytest` and FastAPI `TestClient`.

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

External AI calls are mocked during automated tests to keep the test suite fast, deterministic, and independent from API usage.

---

## Tech Stack

### Backend

- Python 3.12
- FastAPI
- Pydantic
- SQLAlchemy

### Database

- PostgreSQL
- Psycopg 3

### AI

- OpenAI API
- AI tool calling
- Retrieval-Augmented Generation (RAG)

### Authentication

- JWT
- Argon2 password hashing

### Testing

- pytest
- FastAPI TestClient

### Infrastructure

- Docker
- Docker Compose
- Render

---

## Architecture

```text
                         Internet
                            |
                            v
                    FastAPI Backend
                            |
          +-----------------+-----------------+
          |                 |                 |
          v                 v                 v
   Authentication       AI Agent        Support System
          |                 |                 |
          |          +------+-------+         |
          |          |              |         |
          v          v              v         v
      PostgreSQL   OpenAI      RAG Knowledge Base
                       |
                       v
                 Business Tools
                       |
                       v
                   PostgreSQL
```

Cloud deployment:

```text
Browser / Client
       |
       v
Render Web Service
       |
       v
Dockerized FastAPI
       |
       +---------> OpenAI API
       |
       +---------> RAG Knowledge Base
       |
       v
Render PostgreSQL
```

---

## Project Structure

```text
ai-business-operations-platform/
│
├── routers/
│   ├── __init__.py
│   ├── auth.py
│   ├── conversations.py
│   ├── support.py
│   └── knowledge.py
│
├── tests/
│   ├── conftest.py
│   └── test_api.py
│
├── knowledge_base/
│
├── agent_service.py
├── ai_service.py
├── auth_service.py
├── conversation_service.py
├── order_service.py
├── rag_service.py
│
├── database.py
├── dependencies.py
├── models.py
├── main.py
│
├── create_tables.py
├── seed_orders.py
│
├── .env.example
├── .gitignore
├── .dockerignore
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Environment Configuration

The repository contains an example configuration file:

```text
.env.example
```

Copy it to create your local `.env` file:

```bash
cp .env.example .env
```

Then configure the required values inside `.env`.

Example:

```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/database_name

OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=your_openai_model

JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

The real `.env` file is excluded from Git and must never be committed.

---

## Running with Docker

Docker Compose starts both the FastAPI backend and PostgreSQL database.

Build and start the services:

```bash
docker compose up --build
```

The architecture will be:

```text
Docker Compose
│
├── FastAPI container
│
└── PostgreSQL container
```

PostgreSQL data is persisted using a Docker volume.

Open the local Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Stop the containers with:

```bash
docker compose down
```

---

## Running Without Docker

Install the dependencies:

```bash
pip install -r requirements.txt
```

Configure your `.env` file and make sure PostgreSQL is available.

Create the database tables:

```bash
python create_tables.py
```

Start FastAPI:

```bash
uvicorn main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

---

## Running Tests

Run the complete automated test suite:

```bash
python -m pytest -v
```

The current suite contains **10 automated API tests**.

A separate temporary database is used during testing so development data is not modified.

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
- Environment secrets are excluded from Git
- API keys remain server-side

---

## Deployment

The production demo is deployed using:

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

The application automatically creates the required database tables when the Docker container starts.

Live Swagger documentation:

https://ai-business-operations-platform.onrender.com/docs

---

## Purpose

This project was built as a practical backend and AI engineering portfolio project.

It demonstrates how an AI-enabled B2B application can combine:

- REST APIs
- authentication
- authorization
- relational databases
- persistent data
- AI agents
- AI tool calling
- Retrieval-Augmented Generation
- business workflows
- automated testing
- Docker
- cloud deployment

The project is designed to represent the architecture and engineering practices used in real AI-enabled business applications.