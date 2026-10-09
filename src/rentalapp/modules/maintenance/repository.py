from sqlalchemy import select

from rentalapp.core.repository import BaseRepository
from rentalapp.modules.maintenance.models import MaintenanceRequest


class MaintenanceRepository(BaseRepository[MaintenanceRequest]):
    model = MaintenanceRequest

    def list_by_unit(self, unit_id: int) -> list[MaintenanceRequest]:
        stmt = select(MaintenanceRequest).where(MaintenanceRequest.unit_id == unit_id)
        return list(self.db.scalars(stmt).all())

    def list_open(self) -> list[MaintenanceRequest]:
        stmt = select(MaintenanceRequest).where(
            MaintenanceRequest.status.in_(["open", "in_progress"])
        )
        return list(self.db.scalars(stmt).all())
