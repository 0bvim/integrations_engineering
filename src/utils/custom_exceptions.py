# src/utils/custom_exceptions.py

class IntegrationBaseException(Exception):
    """Base class for custom exceptions in this application."""
    pass

class ConfigError(IntegrationBaseException):
    """Raised for configuration errors."""
    pass

class ClientFileError(IntegrationBaseException):
    """Raised for errors related to client file operations (read/write)."""
    pass

class TracOSDBError(IntegrationBaseException):
    """Raised for errors related to TracOS MongoDB operations."""
    pass

class TranslationError(IntegrationBaseException):
    """Raised for errors during data translation or validation."""
    pass

class DataValidationError(TranslationError):
    """Raised specifically for data validation failures during translation."""
    pass
