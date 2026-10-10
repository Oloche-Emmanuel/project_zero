from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from rentalapp.config import get_settings
from rentalapp.database import Base

# Import every module's models so Base.metadata is fully populated for
# autogenerate. New modules must add their import here too.
from rentalapp.modules.leases import models as leases_models  # noqa: F401
from rentalapp.modules.maintenance import models as maintenance_models  # noqa: F401
from rentalapp.modules.payments import models as payments_models  # noqa: F401
from rentalapp.modules.properties import models as properties_models  # noqa: F401
from rentalapp.modules.tenants import models as tenants_models  # noqa: F401
from rentalapp.modules.users import models as users_models  # noqa: F401

config = context.config

# Only configure logging when run from the alembic CLI; when the app runs
# migrations at startup (rentalapp.migrate), reconfiguring logging here
# would silence uvicorn's loggers.
if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name)

# The app's settings are the default; rentalapp.migrate passes its own URL.
# '%' is escaped because the config object uses ConfigParser interpolation.
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", get_settings().database_url.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        # render_as_batch lets ALTER-style migrations work on SQLite too.
        context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
