from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rentalapp.core.deps import get_current_user, require_roles
from rentalapp.database import get_db
from rentalapp.modules.leases.schemas import LeaseCreate, LeaseRead, LeaseUpdate
from rentalapp.modules.leases.service import LeaseService
from rentalapp.modules.users.models import User, UserRole

router = APIRouter(prefix="/api/v1/leases", tags=["leases"])

_staff = require_roles(UserRole.ADMIN, UserRole.LANDLORD)


@router.post("", response_model=LeaseRead, status_code=201)
def create_lease(data: LeaseCreate, db: Session = Depends(get_db), user: User = Depends(_staff)) -> LeaseRead:
    return LeaseService(db).create(data, user)


@router.get("/{lease_id}", response_model=LeaseRead)
def get_lease(lease_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return LeaseService(db).get(lease_id, user)


@router.get("/by-unit/{unit_id}", response_model=list[LeaseRead])
def list_leases_for_unit(unit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return LeaseService(db).list_for_unit(unit_id, user)


@router.get("/by-tenant/{tenant_id}", response_model=list[LeaseRead])
def list_leases_for_tenant(tenant_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return LeaseService(db).list_for_tenant(tenant_id, user)


@router.patch("/{lease_id}", response_model=LeaseRead)
def update_lease(lease_id: int, data: LeaseUpdate, db: Session = Depends(get_db), user: User = Depends(_staff)):
    return LeaseService(db).update(lease_id, data, user)


@router.post("/{lease_id}/terminate", response_model=LeaseRead)
def terminate_lease(lease_id: int, db: Session = Depends(get_db), user: User = Depends(_staff)):
    return LeaseService(db).terminate(lease_id, user)
