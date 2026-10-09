from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rentalapp.core.deps import get_current_user, require_roles
from rentalapp.database import get_db
from rentalapp.modules.properties.schemas import (
    PropertyCreate,
    PropertyRead,
    PropertyUpdate,
    UnitCreate,
    UnitRead,
    UnitUpdate,
)
from rentalapp.modules.properties.service import PropertyService
from rentalapp.modules.users.models import User, UserRole

router = APIRouter(prefix="/api/v1/properties", tags=["properties"])


@router.post("", response_model=PropertyRead, status_code=201)
def create_property(
    data: PropertyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.LANDLORD)),
) -> PropertyRead:
    return PropertyService(db).create(data, user)


@router.get("", response_model=list[PropertyRead])
def list_properties(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[PropertyRead]:
    return PropertyService(db).list_for_user(user)


@router.get("/{property_id}", response_model=PropertyRead)
def get_property(property_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return PropertyService(db).get_for_user(property_id, user)


@router.patch("/{property_id}", response_model=PropertyRead)
def update_property(
    property_id: int,
    data: PropertyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.LANDLORD)),
):
    return PropertyService(db).update(property_id, data, user)


@router.delete("/{property_id}", status_code=204)
def delete_property(
    property_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.LANDLORD)),
) -> None:
    PropertyService(db).delete(property_id, user)


@router.post("/{property_id}/units", response_model=UnitRead, status_code=201)
def add_unit(
    property_id: int,
    data: UnitCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.LANDLORD)),
):
    return PropertyService(db).add_unit(property_id, data, user)


@router.get("/{property_id}/units", response_model=list[UnitRead])
def list_units(property_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return PropertyService(db).list_units(property_id, user)


@router.get("/units/{unit_id}", response_model=UnitRead)
def get_unit(unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return PropertyService(db).get_unit_for_user(unit_id, user)


@router.patch("/units/{unit_id}", response_model=UnitRead)
def update_unit(
    unit_id: int,
    data: UnitUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.LANDLORD)),
):
    return PropertyService(db).update_unit(unit_id, data, user)
