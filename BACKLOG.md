# Rental Property Management — Backlog

Derived from the existing feature set in [src/rentalapp/modules](src/rentalapp/modules).
Organized into epics, broken into user stories, and grouped into sprints by
dependency order (each sprint builds on data/endpoints the previous one
introduced).

Priority: **P0** = blocking/core, **P1** = important, **P2** = nice-to-have.

---

## Epics

- **EPIC-1: Auth & Accounts**
- **EPIC-2: Properties & Units**
- **EPIC-3: Tenants**
- **EPIC-4: Leases**
- **EPIC-5: Rent Invoicing & Payments**
- **EPIC-6: Maintenance Requests**
- **EPIC-7: Access Control & Data Scoping** (cross-cutting)

---

## EPIC-1: Auth & Accounts

### US-101 — Register an account (P0)
As a new user, I want to register with an email/password and a role, so that
I can get an account appropriate to my relationship with the properties.
- Acceptance: `POST /auth/register` creates a user with `admin`/`landlord`/`tenant` role; password is hashed, never stored/returned in plaintext.

### US-102 — Log in and receive a JWT (P0)
As a registered user, I want to log in and receive a JWT, so that I can
authenticate subsequent API calls.
- Acceptance: `POST /auth/login` validates credentials and returns a bearer token; invalid credentials return 401.

### US-103 — View my own profile (P1)
As any logged-in user, I want to fetch my own profile, so that a client app
can display who I am and what role I have.
- Acceptance: `GET /users/me` returns the current user's record derived from the JWT, no ID required.

### US-104 — List all users (P1)
As an admin, I want to list all users, so that I can audit or support
accounts across the platform.
- Acceptance: `GET /users` is admin-only; non-admins get 403.

### US-105 — View and update any user (P1)
As an admin, I want to view and update any single user's record, so that I
can fix account issues without touching the database directly.
- Acceptance: `GET/PATCH /users/{id}` admin-only; update supports role/contact field changes.

---

## EPIC-2: Properties & Units

### US-201 — Create a property (P0)
As a landlord, I want to create a property record (address, type), so that I
have a place to attach units, leases, and invoices.
- Acceptance: `POST /properties` associates the property with the creating landlord.

### US-202 — List/view my properties only (P0)
As a landlord, I want to list and view only my own properties, so that I
never see another landlord's data.
- Acceptance: `GET /properties` and `GET /properties/{id}` scoped to owner; admins see all; other landlords get 403/empty.

### US-203 — Update a property (P1)
As a landlord, I want to update a property's details, so that I can correct
or refresh its information over time.
- Acceptance: `PATCH /properties/{id}` restricted to the owning landlord or admin.

### US-204 — Delete a property (P2)
As a landlord, I want to delete a property I no longer manage, so that stale
records don't clutter my portfolio.
- Acceptance: `DELETE /properties/{id}`; blocked or cascaded sensibly if active units/leases exist.

### US-205 — Add a unit to a property (P0)
As a landlord, I want to add individual units to a property (bedrooms, rent
amount), so that I can manage rentable space separately from the building.
- Acceptance: `POST /properties/{id}/units` creates a unit defaulted to vacant.

### US-206 — List units under a property (P0)
As a landlord, I want to list all units under a property, so that I can see
occupancy and rent at a glance.
- Acceptance: `GET /properties/{id}/units` returns rent + vacancy status per unit.

### US-207 — View/update a single unit (P1)
As a landlord, I want to view or update a single unit, so that I can adjust
rent or details for that specific space.
- Acceptance: `GET/PATCH /units/{id}` restricted to the owning landlord or admin.

### US-208 — Vacancy status stays accurate automatically (P0)
As a landlord, I want a unit's vacancy status to always reflect reality, so
that I never have to manually track whether a unit is occupied.
- Acceptance: unit flips vacant/occupied automatically on lease creation/termination (see EPIC-4).

---

## EPIC-3: Tenants

