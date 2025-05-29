import logging
from config import LOG_LEVEL, LOG_FORMAT

def setup_logger(name="IntegrationService"):
    """Configures and returns a logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    # Prevent duplicate handlers if logger is already configured
    if not logger.handlers:
        # Console Handler
        ch = logging.StreamHandler()
        ch.setLevel(LOG_LEVEL)
        formatter = logging.Formatter(LOG_FORMAT)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File Handler
        log_file_path = "integration_service.log"
        fh = logging.FileHandler(log_file_path)
        fh.setLevel(LOG_LEVEL)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.info(f"Logging to file: {log_file_path}")

    return logger

if __name__ == "__main__":
    logger = setup_logger("TestLogger")
    logger.debug("This is a debug message.") # Won't show if LOG_LEVEL is INFO
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")
