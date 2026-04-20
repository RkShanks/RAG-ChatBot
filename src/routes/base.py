import logging

from fastapi import APIRouter, Depends, Request

from helpers.config import Settings, get_settings
from helpers.exceptions import CustomAPIException
from helpers.ResponseEnums import ResponseSignal

logger = logging.getLogger(__name__)

base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"],
)


@base_router.get("/")
async def welcome(request: Request, app_settings: Settings = Depends(get_settings)):

    app_name = app_settings.APP_NAME
    app_version = app_settings.APP_VERSION
    db_client = request.app.state.db_client

    db_connection_status = await check_db_connection(db_client=db_client)

    return {
        "app_name": app_name,
        "app_version": app_version,
        "db_connection_status": db_connection_status,
    }


async def check_db_connection(db_client):
    try:
        await db_client.command("ping")
        return ResponseSignal.DB_CONNECTION_SUCCESS.signal

    except Exception as e:
        raise CustomAPIException(
            signal_enum=ResponseSignal.DB_CONNECTION_FAILED,
            status_code=503,  # 503 Service Unavailable is the standard for failed health checks
            dev_detail="Database ping failed during system health check.",
        ) from e
