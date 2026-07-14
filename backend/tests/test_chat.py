import json
import pytest
import io


def get_auth_headers(client, email, password):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_manage_chat_sessions(client, test_user):
    headers = get_auth_headers(client, test_user.email, "password123")
    
    # Create session
    response = client.post(
        "/api/v1/chat/sessions",
        json={"title": "Contract Review"},
        headers=headers
    )
    assert response.status_code == 201
    session_data = response.json()
    assert session_data["title"] == "Contract Review"
    assert "id" in session_data
    
    session_id = session_data["id"]
    
    # List sessions
    list_response = client.get(
        "/api/v1/chat/sessions",
        headers=headers
    )
    assert list_response.status_code == 200
    sessions = list_response.json()
    assert len(sessions) >= 1
    assert any(s["id"] == session_id for s in sessions)
    
    # Get session details/history
    details_response = client.get(
        f"/api/v1/chat/sessions/{session_id}",
        headers=headers
    )
    assert details_response.status_code == 200
    details = details_response.json()
    assert details["title"] == "Contract Review"
    assert len(details["messages"]) == 0  # no messages yet
    
    # Delete session
    delete_response = client.delete(
        f"/api/v1/chat/sessions/{session_id}",
        headers=headers
    )
    assert delete_response.status_code == 204
    
    # Verify deleted
    list_response2 = client.get(
        "/api/v1/chat/sessions",
        headers=headers
    )
    assert not any(s["id"] == session_id for s in list_response2.json())


def test_chat_query_streaming_and_feedback(client, test_user):
    headers = get_auth_headers(client, test_user.email, "password123")
    
    # 1. Create a folder & upload a mock PDF document first
    pdf_content = b"%PDF-1.4 mock content for indexing"
    file_obj = ("test_doc.pdf", pdf_content)
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": file_obj},
        headers=headers
    )
    assert upload_response.status_code == 202
    doc_id = upload_response.json()["id"]

    # 2. Create a chat session
    session = client.post(
        "/api/v1/chat/sessions",
        json={"title": "Doc Q&A"},
        headers=headers
    ).json()
    session_id = session["id"]

    # 3. Submit a query to chat streaming
    # We must receive citations event first, then message chunks, then metrics
    # Note: testing SSE endpoints using TestClient.post with stream=True or normal read
    response = client.post(
        "/api/v1/chat/query",
        json={
            "session_id": session_id,
            "query": "What is the content of this document?",
            "doc_ids": [doc_id]
        },
        headers=headers
    )
    assert response.status_code == 200
    
    # Read the event stream line-by-line
    events = []
    for line in response.iter_lines():
        if line:
            events.append(line.decode("utf-8") if isinstance(line, bytes) else line)

    # Process and verify the SSE events
    events_joined = "\n".join(events)
    assert "event: citations" in events_joined
    assert "event: message" in events_joined
    assert "event: metrics" in events_joined
    assert "event: close" in events_joined

    # Fetch history to verify user and assistant messages were saved in DB
    history = client.get(
        f"/api/v1/chat/sessions/{session_id}",
        headers=headers
    ).json()
    
    assert len(history["messages"]) == 2
    user_msg = history["messages"][0]
    assistant_msg = history["messages"][1]
    
    assert user_msg["role"] == "user"
    assert user_msg["content"] == "What is the content of this document?"
    
    assert assistant_msg["role"] == "assistant"
    assert len(assistant_msg["citations"]) >= 1
    assert assistant_msg["metrics"]["total_time_ms"] > 0
    
    message_id = assistant_msg["id"]
    
    # 4. Submit upvote feedback for assistant message
    feedback_response = client.post(
        "/api/v1/chat/feedback",
        json={
            "message_id": message_id,
            "rating": 1,
            "comment": "Very accurate answer!"
        },
        headers=headers
    )
    assert feedback_response.status_code == 200
    fb_data = feedback_response.json()
    assert fb_data["rating"] == 1
    assert fb_data["comment"] == "Very accurate answer!"
