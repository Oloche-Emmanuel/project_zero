from datetime import datetime, timezone

from sqlalchemy.orm import Session

from rentalapp.core.access import AccessPolicy
from rentalapp.core.exceptions import ForbiddenError, NotFoundError
from rentalapp.modules.maintenance.models import MaintenanceRequest, MaintenanceStatus
from rentalapp.modules.maintenance.repository import MaintenanceRepository
from rentalapp.modules.maintenance.schemas import MaintenanceRequestCreate, MaintenanceRequestUpdate
from rentalapp.modules.tenants.models import Tenant
from rentalapp.modules.users.models import User, UserRole


class MaintenanceService:
    def __init__(self, db: Session) -> None:
        self.repo = MaintenanceRepository(db)

    def _can_view(self, access: AccessPolicy, request: MaintenanceRequest) -> bool:
        own = access.own_tenant_id
        if own is not None and request.tenant_id == own:
            return True
        return access.can_manage_unit(access.require_unit(request.unit_id))

    def create(self, data: MaintenanceRequestCreate, user: User) -> MaintenanceRequest:
        access = AccessPolicy(self.repo.db, user)
        values = data.model_dump()

        if user.role == UserRole.TENANT:
            # Tenants may only report issues on a unit they currently lease,
            # and the request is always filed under their own tenant record.
            access.require_unit(data.unit_id)
            if not access.has_active_lease_on_unit(data.unit_id):
                raise ForbiddenError("You can only report issues for a unit you currently lease")
            values["tenant_id"] = access.own_tenant_id
        else:
            access.require_manageable_unit(data.unit_id)
            if data.tenant_id is not None and not self.repo.db.get(Tenant, data.tenant_id):
                raise NotFoundError(f"Tenant {data.tenant_id} not found")

        return self.repo.add(MaintenanceRequest(**values))

    def get(self, request_id: int, user: User) -> MaintenanceRequest:
        request = self.repo.get(request_id)
        if not request:
            raise NotFoundError(f"Maintenance request {request_id} not found")
        if not self._can_view(AccessPolicy(self.repo.db, user), request):
            raise ForbiddenError("You do not have access to this maintenance request")
        return request

    def list_for_unit(self, unit_id: int, user: User) -> list[MaintenanceRequest]:
        access = AccessPolicy(self.repo.db, user)
        access.require_unit(unit_id)
        return [r for r in self.repo.list_by_unit(unit_id) if self._can_view(access, r)]

    def list_open(self, user: User) -> list[MaintenanceRequest]:
        access = AccessPolicy(self.repo.db, user)
        if access.is_admin:
            return self.repo.list_open()
        return [r for r in self.repo.list_open() if self._can_view(access, r)]

    def update(self, request_id: int, data: MaintenanceRequestUpdate, user: User) -> MaintenanceRequest:
        request = self.repo.get(request_id)
        if not request:
            raise NotFoundError(f"Maintenance request {request_id} not found")
        AccessPolicy(self.repo.db, user).require_manageable_unit(request.unit_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(request, field, value)

        if request.status in (MaintenanceStatus.COMPLETED, MaintenanceStatus.CANCELLED) and not request.resolved_at:
            request.resolved_at = datetime.now(timezone.utc)

        self.repo.db.commit()
        self.repo.db.refresh(request)
        return request