### US-301 — Create a tenant profile (P0)
As staff, I want to create a tenant profile with contact and
emergency-contact info, so that I have the information needed before or
independent of signing a lease.
- Acceptance: `POST /tenants` staff-only (admin/landlord).

### US-302 — Link a tenant to a login account (P1)
As staff, I want to optionally link a tenant profile to a login account, so
that the same person can log in and see their own lease/invoices.
- Acceptance: tenant record can reference a `user_id` with role `tenant`; unlinked tenants remain valid.

### US-303 — List and search tenants (P1)
As staff, I want to list and search tenants, so that I can find the right
person when creating a lease.
- Acceptance: `GET /tenants` staff-only.

### US-304 — View/update a tenant (P1)
As staff, I want to view and update a tenant's details, so that I can keep
contact information current.
- Acceptance: `GET/PATCH /tenants/{id}` staff-only.

### US-305 — Delete a tenant (P2)
As staff, I want to delete a tenant record, so that I can remove someone
entered in error or who never signed a lease.
- Acceptance: `DELETE /tenants/{id}`; blocked if active leases reference the tenant.

---

## EPIC-4: Leases

### US-401 — Create a lease (P0)
As staff, I want to bind a tenant to a unit for a date range and rent
amount, so that the lease terms are recorded formally.
- Acceptance: `POST /leases`; unit flips to occupied on success.

### US-402 — Prevent double-booking a unit (P0)
As staff, I want the system to reject a second active lease on an
already-leased unit, so that I can't accidentally double-book a space.
- Acceptance: creating a lease on an occupied unit returns a conflict error.

### US-403 — View a lease (P1)
As an authorized user, I want to view a single lease's details, so that I
can confirm its terms.
- Acceptance: `GET /leases/{id}` viewable by involved tenant, owning landlord, or admin.

### US-404 — List leases by unit (P1)
As staff, I want to list all leases for a given unit, so that I can see its
rental history.
- Acceptance: `GET /leases/by-unit/{unit_id}`.

### US-405 — List leases by tenant (P1)
As staff, I want to list all leases for a given tenant, so that I can see
everywhere that tenant has lived.
- Acceptance: `GET /leases/by-tenant/{tenant_id}`.

### US-406 — Update lease terms (P1)
As staff, I want to update a lease's terms (e.g., rent, end date), so that I
can reflect renewals or amendments.
- Acceptance: `PATCH /leases/{id}` staff-only.

### US-407 — Terminate a lease early (P0)
As staff, I want to terminate a lease early, so that I can free up the unit
and stop future invoicing when a tenant moves out ahead of schedule.
- Acceptance: `POST /leases/{id}/terminate` sets lease inactive and unit back to vacant.

---

## EPIC-5: Rent Invoicing & Payments

### US-501 — Generate a rent invoice (P0)
As staff, I want to generate a rent invoice for a lease, so that there's a
billable record of what's owed for a period.
- Acceptance: `POST /invoices` tied to an active lease with amount + due date.

### US-502 — View an invoice (P1)
As an authorized user, I want to view a single invoice, so that I can check
what's owed and its status.
- Acceptance: `GET /invoices/{id}` viewable by tenant on the lease, owning landlord, or admin.

### US-503 — List invoices for a lease (P1)
As an authorized user, I want to list all invoices for a lease, so that I
(or the tenant) can see full billing history.
- Acceptance: `GET /invoices/by-lease/{lease_id}`.

### US-504 — Record a payment (P0)
As staff, I want to record a full or partial payment against an invoice, so
that the balance owed updates accurately.
- Acceptance: `POST /invoices/{id}/payments`; invoice status moves to partially-paid/paid based on amount.

### US-505 — See accurate payment status (P0)
As a tenant, I want my invoice to show accurately whether I've paid in
full, partially, or not at all, so that I know what I still owe.
- Acceptance: invoice response includes computed status + remaining balance.

