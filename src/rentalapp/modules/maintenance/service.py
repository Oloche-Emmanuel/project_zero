from datetime import datetime, timezone

from sqlalchemy.orm import Session

from rentalapp.core.exceptions import NotFoundError
from rentalapp.modules.maintenance.models import MaintenanceRequest, MaintenanceStatus
from rentalapp.modules.maintenance.repository import MaintenanceRepository
from rentalapp.modules.maintenance.schemas import MaintenanceRequestCreate, MaintenanceRequestUpdate


class MaintenanceService:
    def __init__(self, db: Session) -> None:
        self.repo = MaintenanceRepository(db)

    def create(self, data: MaintenanceRequestCreate) -> MaintenanceRequest:
        request = MaintenanceRequest(**data.model_dump())
        return self.repo.add(request)

    def get(self, request_id: int) -> MaintenanceRequest:
        request = self.repo.get(request_id)
        if not request:
            raise NotFoundError(f"Maintenance request {request_id} not found")
        return request

    def list_for_unit(self, unit_id: int) -> list[MaintenanceRequest]:
        return self.repo.list_by_unit(unit_id)

    def list_open(self) -> list[MaintenanceRequest]:
        return self.repo.list_open()

    def update(self, request_id: int, data: MaintenanceRequestUpdate) -> MaintenanceRequest:
        request = self.get(request_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(request, field, value)

        if request.status in (MaintenanceStatus.COMPLETED, MaintenanceStatus.CANCELLED) and not request.resolved_at:
            request.resolved_at = datetime.now(timezone.utc)

        self.repo.db.commit()
        self.repo.db.refresh(request)
        return request
