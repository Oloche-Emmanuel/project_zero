"""Authorization and validation regression tests.

Each defect found in exploratory testing (EX-01 .. EX-09 in
docs/DESIGN_AND_TESTING.md) has a test here proving it is now blocked, next
to a test proving the legitimate user can still do the same thing.
"""

from datetime import date, timedelta

import pytest

from tests.conftest import register_and_login

PROPERTY = {
    "name": "Maple Apartments",
    "address_line1": "123 Maple St",
    "city": "Springfield",
    "state": "IL",
    "zip_code": "62704",
    "property_type": "apartment",
}


@pytest.fixture()
def world(client):
    """Two landlords and two tenant logins; landlord A owns a leased unit.

    The tenant login `tenant` is linked to the tenant record on A's lease;
    `stranger` is a tenant login with no lease anywhere.
    """
    a = register_and_login(client, email="landlord_a@example.com", role="landlord")
    b = register_and_login(client, email="landlord_b@example.com", role="landlord")
    tenant = register_and_login(client, email="tenant@example.com", role="tenant")
    stranger = register_and_login(client, email="stranger@example.com", role="tenant")
    tenant_user_id = client.get("/api/v1/users/me", headers=tenant).json()["id"]

    property_id = client.post("/api/v1/properties", json=PROPERTY, headers=a).json()["id"]
    unit_id = client.post(
        f"/api/v1/properties/{property_id}/units", json={"unit_number": "1A", "rent_amount": 1200}, headers=a
    ).json()["id"]
    tenant_id = client.post(
        "/api/v1/tenants",
        json={"first_name": "Jane", "last_name": "Doe", "email": "jane@example.com", "user_id": tenant_user_id},
        headers=a,
    ).json()["id"]
    lease_id = client.post(
        "/api/v1/leases",
        json={"unit_id": unit_id, "tenant_id": tenant_id, "start_date": "2026-01-01", "end_date": "2026-12-31", "rent_amount": 1200},
        headers=a,
    ).json()["id"]
    invoice_id = client.post(
        "/api/v1/invoices", json={"lease_id": lease_id, "amount_due": 1200, "due_date": "2026-02-01"}, headers=a
    ).json()["id"]

    return {
        "a": a, "b": b, "tenant": tenant, "stranger": stranger,
        "property_id": property_id, "unit_id": unit_id, "tenant_id": tenant_id,
        "lease_id": lease_id, "invoice_id": invoice_id,
    }


# -- EX-01: admin self-registration ------------------------------------------

def test_public_signup_cannot_create_admin(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "evil@example.com", "password": "supersecret", "full_name": "Evil", "role": "admin"},
    )
    assert resp.status_code == 403


def test_landlord_cannot_create_admin(client):
    headers = register_and_login(client, email="landlord@example.com", role="landlord")
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "evil@example.com", "password": "supersecret", "full_name": "Evil", "role": "admin"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_admin_can_create_admin(client, admin_headers):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "second@example.com", "password": "supersecret", "full_name": "Second", "role": "admin"},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "admin"


def test_signup_with_invalid_token_is_rejected(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "x@example.com", "password": "supersecret", "full_name": "X", "role": "tenant"},
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert resp.status_code == 401


# -- EX-02 / EX-03: invoices ---------------------------------------------------

def test_other_landlord_cannot_read_invoice(client, world):
    assert client.get(f"/api/v1/invoices/{world['invoice_id']}", headers=world["b"]).status_code == 403
    assert client.get(f"/api/v1/invoices/by-lease/{world['lease_id']}", headers=world["b"]).status_code == 403


def test_other_landlord_cannot_record_payment(client, world):
    resp = client.post(
        f"/api/v1/invoices/{world['invoice_id']}/payments",
        json={"amount": 1, "payment_method": "cash"},
        headers=world["b"],
    )
    assert resp.status_code == 403


def test_other_landlord_cannot_invoice_lease(client, world):
    resp = client.post(
        "/api/v1/invoices", json={"lease_id": world["lease_id"], "amount_due": 10, "due_date": "2026-03-01"}, headers=world["b"]
    )
    assert resp.status_code == 403


def test_leasing_tenant_can_read_own_invoices(client, world):
    assert client.get(f"/api/v1/invoices/{world['invoice_id']}", headers=world["tenant"]).status_code == 200
    resp = client.get(f"/api/v1/invoices/by-lease/{world['lease_id']}", headers=world["tenant"])
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_unrelated_tenant_cannot_read_invoice(client, world):
    assert client.get(f"/api/v1/invoices/{world['invoice_id']}", headers=world["stranger"]).status_code == 403


# -- EX-04: leases --------------------------------------------------------------

def test_unrelated_tenant_cannot_read_lease(client, world):
    assert client.get(f"/api/v1/leases/{world['lease_id']}", headers=world["stranger"]).status_code == 403


def test_other_landlord_cannot_read_or_change_lease(client, world):
    assert client.get(f"/api/v1/leases/{world['lease_id']}", headers=world["b"]).status_code == 403
    assert client.post(f"/api/v1/leases/{world['lease_id']}/terminate", headers=world["b"]).status_code == 403


