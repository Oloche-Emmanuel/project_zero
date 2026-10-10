from sqlalchemy import select

from rentalapp.core.repository import BaseRepository
from rentalapp.modules.tenants.models import Tenant


class TenantRepository(BaseRepository[Tenant]):
    model = Tenant

    def get_by_user_id(self, user_id: int) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.user_id == user_id)
        return self.db.scalars(stmt).first()

    def list_by_owner(self, owner_id: int, offset: int = 0, limit: int = 100) -> list[Tenant]:
        stmt = select(Tenant).where(Tenant.owner_id == owner_id).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())
