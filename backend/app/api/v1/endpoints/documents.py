import io
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_db
from app.db.models import User
from app.schemas.document import FolderCreate, FolderResponse, DocumentResponse, DocumentRename, FolderContentsResponse
from app.services.document import DocumentService

router = APIRouter()


@router.post("/folders", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
def create_folder(
    folder_in: FolderCreate,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new directory/folder for organizing documents."""
    doc_service = DocumentService(db)
    if folder_in.parent_id:
        parent = doc_service.folder_repo.get_by_id(folder_in.parent_id)
        if not parent or parent.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Parent folder not found")
            
    return doc_service.create_folder(
        name=folder_in.name,
        user_id=current_user.id,
        parent_id=folder_in.parent_id
    )


@router.get("/contents", response_model=FolderContentsResponse)
def get_folder_contents(
    parent_id: Optional[int] = None,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db)
):
    """List subfolders and documents inside a specific folder (or root)."""
    doc_service = DocumentService(db)
    if parent_id:
        parent = doc_service.folder_repo.get_by_id(parent_id)
        if not parent or parent.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Folder not found")
            
    folders, docs = doc_service.get_contents(user_id=current_user.id, folder_id=parent_id)

    # Attach enriched metadata dict if available in DB
    enriched_docs = []
    for d in docs:
        d_dict = DocumentResponse.model_validate(d).model_dump()
        if getattr(d, "doc_metadata", None):
            d_dict["doc_metadata"] = d.doc_metadata
        enriched_docs.append(d_dict)

    return {
        "folders": folders,
        "documents": enriched_docs
    }


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    folder_id: Optional[int] = Form(None),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a new PDF document. Starts multimodal ingestion and indexing in background."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDFs are supported."
        )
        
    doc_service = DocumentService(db)
    if folder_id:
        folder = doc_service.folder_repo.get_by_id(folder_id)
        if not folder or folder.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Folder not found")
            
    file_bytes = await file.read()
    
    contents = doc_service.doc_repo.get_by_folder(current_user.id, folder_id)
    for existing_doc in contents:
        if existing_doc.filename == file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A document named '{file.filename}' already exists in this folder."
            )
            
    doc = doc_service.upload_document(
        file_bytes=file_bytes,
        filename=file.filename,
        user_id=current_user.id,
        folder_id=folder_id,
        background_tasks=background_tasks
    )
    return doc


@router.get("/{id}/metadata")
def get_document_metadata(
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve detailed enriched metadata (tables count, figures count, OCR status, language, etc.)."""
    doc_service = DocumentService(db)
    doc = doc_service.doc_repo.get_by_id(id)
    if not doc or doc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found or access denied")

    if getattr(doc, "doc_metadata", None):
        return doc.doc_metadata

    return {
        "doc_id": id,
        "title": doc.filename,
        "page_count": doc.chunk_count or 1,
        "is_scanned": False,
        "ocr_applied": False,
        "table_count": 0,
        "figure_count": 0,
        "language": "en",
        "document_category": "General Document"
    }


@router.get("/{id}/preview")
def preview_document_page(
    id: int,
    page: int = Query(1, ge=1),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Serves document page preview file stream for PDF Preview UI panel."""
    doc_service = DocumentService(db)
    doc = doc_service.doc_repo.get_by_id(id)
    if not doc or doc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found or access denied")

    try:
        file_bytes = doc_service.storage.get_file_bytes(doc.filepath)
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{doc.filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Document file content not found on server: {e}")


@router.put("/{id}/rename", response_model=DocumentResponse)
def rename_document(
    id: int,
    rename_in: DocumentRename,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Rename an existing document."""
    doc_service = DocumentService(db)
    updated_doc = doc_service.rename_document(
        doc_id=id,
        user_id=current_user.id,
        new_filename=rename_in.new_filename
    )
    if not updated_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied"
        )
    return updated_doc


@router.post("/{id}/reindex", response_model=DocumentResponse)
def reindex_document(
    id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Re-trigger background ingestion and indexing for a document."""
    doc_service = DocumentService(db)
    doc = doc_service.doc_repo.get_by_id(id)
    if not doc or doc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found or access denied")

    file_bytes = doc_service.storage.get_file_bytes(doc.filepath)
    doc = doc_service.doc_repo.update_status(id, "indexing", 0)
    background_tasks.add_task(doc_service._process_document, id, file_bytes)
    return doc


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a document from database, storage, and Qdrant vector store."""
    doc_service = DocumentService(db)
    success = doc_service.delete_document(doc_id=id, user_id=current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied"
        )
    return
