from sqlalchemy import select

from rentalapp.core.repository import BaseRepository
from rentalapp.modules.properties.models import Property, Unit


class PropertyRepository(BaseRepository[Property]):
    model = Property

    def list_by_owner(self, owner_id: int, offset: int = 0, limit: int = 100) -> list[Property]:
        stmt = select(Property).where(Property.owner_id == owner_id).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())


class UnitRepository(BaseRepository[Unit]):
    model = Unit

    def list_by_property(self, property_id: int) -> list[Unit]:
        stmt = select(Unit).where(Unit.property_id == property_id)
        return list(self.db.scalars(stmt).all())
