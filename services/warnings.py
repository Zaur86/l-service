class ExcessiveProcessesWarning(UserWarning):
	"""Warning for excessive number of processes."""

	def __init__(self, num_processes: int, available_cores: int):
		super().__init__(f"Requested {num_processes} processes, but only {available_cores} cores are available.")


class TimezoneWarning(Warning):
	"""Warning raised when the provided time has a different timezone, but the process continues."""
	pass


class JsonLengthWarning(UserWarning):
	"""Warning for excessively long JSON strings."""
	def __init__(self, length: int, max_length: int):
		super().__init__(f"JSON string length {length} exceeds the maximum allowed length of {max_length} characters.")
