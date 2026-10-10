from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from rentalapp.config import get_settings
from rentalapp.core.exceptions import AppError
from rentalapp.migrate import upgrade_database

# Import models so they register on Base.metadata.
from rentalapp.modules.leases import models as _leases_models  # noqa: F401
from rentalapp.modules.leases.router import router as leases_router
from rentalapp.modules.maintenance import models as _maintenance_models  # noqa: F401
from rentalapp.modules.maintenance.router import router as maintenance_router
from rentalapp.modules.payments import models as _payments_models  # noqa: F401
from rentalapp.modules.payments.router import router as payments_router
from rentalapp.modules.properties import models as _properties_models  # noqa: F401
from rentalapp.modules.properties.router import router as properties_router
from rentalapp.modules.tenants import models as _tenants_models  # noqa: F401
from rentalapp.modules.tenants.router import router as tenants_router
from rentalapp.modules.users import models as _users_models  # noqa: F401
from rentalapp.modules.users.router import router as users_router

settings = get_settings()

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


def create_app(run_migrations: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Apply any pending Alembic migrations, so every environment (local
        # SQLite, Render Postgres) is on the latest schema before serving.
        # Tests build their own throwaway schema and pass False.
        if run_migrations:
            upgrade_database()
        yield

    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    # The frontend authenticates with a bearer token (not cookies), so a
    # permissive CORS policy carries no CSRF risk and just makes local/
    # alternate-origin frontend development easier.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    # New feature modules register their router here and nowhere else.
    app.include_router(users_router)
    app.include_router(properties_router)
    app.include_router(tenants_router)
    app.include_router(leases_router)
    app.include_router(payments_router)
    app.include_router(maintenance_router)

    @app.get("/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok"}

    # Static frontend, mounted last so it never shadows the API routes above.
    if FRONTEND_DIR.is_dir():
        app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

    return app


app = create_app()
