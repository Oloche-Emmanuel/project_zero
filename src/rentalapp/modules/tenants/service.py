from sqlalchemy.orm import Session

from rentalapp.core.access import AccessPolicy
from rentalapp.modules.tenants.models import Tenant
from rentalapp.modules.tenants.repository import TenantRepository
from rentalapp.modules.tenants.schemas import TenantCreate, TenantUpdate
from rentalapp.modules.users.models import User


class TenantService:
    def __init__(self, db: Session) -> None:
        self.repo = TenantRepository(db)

    def create(self, data: TenantCreate, user: User) -> Tenant:
        tenant = Tenant(**data.model_dump(), owner_id=user.id)
        return self.repo.add(tenant)

    def get(self, tenant_id: int, user: User) -> Tenant:
        return AccessPolicy(self.repo.db, user).require_manageable_tenant(tenant_id)

    def list(self, user: User, offset: int = 0, limit: int = 100) -> list[Tenant]:
        if AccessPolicy(self.repo.db, user).is_admin:
            return self.repo.list(offset=offset, limit=limit)
        return self.repo.list_by_owner(user.id, offset=offset, limit=limit)

    def update(self, tenant_id: int, data: TenantUpdate, user: User) -> Tenant:
        tenant = self.get(tenant_id, user)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(tenant, field, value)
        self.repo.db.commit()
        self.repo.db.refresh(tenant)
        return tenant

    def delete(self, tenant_id: int, user: User) -> None:
        tenant = self.get(tenant_id, user)
        self.repo.delete(tenant)
