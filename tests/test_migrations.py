"""Schema migration tests (Alembic), run against throwaway SQLite files."""

from alembic import command
from sqlalchemy import create_engine, inspect, text

from rentalapp.migrate import MIGRATIONS_DIR, upgrade_database


def _url(tmp_path):
    return f"sqlite:///{(tmp_path / 'app.db').as_posix()}"


def _version(url):
    engine = create_engine(url)
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    engine.dispose()
    return version


def _config(url):
    from alembic.config import Config

    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", url)
    config.attributes["configure_logger"] = False
    return config


def test_upgrade_creates_full_schema_on_empty_database(tmp_path):
    url = _url(tmp_path)
    upgrade_database(url)

    engine = create_engine(url)
    insp = inspect(engine)
    assert {"users", "properties", "units", "tenants", "leases", "invoices", "maintenance_requests"} <= set(insp.get_table_names())
    assert "owner_id" in {c["name"] for c in insp.get_columns("tenants")}
    engine.dispose()
    assert _version(url) == "0002"


def test_upgrade_is_idempotent(tmp_path):
    url = _url(tmp_path)
    upgrade_database(url)
    upgrade_database(url)
    assert _version(url) == "0002"


def test_legacy_create_all_database_is_stamped_and_backfilled(tmp_path):
    """A database made by older builds (create_all, no alembic_version)
    gets the new column, and existing tenants inherit an owner from their
    lease; tenants with no lease stay unowned."""
    url = _url(tmp_path)
    command.upgrade(_config(url), "0001")

    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE alembic_version"))
        conn.execute(text(
            "INSERT INTO users (id, email, hashed_password, full_name, role, is_active) "
            "VALUES (7, 'l@example.com', 'x', 'L', 'LANDLORD', 1)"
        ))
        conn.execute(text(
            "INSERT INTO properties (id, owner_id, name, address_line1, city, state, zip_code, property_type) "
            "VALUES (1, 7, 'P', '1 St', 'C', 'S', '0', 'CONDO')"
        ))
        conn.execute(text(
            "INSERT INTO units (id, property_id, unit_number, bedrooms, bathrooms, rent_amount, status) "
            "VALUES (1, 1, '1A', 1, 1.0, 100, 'OCCUPIED')"
        ))
        conn.execute(text("INSERT INTO tenants (id, first_name, last_name, email) VALUES (1, 'Leased', 'T', 'a@example.com')"))
        conn.execute(text("INSERT INTO tenants (id, first_name, last_name, email) VALUES (2, 'Unleased', 'T', 'b@example.com')"))
        conn.execute(text(
            "INSERT INTO leases (id, unit_id, tenant_id, start_date, end_date, rent_amount, security_deposit, status) "
            "VALUES (1, 1, 1, '2026-01-01', '2026-12-31', 100, 0, 'ACTIVE')"
        ))
    engine.dispose()

    upgrade_database(url)

    assert _version(url) == "0002"
    engine = create_engine(url)
    with engine.connect() as conn:
        owners = dict(conn.execute(text("SELECT id, owner_id FROM tenants ORDER BY id")).all())
    engine.dispose()
    assert owners == {1: 7, 2: None}


def test_downgrade_removes_tenant_owner(tmp_path):
    url = _url(tmp_path)
    upgrade_database(url)
    command.downgrade(_config(url), "0001")

    engine = create_engine(url)
    assert "owner_id" not in {c["name"] for c in inspect(engine).get_columns("tenants")}
    engine.dispose()
    assert _version(url) == "0001"