### US-506 — Refresh overdue statuses (P1)
As staff, I want to trigger a refresh of overdue statuses across invoices,
so that past-due rent is automatically flagged without manually checking
every invoice's due date.
- Acceptance: `POST /invoices/refresh-overdue` staff-only; flips unpaid invoices past due date to overdue.

---

## EPIC-6: Maintenance Requests

### US-601 — Tenant logs an issue (P0)
As a tenant, I want to log a maintenance issue against my unit, so that
staff are notified of a problem needing attention.
- Acceptance: `POST /maintenance-requests`; tenant restricted to their own unit.

### US-602 — Staff logs an issue (P1)
As staff, I want to log a maintenance issue on behalf of a tenant or from an
inspection, so that issues get tracked even when not tenant-reported.
- Acceptance: same endpoint, staff can create for any unit they manage.

### US-603 — List open requests (P0)
As staff, I want to list all open requests, so that I can prioritize what
needs to be addressed.
- Acceptance: `GET /maintenance-requests/open`.

### US-604 — View a request (P1)
As an authorized user, I want to view a single request's details and
history, so that I can follow its progress.
- Acceptance: `GET /maintenance-requests/{id}`.

### US-605 — List requests by unit (P1)
As staff, I want to list all maintenance requests for a specific unit, so
that I can see recurring issues in that space.
- Acceptance: `GET /maintenance-requests/by-unit/{unit_id}`.

### US-606 — Update request status (P0)
As staff, I want to move a request through open → in_progress →
completed/cancelled, so that the workflow reflects real-world repair
status.
- Acceptance: `PATCH /maintenance-requests/{id}` staff-only; only valid transitions allowed.

### US-607 — Tenant tracks their request (P1)
As a tenant, I want to see the current status of my maintenance request, so
that I know whether it's been picked up.
- Acceptance: tenant can `GET` their own request by ID.

---

## EPIC-7: Access Control & Data Scoping (cross-cutting)

### US-701 — Role-scoped data on every endpoint (P0)
As any user, I want every request to be scoped to my role (landlord sees
only their properties; tenant sees only their own leases/invoices/requests;
admin sees everything), so that data stays private between unrelated
parties.
- Acceptance: cross-role access attempts return 403/404, verified per module.

---

## Sprint Plan

### Sprint 1 — Foundation: Auth & Property Setup
Everything downstream depends on accounts existing and properties/units
being manageable.
- US-101, US-102, US-103 (Auth)
- US-201, US-202, US-203, US-205, US-206, US-207 (Properties & Units core)
- US-701 (scoping, established early as a pattern for every module after)

### Sprint 2 — Admin Tools & Tenant Records
- US-104, US-105 (Admin user management)
- US-204 (Delete property)
- US-301, US-302, US-303, US-304, US-305 (Tenants)

### Sprint 3 — Leasing
- US-401, US-402, US-403, US-404, US-405, US-406, US-407 (full Leases epic)
- US-208 (vacancy auto-sync, verified against lease create/terminate)

### Sprint 4 — Rent Invoicing & Payments
- US-501, US-502, US-503, US-504, US-505, US-506 (full Payments epic)

### Sprint 5 — Maintenance Requests
- US-601 through US-607 (full Maintenance epic)

### Sprint 6 — Hardening & Polish
- Cross-epic bug fixes, edge cases surfaced in Sprints 1–5
- Deepen US-701 coverage (authz regression tests across all modules)
- P2 items not yet done (US-204 if deferred, etc.)

---

## Notes

- Sprint sizing assumes ~2-week sprints with a small team; rebalance freely
  based on actual velocity.
- Because the backend modules for all six epics already exist in
  [src/rentalapp/modules](src/rentalapp/modules), this backlog doubles as a
  **verification/test-coverage checklist** as much as a build plan — treat
  stories as "confirm implemented + tested" where code already exists, and
  "implement" only where it's genuinely missing (e.g., frontend views).
