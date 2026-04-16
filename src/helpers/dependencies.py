import logging
from fastapi import Header
from helpers.exceptions import CustomAPIException
from helpers.ResponseEnums import ResponseSignal

logger = logging.getLogger(__name__)

async def get_session_id(x_session_id: str = Header(..., alias="X-Session-ID", min_length=1)) -> str:
    """
    Dependency to statically extract the X-Session-ID header for stateless authentication.
    The client must provide this header as a UUID to query or modify isolated project data.
    """
    if not x_session_id:
        logger.warning("Rejecting request: Missing X-Session-ID")
        raise CustomAPIException(
            signal_enum=ResponseSignal.VALIDATION_FAILED,
            status_code=401,
            dev_detail="Missing X-Session-ID header for stateless authentication."
        )
    return x_session_id
