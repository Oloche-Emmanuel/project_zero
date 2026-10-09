from sqlalchemy import select

from rentalapp.core.repository import BaseRepository
from rentalapp.modules.tenants.models import Tenant


class TenantRepository(BaseRepository[Tenant]):
    model = Tenant

    def get_by_user_id(self, user_id: int) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.user_id == user_id)
        return self.db.scalars(stmt).first()
