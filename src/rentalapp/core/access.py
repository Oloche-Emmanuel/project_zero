from sqlalchemy import select
from sqlalchemy.orm import Session

from rentalapp.core.exceptions import ForbiddenError, NotFoundError
from rentalapp.modules.leases.models import Lease, LeaseStatus
from rentalapp.modules.properties.models import Property, Unit
from rentalapp.modules.tenants.models import Tenant
from rentalapp.modules.users.models import User, UserRole


class AccessPolicy:
    """Answers "may this user see / change this record?" for every module.

    Ownership flows from properties: a landlord manages the units of the
    properties they own, and everything attached to those units (leases,
    invoices, maintenance requests). Tenant records are owned by the
    landlord who created them. A tenant-role user can *view* the leases,
    invoices and maintenance requests of the tenant record linked to their
    account. Admins can do everything.

    Services call the `require_*` methods, which raise NotFoundError /
    ForbiddenError, so routers never hand-roll authorization.
    """

    def __init__(self, db: Session, user: User) -> None:
        self.db = db
        self.user = user
        self._tenant_id: int | None = None
        self._tenant_id_loaded = False

    @property
    def is_admin(self) -> bool:
        return self.user.role == UserRole.ADMIN

    @property
    def own_tenant_id(self) -> int | None:
        """The tenant record linked to this user's login, if any."""
        if not self._tenant_id_loaded:
            stmt = select(Tenant.id).where(Tenant.user_id == self.user.id)
            self._tenant_id = self.db.scalars(stmt).first()
            self._tenant_id_loaded = True
        return self._tenant_id

    # -- units -------------------------------------------------------------

    def can_manage_unit(self, unit: Unit) -> bool:
        if self.is_admin:
            return True
        prop = self.db.get(Property, unit.property_id)
        return prop is not None and prop.owner_id == self.user.id

    def require_unit(self, unit_id: int) -> Unit:
        unit = self.db.get(Unit, unit_id)
        if not unit:
            raise NotFoundError(f"Unit {unit_id} not found")
        return unit

    def require_manageable_unit(self, unit_id: int) -> Unit:
        unit = self.require_unit(unit_id)
        if not self.can_manage_unit(unit):
            raise ForbiddenError("You do not have access to this unit")
        return unit

    # -- tenants -----------------------------------------------------------

    def can_manage_tenant(self, tenant: Tenant) -> bool:
        return self.is_admin or tenant.owner_id == self.user.id

    def require_manageable_tenant(self, tenant_id: int) -> Tenant:
        tenant = self.db.get(Tenant, tenant_id)
        if not tenant:
            raise NotFoundError(f"Tenant {tenant_id} not found")
        if not self.can_manage_tenant(tenant):
            raise ForbiddenError("You do not have access to this tenant")
        return tenant

    # -- leases ------------------------------------------------------------

    def can_manage_lease(self, lease: Lease) -> bool:
        unit = self.db.get(Unit, lease.unit_id)
        return unit is not None and self.can_manage_unit(unit)

    def can_view_lease(self, lease: Lease) -> bool:
        own = self.own_tenant_id
        return (own is not None and lease.tenant_id == own) or self.can_manage_lease(lease)

    def require_lease(self, lease_id: int) -> Lease:
        lease = self.db.get(Lease, lease_id)
        if not lease:
            raise NotFoundError(f"Lease {lease_id} not found")
        return lease

    def require_viewable_lease(self, lease_id: int) -> Lease:
        lease = self.require_lease(lease_id)
        if not self.can_view_lease(lease):
            raise ForbiddenError("You do not have access to this lease")
        return lease

    def require_manageable_lease(self, lease_id: int) -> Lease:
        lease = self.require_lease(lease_id)
        if not self.can_manage_lease(lease):
            raise ForbiddenError("You do not have access to this lease")
        return lease

    def has_active_lease_on_unit(self, unit_id: int) -> bool:
        """Whether this user's own tenant record actively leases the unit."""
        own = self.own_tenant_id
        if own is None:
            return False
        stmt = select(Lease.id).where(
            Lease.unit_id == unit_id, Lease.tenant_id == own, Lease.status == LeaseStatus.ACTIVE
        )
        return self.db.scalars(stmt).first() is not None
