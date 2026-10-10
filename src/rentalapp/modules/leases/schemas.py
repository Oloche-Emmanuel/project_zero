from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from rentalapp.modules.leases.models import LeaseStatus


class LeaseCreate(BaseModel):
    unit_id: int
    tenant_id: int
    start_date: date
    end_date: date
    rent_amount: float = Field(gt=0)
    security_deposit: float = Field(default=0, ge=0)


class LeaseUpdate(BaseModel):
    end_date: date | None = None
    rent_amount: float | None = Field(default=None, gt=0)
    security_deposit: float | None = Field(default=None, ge=0)
    status: LeaseStatus | None = None


class LeaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    unit_id: int
    tenant_id: int
    start_date: date
    end_date: date
    rent_amount: float
    security_deposit: float
    status: LeaseStatus
    created_at: datetime
