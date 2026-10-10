from datetime import date

from sqlalchemy.orm import Session

from rentalapp.core.access import AccessPolicy
from rentalapp.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from rentalapp.modules.leases.models import Lease
from rentalapp.modules.payments.models import Invoice, InvoiceStatus
from rentalapp.modules.payments.repository import InvoiceRepository
from rentalapp.modules.payments.schemas import InvoiceCreate, PaymentRecord
from rentalapp.modules.users.models import User


class InvoiceService:
    def __init__(self, db: Session) -> None:
        self.repo = InvoiceRepository(db)

    def create(self, data: InvoiceCreate, user: User) -> Invoice:
        AccessPolicy(self.repo.db, user).require_manageable_lease(data.lease_id)
        invoice = Invoice(**data.model_dump())
        return self.repo.add(invoice)

    def _get(self, invoice_id: int) -> Invoice:
        invoice = self.repo.get(invoice_id)
        if not invoice:
            raise NotFoundError(f"Invoice {invoice_id} not found")
        return invoice

    def get(self, invoice_id: int, user: User) -> Invoice:
        invoice = self._get(invoice_id)
        access = AccessPolicy(self.repo.db, user)
        if not access.can_view_lease(access.require_lease(invoice.lease_id)):
            raise ForbiddenError("You do not have access to this invoice")
        return invoice

    def list_for_lease(self, lease_id: int, user: User) -> list[Invoice]:
        AccessPolicy(self.repo.db, user).require_viewable_lease(lease_id)
        return self.repo.list_by_lease(lease_id)

    def record_payment(self, invoice_id: int, data: PaymentRecord, user: User) -> Invoice:
        invoice = self._get(invoice_id)
        access = AccessPolicy(self.repo.db, user)
        if not access.can_manage_lease(access.require_lease(invoice.lease_id)):
            raise ForbiddenError("You do not have access to this invoice")
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

    def refresh_overdue_statuses(self, user: User | None = None, today: date | None = None) -> list[Invoice]:
        """Flag pending/partial invoices past their due date as overdue.

        Intended to be called on a schedule (cron/background job) once one
        is wired up, with no user (all invoices). Exposed via an endpoint
        for now so staff can trigger it on demand; a landlord only refreshes
        (and sees) invoices on their own leases.
        """
        today = today or date.today()
        access = AccessPolicy(self.repo.db, user) if user else None
        newly_overdue = []
        for invoice in self.repo.list_overdue_candidates():
            if access and not access.can_manage_lease(self.repo.db.get(Lease, invoice.lease_id)):
                continue
            if invoice.due_date < today:
                invoice.status = InvoiceStatus.OVERDUE
                newly_overdue.append(invoice)
        if newly_overdue:
            self.repo.db.commit()
        return newly_overdue
