import pytest
import json
import time

from app.db.models import User, Document, Folder, ChatSession, ChatMessage


def test_complete_e2e_flow(client, db_session):
    # 1. Register a new user (expects 201 Created)
    reg_email = f"e2e_verify_{int(time.time())}@docmind.com"
    reg_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": reg_email,
            "password": "e2e_password_123",
            "full_name": "E2E Verification User"
        }
    )
    assert reg_response.status_code in [200, 201]
    
    # 2. Login to retrieve JWT Access token
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": reg_email,
            "password": "e2e_password_123"
        }
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    # 3. Create a Folder
    folder_response = client.post(
        "/api/v1/documents/folders",
        headers=headers,
        json={"name": "E2E Test Folder", "parent_id": None}
    )
    assert folder_response.status_code in [200, 201]
    folder_id = folder_response.json()["id"]
    
    # 4. Upload descriptive sample document (resume_sample.pdf contents)
    pdf_content = b"%PDF-1.4 mock resume content with work history at Google and skills in Python"
    upload_response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("resume_sample.pdf", pdf_content, "application/pdf")},
        data={"folder_id": str(folder_id)}
    )
    assert upload_response.status_code in [200, 201, 202]
    doc_id = upload_response.json()["id"]
    
    # 5. Verify metadata exists in DB
    contents_response = client.get(f"/api/v1/documents/contents?parent_id={folder_id}", headers=headers)
    assert contents_response.status_code == 200
    docs = contents_response.json()["documents"]
    assert any(d["id"] == doc_id for d in docs)
    
    # 6. Create a Chat Session
    session_response = client.post(
        "/api/v1/chat/sessions",
        headers=headers,
        json={"title": "E2E Conversation"}
    )
    assert session_response.status_code in [200, 201]
    session_id = session_response.json()["id"]
    
    # 7. Ask a Question with RAG Active (triggers mock RAG stream in test env)
    query_response = client.post(
        "/api/v1/chat/query",
        headers=headers,
        json={
            "session_id": session_id,
            "query": "Isolate this candidate's programming languages and skills.",
            "doc_ids": [doc_id]
        }
    )
    assert query_response.status_code == 200
    stream_content = query_response.text
    assert "event: citations" in stream_content
    assert "event: message" in stream_content
    assert "event: metrics" in stream_content
    
    # 8. Run Document Intelligence Analysis
    analysis_response = client.post(
        f"/api/v1/chat/documents/{doc_id}/analyze",
        headers=headers
    )
    assert analysis_response.status_code == 200
    analysis = analysis_response.json()
    assert "summary" in analysis
    assert "action_items" in analysis
    assert "risks" in analysis
    
    # 9. Make the current user an admin to check stats
    user_obj = db_session.query(User).filter(User.email == reg_email).first()
    assert user_obj is not None
    user_obj.is_admin = True
    db_session.commit()
        
    stats_response = client.get("/api/v1/admin/stats", headers=headers)
    assert stats_response.status_code == 200
    assert stats_response.json()["documents_count"] >= 1
    
    # 10. Verify metrics scrape
    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert "docmind_http_requests_total" in metrics_response.text
