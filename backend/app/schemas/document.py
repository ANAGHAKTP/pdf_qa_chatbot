from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None


class FolderResponse(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentRename(BaseModel):
    new_filename: str


class DocumentResponse(BaseModel):
    id: int
    filename: str
    filepath: str
    file_size: int
    chunk_count: int
    status: str
    s3_key: Optional[str] = None
    folder_id: Optional[int] = None
    created_at: datetime
    doc_metadata: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class FolderContentsResponse(BaseModel):
    folders: List[FolderResponse]
    documents: List[DocumentResponse]
