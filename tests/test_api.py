import routers.conversations as conversations_router
import routers.knowledge as knowledge_router
import routers.microsoft as microsoft_router
import routers.support as support_router


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

    return response.json()["access_token"]


def authorization_header(
    token: str,
) -> dict:
    return {
        "Authorization": f"Bearer {token}"
    }


def test_home(client):
    response = client.get("/")

    assert response.status_code == 200

    assert response.json() == {
        "app": "AI Business Operations Platform",
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
        headers=authorization_header(token),
    )

    assert response.status_code == 200
    assert response.json()["email"] == "john@example.com"


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
        headers=authorization_header(token),
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
        "detail": "Administrator access required."
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
        headers=authorization_header(token),
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
    assert (tmp_path / "test.txt").exists()


def test_create_and_list_conversations(client):
    token = login(
        client,
        "john@example.com",
        "MyPassword123",
    )

    headers = authorization_header(token)

    create_response = client.post(
        "/conversations",
        headers=headers,
    )

    assert create_response.status_code == 200

    conversation_id = create_response.json()[
        "conversation_id"
    ]

    list_response = client.get(
        "/conversations",
        headers=headers,
    )

    assert list_response.status_code == 200

    conversations = list_response.json()

    assert len(conversations) == 1
    assert conversations[0]["conversation_id"] == (
        conversation_id
    )
    assert conversations[0]["title"] == "New conversation"


def test_user_cannot_access_another_users_conversation(
    client,
):
    john_token = login(
        client,
        "john@example.com",
        "MyPassword123",
    )

    create_response = client.post(
        "/conversations",
        headers=authorization_header(john_token),
    )

    conversation_id = create_response.json()[
        "conversation_id"
    ]

    emma_token = login(
        client,
        "emma@example.com",
        "EmmaPassword123",
    )

    response = client.get(
        (
            f"/conversations/"
            f"{conversation_id}/messages"
        ),
        headers=authorization_header(emma_token),
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Conversation not found "
            "for this customer."
        )
    }


