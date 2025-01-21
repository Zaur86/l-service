"""
Contains custom errors related to parameter validation.
"""

from app.errors.base_error import CustomError


class InvalidParameterValueError(CustomError):
    """Raised when a parameter has an invalid value."""
    pass
