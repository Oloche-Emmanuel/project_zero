from sqlalchemy import select

from rentalapp.core.repository import BaseRepository
from rentalapp.modules.payments.models import Invoice, InvoiceStatus


class InvoiceRepository(BaseRepository[Invoice]):
    model = Invoice

    def list_by_lease(self, lease_id: int) -> list[Invoice]:
        stmt = select(Invoice).where(Invoice.lease_id == lease_id)
        return list(self.db.scalars(stmt).all())

    def list_overdue_candidates(self) -> list[Invoice]:
        stmt = select(Invoice).where(Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.PARTIAL]))
        return list(self.db.scalars(stmt).all())
