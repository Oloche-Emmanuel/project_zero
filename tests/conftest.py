import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from rentalapp.database import Base, get_db
from rentalapp.main import create_app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)


def register_and_login(client, email="landlord@example.com", role="landlord"):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret", "full_name": "Test User", "role": role},
    )
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": "supersecret"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
