import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


os.environ["JWT_SECRET_KEY"] = "pytest-secret-key"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_EXPIRE_MINUTES"] = "60"

os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["OPENAI_MODEL"] = "test-model"


from auth_service import hash_password
from database import Base, get_db
from main import app
from models import User


test_engine = create_engine(
    "sqlite://",
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db

    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_test_database():
    Base.metadata.drop_all(
        bind=test_engine
    )

    Base.metadata.create_all(
        bind=test_engine
    )

    db = TestingSessionLocal()

    try:
        john = User(
            email="john@example.com",
            password_hash=hash_password(
                "MyPassword123"
            ),
            role="admin",
        )

        emma = User(
            email="emma@example.com",
            password_hash=hash_password(
                "EmmaPassword123"
            ),
            role="customer",
        )

        db.add(john)
        db.add(emma)
        db.commit()

    finally:
        db.close()

    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client