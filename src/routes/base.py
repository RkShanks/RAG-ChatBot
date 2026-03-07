import logging

from fastapi import APIRouter, Depends, Request

from helpers.config import Settings, get_settings
from models.enums.ResponseEnums import ResponseSignal

base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"],
)


@base_router.get("/")
async def welcome(request: Request, app_settings: Settings = Depends(get_settings)):

    app_name = app_settings.APP_NAME
    app_version = app_settings.APP_VERSION
    db_client = request.app.state.db_client

    db_connection_status = check_db_connection(db_client=db_client)
    return {
        "app_name": app_name,
        "app_version": app_version,
        "db_connection_status": db_connection_status,
    }


def check_db_connection(db_client):
    try:
        # The ping command is used to check the connection to the database
        db_client.command("ping")
        return ResponseSignal.DB_CONNECTION_SUCCESS.value
    except Exception as e:
        logging.getLogger("uvicorn.error").error(f"Database connection failed: {e}")
        return ResponseSignal.DB_CONNECTION_FAILED.value
