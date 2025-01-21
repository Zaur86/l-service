class InternalRawStorageService:
    """
    Base class for working with internal raw data storage.
    """

    def prepare_extraction(self, *args, **kwargs):
        """
        Prepares for data extraction.
        Must be implemented in subclasses.
        """
        raise NotImplementedError("The 'prepare_extraction' method must be implemented in a subclass")

    def extract_data(self, *args, **kwargs):
        """
        Method for extracting data.
        Must be implemented in subclasses.
        """
        raise NotImplementedError("The 'extract_data' method must be implemented in a subclass")
