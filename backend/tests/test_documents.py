import io
import pytest


def get_auth_headers(client, email, password):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_folder(client, test_user):
    headers = get_auth_headers(client, test_user.email, "password123")
    
    response = client.post(
        "/api/v1/documents/folders",
        json={"name": "Contracts"},
        headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Contracts"
    assert data["parent_id"] is None
    assert data["user_id"] == test_user.id
    
    # Create subfolder
    sub_response = client.post(
        "/api/v1/documents/folders",
        json={"name": "2024", "parent_id": data["id"]},
        headers=headers
    )
    assert sub_response.status_code == 201
    sub_data = sub_response.json()
    assert sub_data["name"] == "2024"
    assert sub_data["parent_id"] == data["id"]


def test_create_folder_invalid_parent(client, test_user, admin_user):
    # Admin creates folder
    admin_headers = get_auth_headers(client, admin_user.email, "adminpassword")
    admin_folder = client.post(
        "/api/v1/documents/folders",
        json={"name": "Admin Only"},
        headers=admin_headers
    ).json()
    
    # User tries to create subfolder under admin folder
    user_headers = get_auth_headers(client, test_user.email, "password123")
    response = client.post(
        "/api/v1/documents/folders",
        json={"name": "Attempt", "parent_id": admin_folder["id"]},
        headers=user_headers
    )
    assert response.status_code == 404


def test_upload_and_manage_document(client, test_user):
    headers = get_auth_headers(client, test_user.email, "password123")
    
    # Create dummy pdf file content
    pdf_content = b"%PDF-1.4 dummy pdf content for testing upload"
    file_obj = ("test_doc.pdf", pdf_content)
    
    # Upload document
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": file_obj},
        headers=headers
    )
    assert response.status_code == 202
    data = response.json()
    assert data["filename"] == "test_doc.pdf"
    assert data["status"] == "indexing"
    
    doc_id = data["id"]
    
    # Rename document
    rename_response = client.put(
        f"/api/v1/documents/{doc_id}/rename",
        json={"new_filename": "renamed_doc.pdf"},
        headers=headers
    )
    assert rename_response.status_code == 200
    assert rename_response.json()["filename"] == "renamed_doc.pdf"
    
    # Get contents
    contents_response = client.get(
        "/api/v1/documents/contents",
        headers=headers
    )
    assert contents_response.status_code == 200
    docs = contents_response.json()["documents"]
    assert len(docs) == 1
    assert docs[0]["filename"] == "renamed_doc.pdf"
    assert docs[0]["status"] == "ready"
    assert docs[0]["chunk_count"] == 1
    
    # Delete document
    delete_response = client.delete(
        f"/api/v1/documents/{doc_id}",
        headers=headers
    )
    assert delete_response.status_code == 204
    
    # Verify deleted
    contents_response2 = client.get(
        "/api/v1/documents/contents",
        headers=headers
    )
    assert len(contents_response2.json()["documents"]) == 0


def test_document_cross_user_access(client, test_user, admin_user):
    user_headers = get_auth_headers(client, test_user.email, "password123")
    admin_headers = get_auth_headers(client, admin_user.email, "adminpassword")
    
    # User uploads a file
    pdf_content = b"%PDF-1.4 dummy pdf"
    file_obj = ("user_private.pdf", pdf_content)
    user_doc = client.post(
        "/api/v1/documents/upload",
        files={"file": file_obj},
        headers=user_headers
    ).json()
    
    # Admin tries to rename user file
    rename_response = client.put(
        f"/api/v1/documents/{user_doc['id']}/rename",
        json={"new_filename": "hacked.pdf"},
        headers=admin_headers
    )
    assert rename_response.status_code == 404
    
    # Admin tries to delete user file
    delete_response = client.delete(
        f"/api/v1/documents/{user_doc['id']}",
        headers=admin_headers
    )
    assert delete_response.status_code == 404
