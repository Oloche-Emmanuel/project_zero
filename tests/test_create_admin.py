from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from rentalapp import create_admin
from rentalapp.core.security import verify_password
from rentalapp.migrate import upgrade_database
from rentalapp.modules.users.models import User, UserRole


def _setup(tmp_path, monkeypatch, passwords):
    url = f"sqlite:///{(tmp_path / 'app.db').as_posix()}"
    upgrade_database(url)
    Session = sessionmaker(bind=create_engine(url))
    monkeypatch.setattr(create_admin, "SessionLocal", Session)
    monkeypatch.setattr(create_admin, "upgrade_database", lambda: None)
    answers = iter(passwords)
    monkeypatch.setattr(create_admin.getpass, "getpass", lambda prompt="": next(answers))
    return Session


def test_creates_admin(tmp_path, monkeypatch):
    Session = _setup(tmp_path, monkeypatch, ["correct-horse", "correct-horse"])
    assert create_admin.main(["boss@example.com", "The Boss"]) == 0
    with Session() as db:
        user = db.scalars(select(User).where(User.email == "boss@example.com")).one()
        assert user.role == UserRole.ADMIN
        assert verify_password("correct-horse", user.hashed_password)


def test_rejects_mismatched_or_short_password(tmp_path, monkeypatch):
    Session = _setup(tmp_path, monkeypatch, ["short", "short"])
    assert create_admin.main(["boss@example.com"]) == 1
    with Session() as db:
        assert db.scalars(select(User)).first() is None


def test_promotes_existing_user(tmp_path, monkeypatch):
    Session = _setup(tmp_path, monkeypatch, [])
    with Session() as db:
        db.add(User(email="l@example.com", hashed_password="x", full_name="L", role=UserRole.LANDLORD))
        db.commit()
    assert create_admin.main(["l@example.com"]) == 0
    with Session() as db:
        assert db.scalars(select(User)).one().role == UserRole.ADMIN
