from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import Folder


class FolderRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str, user_id: int, parent_id: Optional[int] = None) -> Folder:
        folder = Folder(
            name=name,
            user_id=user_id,
            parent_id=parent_id
        )
        self.db.add(folder)
        self.db.commit()
        self.db.refresh(folder)
        return folder

    def get_by_id(self, folder_id: int) -> Optional[Folder]:
        return self.db.query(Folder).filter(Folder.id == folder_id).first()

    def get_by_user(self, user_id: int) -> List[Folder]:
        return self.db.query(Folder).filter(Folder.user_id == user_id).all()

    def get_subfolders(self, user_id: int, parent_id: Optional[int]) -> List[Folder]:
        return self.db.query(Folder).filter(
            Folder.user_id == user_id,
            Folder.parent_id == parent_id
        ).all()

    def delete(self, folder_id: int) -> bool:
        # Note: cascading deletes documents or marks them as unassigned depending on setup.
        # Here we delete the folder entity from DB. Documents will set folder_id to NULL due to SQLAlchemy or we can handle it.
        # Wait, since our models say folder_id = ForeignKey('folders.id'), deleting the folder will set folder_id to NULL.
        folder = self.get_by_id(folder_id)
        if folder:
            self.db.delete(folder)
            self.db.commit()
            return True
        return False

    def rename(self, folder_id: int, new_name: str) -> Optional[Folder]:
        folder = self.get_by_id(folder_id)
        if folder:
            folder.name = new_name
            self.db.commit()
            self.db.refresh(folder)
            return folder
        return None
