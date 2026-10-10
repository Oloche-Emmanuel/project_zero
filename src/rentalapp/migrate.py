from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from rentalapp.config import get_settings

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"

# The revision that matches the schema older builds created with
# Base.metadata.create_all(), before Alembic migrations were introduced.
BASELINE_REVISION = "0001"


def upgrade_database(database_url: str | None = None) -> None:
    """Bring the database schema up to date (`alembic upgrade head`).

    Databases created by earlier builds via create_all() have the tables but
    no alembic_version table; those are stamped at the baseline first so
    only the newer migrations run against them.
    """
    url = database_url or get_settings().database_url

    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    config.attributes["configure_logger"] = False

    engine = create_engine(url)
    try:
        tables = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    if "alembic_version" not in tables and "users" in tables:
        command.stamp(config, BASELINE_REVISION)
    command.upgrade(config, "head")


if __name__ == "__main__":
    upgrade_database()
