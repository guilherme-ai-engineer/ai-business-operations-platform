import routers.knowledge as knowledge_router


def login(
    client,
    email: str,
    password: str,
) -> str:
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()[
        "access_token"
    ]


def authorization_header(
    token: str,
) -> dict:
    return {
        "Authorization": (
            f"Bearer {token}"
        )
    }


def test_home(client):
    response = client.get("/")

    assert response.status_code == 200

    assert response.json() == {
        "app": (
            "AI Business Operations Platform"
        ),
        "status": "running",
    }


def test_login(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "john@example.com",
            "password": "MyPassword123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_auth_me(client):
    token = login(
        client,
        "john@example.com",
        "MyPassword123",
    )

    response = client.get(
        "/auth/me",
        headers=authorization_header(
            token
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == (
        "john@example.com"
    )


def test_customer_cannot_upload_document(
    client,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        knowledge_router,
        "KNOWLEDGE_BASE_DIR",
        tmp_path,
    )

    token = login(
        client,
        "emma@example.com",
        "EmmaPassword123",
    )

    response = client.post(
        "/documents",
        headers=authorization_header(
            token
        ),
        files={
            "file": (
                "test.txt",
                b"Test document",
                "text/plain",
            )
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "Administrator access required."
        )
    }


def test_admin_can_upload_document(
    client,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        knowledge_router,
        "KNOWLEDGE_BASE_DIR",
        tmp_path,
    )

    token = login(
        client,
        "john@example.com",
        "MyPassword123",
    )

    response = client.post(
        "/documents",
        headers=authorization_header(
            token
        ),
        files={
            "file": (
                "test.txt",
                b"Test document",
                "text/plain",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "test.txt"
    assert data["status"] == "uploaded"

    assert (
        tmp_path / "test.txt"
    ).exists()