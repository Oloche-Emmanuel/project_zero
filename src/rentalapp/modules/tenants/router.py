from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rentalapp.core.deps import require_roles
from rentalapp.database import get_db
from rentalapp.modules.tenants.schemas import TenantCreate, TenantRead, TenantUpdate
from rentalapp.modules.tenants.service import TenantService
from rentalapp.modules.users.models import User, UserRole

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])

_staff = require_roles(UserRole.ADMIN, UserRole.LANDLORD)


@router.post("", response_model=TenantRead, status_code=201)
def create_tenant(data: TenantCreate, db: Session = Depends(get_db), _: User = Depends(_staff)) -> TenantRead:
    return TenantService(db).create(data)


@router.get("", response_model=list[TenantRead])
def list_tenants(db: Session = Depends(get_db), _: User = Depends(_staff)) -> list[TenantRead]:
    return TenantService(db).list()


@router.get("/{tenant_id}", response_model=TenantRead)
def get_tenant(tenant_id: int, db: Session = Depends(get_db), _: User = Depends(_staff)):
    return TenantService(db).get(tenant_id)


@router.patch("/{tenant_id}", response_model=TenantRead)
def update_tenant(tenant_id: int, data: TenantUpdate, db: Session = Depends(get_db), _: User = Depends(_staff)):
    return TenantService(db).update(tenant_id, data)


@router.delete("/{tenant_id}", status_code=204)
def delete_tenant(tenant_id: int, db: Session = Depends(get_db), _: User = Depends(_staff)) -> None:
    TenantService(db).delete(tenant_id)
