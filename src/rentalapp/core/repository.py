from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from rentalapp.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic CRUD over a single SQLAlchemy model.

    Each module's repository subclasses this and adds domain-specific
    queries (e.g. "find units by property"), so new modules get basic
    persistence for free and only write the queries that are actually
    special to them.
    """

    model: type[ModelType]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, id_: int) -> ModelType | None:
        return self.db.get(self.model, id_)

    def list(self, offset: int = 0, limit: int = 100) -> list[ModelType]:
        stmt = select(self.model).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    def add(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelType) -> None:
        self.db.delete(obj)
        self.db.commit()
