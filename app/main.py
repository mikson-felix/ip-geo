from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from app.api.exception_handlers import register_exception_handlers
from app.api.healthcheck import router as healthcheck_router
from app.api.v1.routes import router as v1_router
from app.bootstrap import run_startup_checks
from app.config import get_settings
from app.ioc import get_providers
from app.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings)

    await run_startup_checks(settings)
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    container: AsyncContainer = make_async_container(*get_providers())
    setup_dishka(container=container, app=app)
    app.include_router(v1_router, prefix="/api/v1")
    app.include_router(healthcheck_router)
    register_exception_handlers(app)
    return app


app = create_app()
