import logging

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.config import settings
from app.core.logging_config import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.SERVICE_NAME,
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",
    debug=settings.DEBUG,
)

app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.SERVICE_NAME} service (LOG_LEVEL={settings.LOG_LEVEL})")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.SERVICE_NAME} service")
