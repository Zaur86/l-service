"""
Contains custom warnings related to time, dates, and timezones.
"""

from app.warnings.base_warning import CustomWarning


class TimezoneWarning(CustomWarning):
    """Warning raised when the provided time has a different timezone, but the process continues."""
    pass
