from logging.config import dictConfig

from helpers.config import get_settings

# Read the environment variable (defaults to development if missing)
ENV = get_settings().ENVIRONMENT.lower() if get_settings().ENVIRONMENT else "development"


def get_log_config():
    selected_formatter = "production_formatter" if ENV == "production" else "development_formatter"
    log_level = "INFO" if ENV == "production" else "DEBUG"

    return {
        "version": 1,
        "disable_existing_loggers": False,
        # 1. ADD THE FILTER: This safely handles logs that don't have a correlation_id
        "filters": {
            "correlation_id": {
                "()": "asgi_correlation_id.CorrelationIdFilter",
                "uuid_length": 32,  # Optional: trims the ID length for cleaner logs
                "default_value": "-",  # Prints a hyphen if there is no web request
            },
        },
        "formatters": {
            "development_formatter": {
                # Notice %(correlation_id)s is in here!
                "format": "%(asctime)s | [%(correlation_id)s] | %(levelname)-8s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "production_formatter": {
                "()": "pythonjsonlogger.JsonFormatter",
                "fmt": "%(asctime)s %(correlation_id)s %(levelname)s %(name)s %(message)s %(filename)s %(lineno)d",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": selected_formatter,
                "level": log_level,
                # 2. ATTACH THE FILTER TO THE HANDLER
                "filters": ["correlation_id"],
            },
        },
        # 3. SILENCE Other Packages: Tell Packages to only log INFO or WARNING, never DEBUG
        "loggers": {
            "pymongo": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "docling": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "python_multipart": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "multipart": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "urllib3.connectionpool": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "filelock": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "httpcore": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "qdrant_client": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "httpx": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": log_level,
        },
    }


def setup_logging():
    dictConfig(get_log_config())
