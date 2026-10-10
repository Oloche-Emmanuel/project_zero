from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rentalapp.core.deps import get_current_user, require_roles
from rentalapp.database import get_db
from rentalapp.modules.maintenance.schemas import (
    MaintenanceRequestCreate,
    MaintenanceRequestRead,
    MaintenanceRequestUpdate,
)
from rentalapp.modules.maintenance.service import MaintenanceService
from rentalapp.modules.users.models import User, UserRole

router = APIRouter(prefix="/api/v1/maintenance-requests", tags=["maintenance"])

_staff = require_roles(UserRole.ADMIN, UserRole.LANDLORD)


@router.post("", response_model=MaintenanceRequestRead, status_code=201)
def create_request(
    data: MaintenanceRequestCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> MaintenanceRequestRead:
    return MaintenanceService(db).create(data, user)


@router.get("/open", response_model=list[MaintenanceRequestRead])
def list_open_requests(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return MaintenanceService(db).list_open(user)


@router.get("/{request_id}", response_model=MaintenanceRequestRead)
def get_request(request_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return MaintenanceService(db).get(request_id, user)


@router.get("/by-unit/{unit_id}", response_model=list[MaintenanceRequestRead])
def list_requests_for_unit(unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return MaintenanceService(db).list_for_unit(unit_id, user)


@router.patch("/{request_id}", response_model=MaintenanceRequestRead)
def update_request(
    request_id: int,
    data: MaintenanceRequestUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(_staff),
):
    return MaintenanceService(db).update(request_id, data, user)
