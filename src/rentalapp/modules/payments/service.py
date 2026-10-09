from datetime import date

from sqlalchemy.orm import Session

from rentalapp.core.exceptions import ConflictError, NotFoundError
from rentalapp.modules.payments.models import Invoice, InvoiceStatus
from rentalapp.modules.payments.repository import InvoiceRepository
from rentalapp.modules.payments.schemas import InvoiceCreate, PaymentRecord


class InvoiceService:
    def __init__(self, db: Session) -> None:
        self.repo = InvoiceRepository(db)

    def create(self, data: InvoiceCreate) -> Invoice:
        invoice = Invoice(**data.model_dump())
        return self.repo.add(invoice)

    def get(self, invoice_id: int) -> Invoice:
        invoice = self.repo.get(invoice_id)
        if not invoice:
            raise NotFoundError(f"Invoice {invoice_id} not found")
        return invoice

    def list_for_lease(self, lease_id: int) -> list[Invoice]:
        return self.repo.list_by_lease(lease_id)

    def record_payment(self, invoice_id: int, data: PaymentRecord) -> Invoice:
        invoice = self.get(invoice_id)
        if invoice.status == InvoiceStatus.PAID:
            raise ConflictError(f"Invoice {invoice_id} is already fully paid")

        invoice.amount_paid = float(invoice.amount_paid) + data.amount
        invoice.payment_method = data.payment_method
        invoice.paid_date = data.paid_date or date.today()

        if invoice.amount_paid >= float(invoice.amount_due):
            invoice.status = InvoiceStatus.PAID
        else:
            invoice.status = InvoiceStatus.PARTIAL

        self.repo.db.commit()
        self.repo.db.refresh(invoice)
        return invoice

    def refresh_overdue_statuses(self) -> list[Invoice]:
        """Flag pending/partial invoices past their due date as overdue.

        Intended to be called on a schedule (cron/background job) once one
        is wired up; exposed via an endpoint for now so it can be triggered
        on demand.
        """
        today = date.today()
        newly_overdue = []
        for invoice in self.repo.list_overdue_candidates():
            if invoice.due_date < today:
                invoice.status = InvoiceStatus.OVERDUE
                newly_overdue.append(invoice)
        if newly_overdue:
            self.repo.db.commit()
        return newly_overdue
