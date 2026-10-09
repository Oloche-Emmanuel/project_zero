from sqlalchemy.orm import Session

from rentalapp.core.exceptions import NotFoundError
from rentalapp.modules.tenants.models import Tenant
from rentalapp.modules.tenants.repository import TenantRepository
from rentalapp.modules.tenants.schemas import TenantCreate, TenantUpdate


class TenantService:
    def __init__(self, db: Session) -> None:
        self.repo = TenantRepository(db)

    def create(self, data: TenantCreate) -> Tenant:
        tenant = Tenant(**data.model_dump())
        return self.repo.add(tenant)

    def get(self, tenant_id: int) -> Tenant:
        tenant = self.repo.get(tenant_id)
        if not tenant:
            raise NotFoundError(f"Tenant {tenant_id} not found")
        return tenant

    def list(self, offset: int = 0, limit: int = 100) -> list[Tenant]:
        return self.repo.list(offset=offset, limit=limit)

    def update(self, tenant_id: int, data: TenantUpdate) -> Tenant:
        tenant = self.get(tenant_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(tenant, field, value)
        self.repo.db.commit()
        self.repo.db.refresh(tenant)
        return tenant

    def delete(self, tenant_id: int) -> None:
        tenant = self.get(tenant_id)
        self.repo.delete(tenant)
