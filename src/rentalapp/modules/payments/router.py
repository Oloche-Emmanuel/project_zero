from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rentalapp.core.deps import get_current_user, require_roles
from rentalapp.database import get_db
from rentalapp.modules.payments.schemas import InvoiceCreate, InvoiceRead, PaymentRecord
from rentalapp.modules.payments.service import InvoiceService
from rentalapp.modules.users.models import User, UserRole

router = APIRouter(prefix="/api/v1/invoices", tags=["payments"])

_staff = require_roles(UserRole.ADMIN, UserRole.LANDLORD)


@router.post("", response_model=InvoiceRead, status_code=201)
def create_invoice(data: InvoiceCreate, db: Session = Depends(get_db), _: User = Depends(_staff)) -> InvoiceRead:
    return InvoiceService(db).create(data)


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(invoice_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return InvoiceService(db).get(invoice_id)


@router.get("/by-lease/{lease_id}", response_model=list[InvoiceRead])
def list_invoices_for_lease(lease_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return InvoiceService(db).list_for_lease(lease_id)


@router.post("/{invoice_id}/payments", response_model=InvoiceRead)
def record_payment(
    invoice_id: int,
    data: PaymentRecord,
    db: Session = Depends(get_db),
    _: User = Depends(_staff),
):
    return InvoiceService(db).record_payment(invoice_id, data)


@router.post("/refresh-overdue", response_model=list[InvoiceRead])
def refresh_overdue(db: Session = Depends(get_db), _: User = Depends(_staff)):
    return InvoiceService(db).refresh_overdue_statuses()