def test_create_support_ticket_with_mocked_ai(
    client,
    monkeypatch,
):
    def fake_analysis(message):
        return {
            "category": "shipping",
            "priority": "medium",
            "suggested_response": (
                "We are checking your shipment."
            ),
            "knowledge_source": "shipping_policy.txt",
        }

    monkeypatch.setattr(
        support_router,
        "analyze_support_message",
        fake_analysis,
    )

    token = login(
        client,
        "emma@example.com",
        "EmmaPassword123",
    )

    response = client.post(
        "/support",
        headers=authorization_header(token),
        json={
            "customer_name": "Emma Smith",
            "message": "My order has not arrived.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "emma@example.com"
    assert data["category"] == "shipping"
    assert data["priority"] == "medium"
    assert data["status"] == "received"


def test_closed_ticket_cannot_receive_customer_reply(
    client,
    monkeypatch,
):
    def fake_analysis(message):
        return {
            "category": "shipping",
            "priority": "medium",
            "suggested_response": (
                "We are checking your shipment."
            ),
            "knowledge_source": "shipping_policy.txt",
        }

    monkeypatch.setattr(
        support_router,
        "analyze_support_message",
        fake_analysis,
    )

    emma_token = login(
        client,
        "emma@example.com",
        "EmmaPassword123",
    )

    emma_headers = authorization_header(emma_token)

    create_response = client.post(
        "/support",
        headers=emma_headers,
        json={
            "customer_name": "Emma Smith",
            "message": "My order has not arrived.",
        },
    )

    assert create_response.status_code == 200

    ticket_id = create_response.json()["ticket_id"]

    john_token = login(
        client,
        "john@example.com",
        "MyPassword123",
    )

    close_response = client.patch(
        f"/admin/tickets/{ticket_id}",
        headers=authorization_header(john_token),
        json={
            "status": "closed",
        },
    )

    assert close_response.status_code == 200
    assert close_response.json()["status"] == "closed"

    reply_response = client.post(
        f"/tickets/{ticket_id}/replies",
        headers=emma_headers,
        json={
            "message": "Do you have an update?",
        },
    )

    assert reply_response.status_code == 400

    assert reply_response.json() == {
        "detail": (
            "Closed tickets cannot receive "
            "new replies."
        )
    }


def test_agent_chat_with_mocked_ai(
    client,
    monkeypatch,
):
    def fake_run_order_agent(
        message,
        customer_email,
        conversation_id,
    ):
        return "Your order is in transit."

    def fake_generate_title(message):
        return "Order Status"

    monkeypatch.setattr(
        conversations_router,
        "run_order_agent",
        fake_run_order_agent,
    )

    monkeypatch.setattr(
        conversations_router,
        "generate_conversation_title",
        fake_generate_title,
    )

    token = login(
        client,
        "john@example.com",
        "MyPassword123",
    )

    headers = authorization_header(token)

    create_response = client.post(
        "/conversations",
        headers=headers,
    )

    assert create_response.status_code == 200

    conversation_id = create_response.json()[
        "conversation_id"
    ]

    response = client.post(
        "/agent/chat",
        headers=headers,
        json={
            "conversation_id": conversation_id,
            "message": "Where is my order?",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "response": "Your order is in transit."
    }

    conversations_response = client.get(
        "/conversations",
        headers=headers,
    )

    assert conversations_response.status_code == 200

    conversations = conversations_response.json()

    assert conversations[0]["title"] == "Order Status"


def test_microsoft_status_is_disconnected(client):
    token = login(
        client,
        "john@example.com",
        "MyPassword123",
    )

    response = client.get(
        "/integrations/microsoft/status",
        headers=authorization_header(token),
    )

    assert response.status_code == 200

    assert response.json() == {
        "connected": False,
        "microsoft_connection": None,
    }


def test_microsoft_callback_saves_connection(
    client,
    monkeypatch,
):
    def fake_decode_oauth_state(state):
        return 1

    def fake_exchange_code_for_token(code):
        return {
            "access_token": "fake-access-token"
        }

    def fake_get_microsoft_profile(access_token):
        return {
            "id": "microsoft-user-123",
            "displayName": "John Microsoft",
            "mail": "john@microsoft.example",
            "userPrincipalName": (
                "john@microsoft.example"
            ),
        }

    monkeypatch.setattr(
        microsoft_router,
        "decode_oauth_state",
        fake_decode_oauth_state,
    )

    monkeypatch.setattr(
        microsoft_router,
        "exchange_code_for_token",
        fake_exchange_code_for_token,
    )

    monkeypatch.setattr(
        microsoft_router,
        "get_microsoft_profile",
        fake_get_microsoft_profile,
    )

    callback_response = client.get(
        "/integrations/microsoft/callback",
        params={
            "code": "fake-code",
            "state": "fake-state",
        },
    )

    assert callback_response.status_code == 200

    callback_data = callback_response.json()

    assert callback_data["status"] == "connected"
    assert callback_data["local_user"] == (
        "john@example.com"
    )

    assert callback_data[
        "microsoft_connection"
    ]["microsoft_user_id"] == (
        "microsoft-user-123"
    )

    assert callback_data[
        "microsoft_connection"
    ]["display_name"] == (
        "John Microsoft"
    )

    token = login(
        client,
        "john@example.com",
        "MyPassword123",
    )

    status_response = client.get(
        "/integrations/microsoft/status",
        headers=authorization_header(token),
    )

    assert status_response.status_code == 200

    status_data = status_response.json()

    assert status_data["connected"] is True

    assert status_data[
        "microsoft_connection"
    ]["email"] == "john@microsoft.example"


def test_microsoft_disconnect(
    client,
    monkeypatch,
):
    def fake_decode_oauth_state(state):
        return 1

    def fake_exchange_code_for_token(code):
        return {
            "access_token": "fake-access-token"
        }

    def fake_get_microsoft_profile(access_token):
        return {
            "id": "microsoft-user-123",
            "displayName": "John Microsoft",
            "mail": "john@microsoft.example",
            "userPrincipalName": (
                "john@microsoft.example"
            ),
        }

    monkeypatch.setattr(
        microsoft_router,
        "decode_oauth_state",
        fake_decode_oauth_state,
    )

    monkeypatch.setattr(
        microsoft_router,
        "exchange_code_for_token",
        fake_exchange_code_for_token,
    )

    monkeypatch.setattr(
        microsoft_router,
        "get_microsoft_profile",
        fake_get_microsoft_profile,
    )

    callback_response = client.get(
        "/integrations/microsoft/callback",
        params={
            "code": "fake-code",
            "state": "fake-state",
        },
    )

    assert callback_response.status_code == 200

    token = login(
        client,
        "john@example.com",
        "MyPassword123",
    )

    headers = authorization_header(token)

    disconnect_response = client.delete(
        "/integrations/microsoft",
        headers=headers,
    )

    assert disconnect_response.status_code == 200

    assert disconnect_response.json() == {
        "status": "disconnected"
    }

    status_response = client.get(
        "/integrations/microsoft/status",
        headers=headers,
    )

    assert status_response.status_code == 200

    assert status_response.json() == {
        "connected": False,
        "microsoft_connection": None,
    }