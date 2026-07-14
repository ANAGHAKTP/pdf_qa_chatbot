from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import Document


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        filename: str,
        filepath: str,
        file_size: int,
        user_id: int,
        folder_id: Optional[int] = None,
        s3_key: Optional[str] = None
    ) -> Document:
        doc = Document(
            filename=filename,
            filepath=filepath,
            file_size=file_size,
            user_id=user_id,
            folder_id=folder_id,
            s3_key=s3_key,
            status="indexing"
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get_by_id(self, doc_id: int) -> Optional[Document]:
        return self.db.query(Document).filter(Document.id == doc_id).first()

    def get_by_user(self, user_id: int) -> List[Document]:
        return self.db.query(Document).filter(Document.user_id == user_id).all()

    def get_by_folder(self, user_id: int, folder_id: Optional[int]) -> List[Document]:
        return self.db.query(Document).filter(
            Document.user_id == user_id,
            Document.folder_id == folder_id
        ).all()

    def delete(self, doc_id: int) -> bool:
        doc = self.get_by_id(doc_id)
        if doc:
            self.db.delete(doc)
            self.db.commit()
            return True
        return False

    def rename(self, doc_id: int, new_name: str) -> Optional[Document]:
        doc = self.get_by_id(doc_id)
        if doc:
            doc.filename = new_name
            self.db.commit()
            self.db.refresh(doc)
            return doc
        return None

    def update_status(self, doc_id: int, status: str, chunk_count: int = 0) -> Optional[Document]:
        doc = self.get_by_id(doc_id)
        if doc:
            doc.status = status
            doc.chunk_count = chunk_count
            self.db.commit()
            self.db.refresh(doc)
            return doc
        return None
