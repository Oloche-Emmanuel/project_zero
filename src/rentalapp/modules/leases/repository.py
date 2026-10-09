from sqlalchemy import select

from rentalapp.core.repository import BaseRepository
from rentalapp.modules.leases.models import Lease, LeaseStatus


class LeaseRepository(BaseRepository[Lease]):
    model = Lease

    def get_active_for_unit(self, unit_id: int) -> Lease | None:
        stmt = select(Lease).where(Lease.unit_id == unit_id, Lease.status == LeaseStatus.ACTIVE)
        return self.db.scalars(stmt).first()

    def list_by_tenant(self, tenant_id: int) -> list[Lease]:
        stmt = select(Lease).where(Lease.tenant_id == tenant_id)
        return list(self.db.scalars(stmt).all())

    def list_by_unit(self, unit_id: int) -> list[Lease]:
        stmt = select(Lease).where(Lease.unit_id == unit_id)
        return list(self.db.scalars(stmt).all())
