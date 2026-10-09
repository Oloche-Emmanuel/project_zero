from sqlalchemy.orm import Session

from rentalapp.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from rentalapp.modules.leases.models import Lease, LeaseStatus
from rentalapp.modules.leases.repository import LeaseRepository
from rentalapp.modules.leases.schemas import LeaseCreate, LeaseUpdate
from rentalapp.modules.properties.models import UnitStatus
from rentalapp.modules.properties.repository import PropertyRepository, UnitRepository
from rentalapp.modules.users.models import User, UserRole


class LeaseService:
    def __init__(self, db: Session) -> None:
        self.repo = LeaseRepository(db)
        self.unit_repo = UnitRepository(db)
        self.property_repo = PropertyRepository(db)

    def _assert_can_manage_unit(self, unit_id: int, user: User) -> None:
        unit = self.unit_repo.get(unit_id)
        if not unit:
            raise NotFoundError(f"Unit {unit_id} not found")
        prop = self.property_repo.get(unit.property_id)
        if user.role != UserRole.ADMIN and (not prop or prop.owner_id != user.id):
            raise ForbiddenError("You do not have access to this unit")

    def create(self, data: LeaseCreate, user: User) -> Lease:
        self._assert_can_manage_unit(data.unit_id, user)

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

    def get(self, lease_id: int) -> Lease:
        lease = self.repo.get(lease_id)
        if not lease:
            raise NotFoundError(f"Lease {lease_id} not found")
        return lease

    def list_for_unit(self, unit_id: int) -> list[Lease]:
        return self.repo.list_by_unit(unit_id)

    def list_for_tenant(self, tenant_id: int) -> list[Lease]:
        return self.repo.list_by_tenant(tenant_id)

    def update(self, lease_id: int, data: LeaseUpdate, user: User) -> Lease:
        lease = self.get(lease_id)
        self._assert_can_manage_unit(lease.unit_id, user)

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
