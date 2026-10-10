import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
# Minimum bcrypt cost keeps the suite fast; production uses the default (12).
os.environ.setdefault("BCRYPT_ROUNDS", "4")

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

    app = create_app(run_migrations=False)

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


@pytest.fixture()
def admin_headers(client):
    """Auth headers for an admin, inserted directly into the test database
    (public sign-up cannot create admins; production uses create_admin)."""
    from rentalapp.core.security import hash_password
    from rentalapp.modules.users.models import User, UserRole

    db_gen = client.app.dependency_overrides[get_db]()
    db = next(db_gen)
    db.add(User(email="admin@example.com", hashed_password=hash_password("supersecret"), full_name="Admin", role=UserRole.ADMIN))
    db.commit()
    db_gen.close()

    resp = client.post("/api/v1/auth/login", data={"username": "admin@example.com", "password": "supersecret"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
