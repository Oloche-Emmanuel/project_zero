from sqlalchemy.orm import Session

from rentalapp.core.access import AccessPolicy
from rentalapp.core.exceptions import ConflictError, ValidationError
from rentalapp.modules.leases.models import Lease, LeaseStatus
from rentalapp.modules.leases.repository import LeaseRepository
from rentalapp.modules.leases.schemas import LeaseCreate, LeaseUpdate
from rentalapp.modules.properties.models import UnitStatus
from rentalapp.modules.properties.repository import UnitRepository
from rentalapp.modules.users.models import User


class LeaseService:
    def __init__(self, db: Session) -> None:
        self.repo = LeaseRepository(db)
        self.unit_repo = UnitRepository(db)

    def create(self, data: LeaseCreate, user: User) -> Lease:
        access = AccessPolicy(self.repo.db, user)
        access.require_manageable_unit(data.unit_id)
        access.require_manageable_tenant(data.tenant_id)

        if data.end_date <= data.start_date:
            raise ValidationError("end_date must be after start_date")

        if self.repo.get_active_for_unit(data.unit_id):
            raise ConflictError(f"Unit {data.unit_id} already has an active lease")

        lease = Lease(**data.model_dump(), status=LeaseStatus.ACTIVE)
        lease = self.repo.add(lease)

        unit = self.unit_repo.get(data.unit_id)
        unit.status = UnitStatus.OCCUPIED
        self.unit_repo.db.commit()

        return lease

    def get(self, lease_id: int, user: User) -> Lease:
        return AccessPolicy(self.repo.db, user).require_viewable_lease(lease_id)

    def list_for_unit(self, unit_id: int, user: User) -> list[Lease]:
        access = AccessPolicy(self.repo.db, user)
        access.require_unit(unit_id)
        return [lease for lease in self.repo.list_by_unit(unit_id) if access.can_view_lease(lease)]

    def list_for_tenant(self, tenant_id: int, user: User) -> list[Lease]:
        access = AccessPolicy(self.repo.db, user)
        return [lease for lease in self.repo.list_by_tenant(tenant_id) if access.can_view_lease(lease)]

    def update(self, lease_id: int, data: LeaseUpdate, user: User) -> Lease:
        lease = AccessPolicy(self.repo.db, user).require_manageable_lease(lease_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(lease, field, value)
        self.repo.db.commit()
        self.repo.db.refresh(lease)

        if lease.status in (LeaseStatus.EXPIRED, LeaseStatus.TERMINATED):
            unit = self.unit_repo.get(lease.unit_id)
            if unit and unit.status == UnitStatus.OCCUPIED:
                unit.status = UnitStatus.VACANT
                self.unit_repo.db.commit()

        return lease

    def terminate(self, lease_id: int, user: User) -> Lease:
        return self.update(lease_id, LeaseUpdate(status=LeaseStatus.TERMINATED), user)
