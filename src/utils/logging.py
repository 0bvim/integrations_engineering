import sys
import os
from loguru import logger

def setup_logging():
    """Configure application logging"""

    # Remove the default handler
    logger.remove()

    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="INFO",
    )

    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger.add(
        os.path.join(log_dir, "errors.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="ERROR",
        rotation="10 MB",
        retention="1 week",
    )
