from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from rentalapp.modules.payments.models import InvoiceStatus


class InvoiceCreate(BaseModel):
    lease_id: int
    amount_due: float
    due_date: date
    notes: str | None = None


class PaymentRecord(BaseModel):
    amount: float = Field(gt=0)
    payment_method: str
    paid_date: date | None = None


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lease_id: int
    amount_due: float
    amount_paid: float
    due_date: date
    paid_date: date | None
    status: InvoiceStatus
    payment_method: str | None
    notes: str | None
    created_at: datetime
