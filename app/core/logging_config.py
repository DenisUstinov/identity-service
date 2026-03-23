import logging
import sys

from app.config import settings


def setup_logging() -> None:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    stream = sys.stdout if settings.LOG_OUTPUT.lower() == "stdout" else sys.stderr

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)

    logging.basicConfig(
        level=log_level,
        handlers=[handler],
        force=True,
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: Level={settings.LOG_LEVEL}, Output={settings.LOG_OUTPUT}")
