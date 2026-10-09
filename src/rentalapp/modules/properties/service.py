from sqlalchemy.orm import Session

from rentalapp.core.exceptions import ForbiddenError, NotFoundError
from rentalapp.modules.properties.models import Property, Unit
from rentalapp.modules.properties.repository import PropertyRepository, UnitRepository
from rentalapp.modules.properties.schemas import PropertyCreate, PropertyUpdate, UnitCreate, UnitUpdate
from rentalapp.modules.users.models import User, UserRole


class PropertyService:
    def __init__(self, db: Session) -> None:
        self.repo = PropertyRepository(db)
        self.unit_repo = UnitRepository(db)

    def create(self, data: PropertyCreate, owner: User) -> Property:
        prop = Property(owner_id=owner.id, **data.model_dump())
        return self.repo.add(prop)

    def get(self, property_id: int) -> Property:
        prop = self.repo.get(property_id)
        if not prop:
            raise NotFoundError(f"Property {property_id} not found")
        return prop

    def get_for_user(self, property_id: int, user: User) -> Property:
        prop = self.get(property_id)
        self._assert_owner_or_admin(prop, user)
        return prop

    def list_for_user(self, user: User, offset: int = 0, limit: int = 100) -> list[Property]:
        if user.role == UserRole.ADMIN:
            return self.repo.list(offset=offset, limit=limit)
        return self.repo.list_by_owner(user.id, offset=offset, limit=limit)

    def update(self, property_id: int, data: PropertyUpdate, user: User) -> Property:
        prop = self.get_for_user(property_id, user)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(prop, field, value)
        self.repo.db.commit()
        self.repo.db.refresh(prop)
        return prop

    def delete(self, property_id: int, user: User) -> None:
        prop = self.get_for_user(property_id, user)
        self.repo.delete(prop)

    def add_unit(self, property_id: int, data: UnitCreate, user: User) -> Unit:
        prop = self.get_for_user(property_id, user)
        unit = Unit(property_id=prop.id, **data.model_dump())
        return self.unit_repo.add(unit)

    def list_units(self, property_id: int, user: User) -> list[Unit]:
        self.get_for_user(property_id, user)
        return self.unit_repo.list_by_property(property_id)

    def get_unit(self, unit_id: int) -> Unit:
        unit = self.unit_repo.get(unit_id)
        if not unit:
            raise NotFoundError(f"Unit {unit_id} not found")
        return unit

    def get_unit_for_user(self, unit_id: int, user: User) -> Unit:
        unit = self.get_unit(unit_id)
        self.get_for_user(unit.property_id, user)
        return unit

    def update_unit(self, unit_id: int, data: UnitUpdate, user: User) -> Unit:
        unit = self.get_unit(unit_id)
        self.get_for_user(unit.property_id, user)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(unit, field, value)
        self.unit_repo.db.commit()
        self.unit_repo.db.refresh(unit)
        return unit

    @staticmethod
    def _assert_owner_or_admin(prop: Property, user: User) -> None:
        if user.role != UserRole.ADMIN and prop.owner_id != user.id:
            raise ForbiddenError("You do not have access to this property")