def test_leasing_tenant_can_read_own_lease(client, world):
    assert client.get(f"/api/v1/leases/{world['lease_id']}", headers=world["tenant"]).status_code == 200


def test_lease_lists_are_filtered(client, world):
    by_unit = client.get(f"/api/v1/leases/by-unit/{world['unit_id']}", headers=world["b"])
    assert by_unit.status_code == 200 and by_unit.json() == []
    by_tenant = client.get(f"/api/v1/leases/by-tenant/{world['tenant_id']}", headers=world["stranger"])
    assert by_tenant.status_code == 200 and by_tenant.json() == []
    own = client.get(f"/api/v1/leases/by-tenant/{world['tenant_id']}", headers=world["tenant"])
    assert [lease["id"] for lease in own.json()] == [world["lease_id"]]


def test_landlord_cannot_lease_own_unit_to_other_landlords_tenant(client, world):
    other_tenant = client.post(
        "/api/v1/tenants", json={"first_name": "B", "last_name": "T", "email": "bt@example.com"}, headers=world["b"]
    ).json()["id"]
    unit_2 = client.post(
        f"/api/v1/properties/{world['property_id']}/units", json={"unit_number": "2A", "rent_amount": 900}, headers=world["a"]
    ).json()["id"]
    resp = client.post(
        "/api/v1/leases",
        json={"unit_id": unit_2, "tenant_id": other_tenant, "start_date": "2026-01-01", "end_date": "2026-12-31", "rent_amount": 900},
        headers=world["a"],
    )
    assert resp.status_code == 403


# -- EX-05: tenant records ------------------------------------------------------

def test_other_landlord_cannot_access_tenant_record(client, world):
    tid = world["tenant_id"]
    assert client.get(f"/api/v1/tenants/{tid}", headers=world["b"]).status_code == 403
    assert client.patch(f"/api/v1/tenants/{tid}", json={"phone": "555"}, headers=world["b"]).status_code == 403
    assert client.delete(f"/api/v1/tenants/{tid}", headers=world["b"]).status_code == 403


def test_tenant_list_is_scoped_to_owner(client, world):
    assert client.get("/api/v1/tenants", headers=world["b"]).json() == []
    assert [t["id"] for t in client.get("/api/v1/tenants", headers=world["a"]).json()] == [world["tenant_id"]]


def test_admin_sees_all_tenants(client, world, admin_headers):
    assert [t["id"] for t in client.get("/api/v1/tenants", headers=admin_headers).json()] == [world["tenant_id"]]


# -- EX-06 / EX-07: maintenance -------------------------------------------------

def _file_request(client, headers, unit_id, **extra):
    return client.post(
        "/api/v1/maintenance-requests",
        json={"unit_id": unit_id, "title": "Leaky faucet", "description": "Kitchen sink", **extra},
        headers=headers,
    )


def test_unrelated_tenant_cannot_file_maintenance(client, world):
    assert _file_request(client, world["stranger"], world["unit_id"]).status_code == 403


def test_other_landlord_cannot_file_maintenance(client, world):
    assert _file_request(client, world["b"], world["unit_id"]).status_code == 403


def test_leasing_tenant_files_request_under_own_record(client, world):
    # Even if the tenant names someone else's tenant id, it is filed as theirs.
    resp = _file_request(client, world["tenant"], world["unit_id"], tenant_id=999)
    assert resp.status_code == 201
    assert resp.json()["tenant_id"] == world["tenant_id"]


def test_tenant_cannot_change_maintenance_status(client, world):
    request_id = _file_request(client, world["tenant"], world["unit_id"]).json()["id"]
    resp = client.patch(f"/api/v1/maintenance-requests/{request_id}", json={"status": "completed"}, headers=world["tenant"])
    assert resp.status_code == 403


def test_other_landlord_cannot_see_or_change_maintenance(client, world):
    request_id = _file_request(client, world["tenant"], world["unit_id"]).json()["id"]
    assert client.get(f"/api/v1/maintenance-requests/{request_id}", headers=world["b"]).status_code == 403
    resp = client.patch(f"/api/v1/maintenance-requests/{request_id}", json={"status": "completed"}, headers=world["b"])
    assert resp.status_code == 403
    assert client.get("/api/v1/maintenance-requests/open", headers=world["b"]).json() == []
    assert client.get(f"/api/v1/maintenance-requests/by-unit/{world['unit_id']}", headers=world["b"]).json() == []


def test_owner_and_tenant_see_maintenance(client, world):
    request_id = _file_request(client, world["tenant"], world["unit_id"]).json()["id"]
    assert [r["id"] for r in client.get("/api/v1/maintenance-requests/open", headers=world["a"]).json()] == [request_id]
    assert [r["id"] for r in client.get("/api/v1/maintenance-requests/open", headers=world["tenant"]).json()] == [request_id]
    assert client.get("/api/v1/maintenance-requests/open", headers=world["stranger"]).json() == []
    resp = client.patch(f"/api/v1/maintenance-requests/{request_id}", json={"status": "in_progress"}, headers=world["a"])
    assert resp.status_code == 200


