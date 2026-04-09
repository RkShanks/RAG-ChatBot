from typing import Optional

from .ResponseEnums import ResponseSignal


class CustomAPIException(Exception):
    """
    A unified exception class to transport business logic errors to the FastAPI exception handler.
    """

    def __init__(
        self,
        signal_enum: ResponseSignal,  # Require the whole enum object
        status_code: int = 500,
        dev_detail: Optional[str] = None,
        custom_message: Optional[str] = None,
    ):
        # 1. Grab the signal string directly from the enum
        self.signal = signal_enum.signal

        # 2. Use the Enum's default message, UNLESS you provide a custom one
        self.message = custom_message or signal_enum.message

        self.status_code = status_code
        self.dev_detail = dev_detail

        # 3. call the parent Exception class so Python's internal traceback works perfectly
        super().__init__(self.message)
