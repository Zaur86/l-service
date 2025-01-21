"""
Contains custom errors related to interactions with external services
"""


from app.errors.base_error import CustomError


class ElasticSearchError(CustomError):
    """Raised for errors related to Elasticsearch operations."""
    pass