def test_maintenance_on_missing_unit_is_404(client, world):
    assert _file_request(client, world["a"], 9999).status_code == 404


# -- EX-08 / EX-09: invoice and lease validation --------------------------------

def test_invoice_for_missing_lease_is_404(client, world):
    resp = client.post("/api/v1/invoices", json={"lease_id": 9999, "amount_due": 10, "due_date": "2026-03-01"}, headers=world["a"])
    assert resp.status_code == 404


@pytest.mark.parametrize("amount", [0, -5])
def test_invoice_amount_must_be_positive(client, world, amount):
    resp = client.post(
        "/api/v1/invoices", json={"lease_id": world["lease_id"], "amount_due": amount, "due_date": "2026-03-01"}, headers=world["a"]
    )
    assert resp.status_code == 422


@pytest.mark.parametrize("field,value", [("rent_amount", 0), ("rent_amount", -1), ("security_deposit", -1)])
def test_lease_amounts_are_validated(client, world, field, value):
    unit_2 = client.post(
        f"/api/v1/properties/{world['property_id']}/units", json={"unit_number": "2A", "rent_amount": 900}, headers=world["a"]
    ).json()["id"]
    body = {"unit_id": unit_2, "tenant_id": world["tenant_id"], "start_date": "2026-01-01", "end_date": "2026-12-31", "rent_amount": 900}
    body[field] = value
    assert client.post("/api/v1/leases", json=body, headers=world["a"]).status_code == 422


def test_lease_end_before_start_is_rejected(client, world):
    unit_2 = client.post(
        f"/api/v1/properties/{world['property_id']}/units", json={"unit_number": "2A", "rent_amount": 900}, headers=world["a"]
    ).json()["id"]
    resp = client.post(
        "/api/v1/leases",
        json={"unit_id": unit_2, "tenant_id": world["tenant_id"], "start_date": "2026-12-31", "end_date": "2026-01-01", "rent_amount": 900},
        headers=world["a"],
    )
    assert resp.status_code == 422


# -- payments rules ---------------------------------------------------------------

def test_paying_a_paid_invoice_is_a_conflict(client, world):
    url = f"/api/v1/invoices/{world['invoice_id']}/payments"
    assert client.post(url, json={"amount": 1200, "payment_method": "cash"}, headers=world["a"]).json()["status"] == "paid"
    assert client.post(url, json={"amount": 1, "payment_method": "cash"}, headers=world["a"]).status_code == 409


def test_refresh_overdue_only_touches_own_invoices(client, world):
    # Landlord B has their own past-due invoice; refreshing as B must not
    # return (or leak) landlord A's past-due invoice.
    past_due = (date.today() - timedelta(days=5)).isoformat()
    b_property = client.post("/api/v1/properties", json=PROPERTY, headers=world["b"]).json()["id"]
    b_unit = client.post(
        f"/api/v1/properties/{b_property}/units", json={"unit_number": "9", "rent_amount": 500}, headers=world["b"]
    ).json()["id"]
    b_tenant = client.post(
        "/api/v1/tenants", json={"first_name": "B", "last_name": "T", "email": "bt@example.com"}, headers=world["b"]
    ).json()["id"]
    b_lease = client.post(
        "/api/v1/leases",
        json={"unit_id": b_unit, "tenant_id": b_tenant, "start_date": "2026-01-01", "end_date": "2026-12-31", "rent_amount": 500},
        headers=world["b"],
    ).json()["id"]
    b_invoice = client.post(
        "/api/v1/invoices", json={"lease_id": b_lease, "amount_due": 500, "due_date": past_due}, headers=world["b"]
    ).json()["id"]
    future = (date.today() + timedelta(days=30)).isoformat()
    a_future = client.post(
        "/api/v1/invoices", json={"lease_id": world["lease_id"], "amount_due": 1200, "due_date": future}, headers=world["a"]
    ).json()["id"]

    resp = client.post("/api/v1/invoices/refresh-overdue", headers=world["b"])
    assert [inv["id"] for inv in resp.json()] == [b_invoice]
    assert resp.json()[0]["status"] == "overdue"

    # A's invoice due 2026-02-01 is untouched by B's refresh...
    assert client.get(f"/api/v1/invoices/{world['invoice_id']}", headers=world["a"]).json()["status"] == "pending"
    # ...and A's own refresh flags it, but not the one that isn't due yet.
    resp = client.post("/api/v1/invoices/refresh-overdue", headers=world["a"])
    assert [inv["id"] for inv in resp.json()] == [world["invoice_id"]]
    assert client.get(f"/api/v1/invoices/{a_future}", headers=world["a"]).json()["status"] == "pending"


def test_tenant_cannot_refresh_overdue(client, world):
    assert client.post("/api/v1/invoices/refresh-overdue", headers=world["tenant"]).status_code == 403
