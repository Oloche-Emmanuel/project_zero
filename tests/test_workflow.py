from tests.conftest import register_and_login


def test_register_and_login(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "a@example.com", "password": "secret123", "full_name": "A B", "role": "tenant"},
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == "a@example.com"

    resp = client.post("/api/v1/auth/login", data={"username": "a@example.com", "password": "secret123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

    resp = client.post("/api/v1/auth/login", data={"username": "a@example.com", "password": "wrong"})
    assert resp.status_code == 401


def test_full_property_lease_payment_workflow(client):
    headers = register_and_login(client)

    resp = client.post(
        "/api/v1/properties",
        json={
            "name": "Maple Apartments",
            "address_line1": "123 Maple St",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62704",
            "property_type": "apartment",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    property_id = resp.json()["id"]

    resp = client.post(
        f"/api/v1/properties/{property_id}/units",
        json={"unit_number": "1A", "bedrooms": 2, "bathrooms": 1.0, "rent_amount": 1200.0},
        headers=headers,
    )
    assert resp.status_code == 201
    unit = resp.json()
    assert unit["status"] == "vacant"
    unit_id = unit["id"]

    resp = client.post(
        "/api/v1/tenants",
        json={"first_name": "Jane", "last_name": "Doe", "email": "jane@example.com"},
        headers=headers,
    )
    assert resp.status_code == 201
    tenant_id = resp.json()["id"]

    resp = client.post(
        "/api/v1/leases",
        json={
            "unit_id": unit_id,
            "tenant_id": tenant_id,
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "rent_amount": 1200.0,
            "security_deposit": 1200.0,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    lease_id = resp.json()["id"]

    # Unit should now be occupied.
    resp = client.get(f"/api/v1/properties/{property_id}/units", headers=headers)
    assert resp.json()[0]["status"] == "occupied"

    # A second active lease on the same unit is rejected.
    resp = client.post(
        "/api/v1/leases",
        json={
            "unit_id": unit_id,
            "tenant_id": tenant_id,
            "start_date": "2026-02-01",
            "end_date": "2026-12-31",
            "rent_amount": 1200.0,
        },
        headers=headers,
    )
    assert resp.status_code == 409

    resp = client.post(
        "/api/v1/invoices",
        json={"lease_id": lease_id, "amount_due": 1200.0, "due_date": "2026-02-01"},
        headers=headers,
    )
    assert resp.status_code == 201
    invoice_id = resp.json()["id"]
    assert resp.json()["status"] == "pending"

    resp = client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        json={"amount": 500.0, "payment_method": "bank_transfer"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "partial"

    resp = client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        json={"amount": 700.0, "payment_method": "bank_transfer"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "paid"

    resp = client.post(
        "/api/v1/maintenance-requests",
        json={"unit_id": unit_id, "tenant_id": tenant_id, "title": "Leaky faucet", "description": "Kitchen sink"},
        headers=headers,
    )
    assert resp.status_code == 201
    request_id = resp.json()["id"]

    resp = client.patch(
        f"/api/v1/maintenance-requests/{request_id}", json={"status": "completed"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["resolved_at"] is not None

    # Terminating the lease frees the unit up again.
    resp = client.post(f"/api/v1/leases/{lease_id}/terminate", headers=headers)
    assert resp.status_code == 200
    resp = client.get(f"/api/v1/properties/{property_id}/units", headers=headers)
    assert resp.json()[0]["status"] == "vacant"


def test_tenant_role_cannot_create_property(client):
    headers = register_and_login(client, email="tenant@example.com", role="tenant")
    resp = client.post(
        "/api/v1/properties",
        json={
            "name": "X",
            "address_line1": "1 St",
            "city": "C",
            "state": "S",
            "zip_code": "00000",
            "property_type": "condo",
        },
        headers=headers,
    )
    assert resp.status_code == 403


def test_landlord_cannot_see_other_landlords_property(client):
    headers_a = register_and_login(client, email="landlord_a@example.com", role="landlord")
    headers_b = register_and_login(client, email="landlord_b@example.com", role="landlord")

    resp = client.post(
        "/api/v1/properties",
        json={
            "name": "A's Place",
            "address_line1": "1 St",
            "city": "C",
            "state": "S",
            "zip_code": "00000",
            "property_type": "condo",
        },
        headers=headers_a,
    )
    property_id = resp.json()["id"]

    resp = client.get(f"/api/v1/properties/{property_id}", headers=headers_b)
    assert resp.status_code == 403
