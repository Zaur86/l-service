class RuleNotFoundError(Exception):
    """Raised when a rules file for the given index and table is not found."""
    pass


class EtlProcessError(Exception):
    """Raised for general ETL process errors."""
    pass


class ElasticSearchError(Exception):
    """Raised for errors related to Elasticsearch operations."""
    pass


class DatabaseInsertError(Exception):
    """Raised for errors during data insertion into the database."""
    pass


class MissingFieldError(Exception):
    """Exception for missing required fields."""
    pass


class EmptyValueError(Exception):
    """Raised when empty values are not allowed."""
    pass


class InvalidFormatError(Exception):
    """Raised when the provided time format is invalid."""
    pass


class TimezoneMismatchError(Exception):
    """Raised when the provided time has a different timezone and an error is required."""
    pass


class InvalidParameterValueError(Exception):
    """Raised when a parameter has an invalid value."""
    pass


class NestedKeyError(Exception):
    """Exception raised when the specified nested key path does not exist."""
    pass
