import os
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks

from app.db.models import User, Document, Folder
from app.repositories.document import DocumentRepository
from app.repositories.folder import FolderRepository
from app.services.storage import get_storage_service


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.folder_repo = FolderRepository(db)
        self.storage = get_storage_service()

    def create_folder(self, name: str, user_id: int, parent_id: Optional[int] = None) -> Folder:
        return self.folder_repo.create(name=name, user_id=user_id, parent_id=parent_id)

    def get_contents(self, user_id: int, folder_id: Optional[int] = None) -> Tuple[List[Folder], List[Document]]:
        folders = self.folder_repo.get_subfolders(user_id=user_id, parent_id=folder_id)
        documents = self.doc_repo.get_by_folder(user_id=user_id, folder_id=folder_id)
        return folders, documents

    def upload_document(
        self,
        file_bytes: bytes,
        filename: str,
        user_id: int,
        folder_id: Optional[int] = None,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Document:
        # Save file to storage
        storage_key = self.storage.save_file(file_bytes, filename, user_id)
        
        # Create DB record with "indexing" status
        doc = self.doc_repo.create(
            filename=filename,
            filepath=storage_key,
            file_size=len(file_bytes),
            user_id=user_id,
            folder_id=folder_id,
            s3_key=storage_key if os.getenv("USE_S3") == "True" else None
        )
        
        # Trigger background processing
        if background_tasks:
            background_tasks.add_task(self._process_document, doc.id, file_bytes)
        else:
            # Inline processing for synchronous execution (e.g. testing)
            self._process_document(doc.id, file_bytes)
            
        return doc

    def delete_document(self, doc_id: int, user_id: int) -> bool:
        doc = self.doc_repo.get_by_id(doc_id)
        if not doc or doc.user_id != user_id:
            return False
            
        # Delete file from storage
        self.storage.delete_file(doc.filepath)
        
        # Delete embeddings from vector store
        try:
            self._delete_vector_embeddings(doc.id)
        except Exception as e:
            print(f"⚠️ Warning: Could not delete embeddings for document {doc_id}: {e}")
            
        # Delete from database
        return self.doc_repo.delete(doc_id)

    def rename_document(self, doc_id: int, user_id: int, new_filename: str) -> Optional[Document]:
        doc = self.doc_repo.get_by_id(doc_id)
        if not doc or doc.user_id != user_id:
            return None
        return self.doc_repo.rename(doc_id, new_filename)

    def _process_document(self, doc_id: int, file_bytes: bytes):
        """
        Background task to process PDF, create chunks, embed, and load into Chroma.
        This stub will be fully implemented in Phase 4.
        """
        try:
            # Import indexing task lazily to prevent circular imports
            from app.ai.pipeline import ingest_document_pipeline
            chunk_count = ingest_document_pipeline(doc_id, file_bytes)
            self.doc_repo.update_status(doc_id, "ready", chunk_count)
        except Exception as e:
            print(f"❌ Document processing failed for doc {doc_id}: {e}")
            self.doc_repo.update_status(doc_id, "failed")

    def _delete_vector_embeddings(self, doc_id: int):
        """
        Remove document chunks from Chroma.
        This stub will be fully implemented in Phase 4.
        """
        from app.ai.pipeline import remove_document_embeddings
        remove_document_embeddings(doc_id)
