from datetime import datetime

from pydantic import BaseModel, ConfigDict

from rentalapp.modules.maintenance.models import MaintenancePriority, MaintenanceStatus


class MaintenanceRequestCreate(BaseModel):
    unit_id: int
    tenant_id: int | None = None
    title: str
    description: str
    priority: MaintenancePriority = MaintenancePriority.MEDIUM


class MaintenanceRequestUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: MaintenancePriority | None = None
    status: MaintenanceStatus | None = None


class MaintenanceRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    unit_id: int
    tenant_id: int | None
    title: str
    description: str
    priority: MaintenancePriority
    status: MaintenanceStatus
    created_at: datetime
    resolved_at: datetime | None
