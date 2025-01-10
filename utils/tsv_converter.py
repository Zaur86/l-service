from dataclasses import dataclass, field
from multiprocessing import Pool
from io import StringIO
import json
import os
import warnings
from typing import Dict, List, Any, Optional
from models.additional_fields import AdditionalFields
from services.errors import MissingFieldError, NestedKeyError
from services.warnings import ExcessiveProcessesWarning, JsonLengthWarning


@dataclass
class TSVConverter:
	"""
	A class for converting a list of dictionaries to a TSV (Tab-Separated Values) format.

	Attributes:
	----------
	fields_mapping : Dict[str, str]
		A mapping of input dictionary keys to column names in the resulting TSV file.
	not_null_fields : List[str], optional
		A list of fields that must not be empty in the input data.
	missing_value_placeholder : str, optional
		A placeholder for missing values (default is "NULL").
	num_processes : int, optional
		Number of parallel processes to use for conversion (default is 4).
	additional_fields : List[AdditionalFields], optional
		A list of additional fields to be added to the output TSV, either as constant values
		or calculated using functions.
	max_json_length : int, optional
		Maximum allowed length for JSON strings (default: 100000).
	nested_key : Optional[List[str]], optional
		List of keys representing the path to the nested data.

	Methods:
	-------
	add_additional_fields(additional_fields: AdditionalFields):
		Adds additional fields to the converter.
	convert(data: List[Dict[str, Any]]) -> str:
		Converts the input data to a TSV string.
	"""

	fields_mapping: Dict[str, str]
	not_null_fields: List[str] = field(default_factory=list)
	missing_value_placeholder: str = "NULL"
	num_processes: int = 4
	additional_fields: List[AdditionalFields] = field(default_factory=list)
	max_json_length: int = 100000
	nested_key: Optional[List[str]] = None
	debug: bool = False

	def __post_init__(self):
		"""Check available CPU cores and issue a warning if num_processes exceeds them."""
		available_cores = os.cpu_count() or 1
		if self.num_processes > available_cores:
			warnings.warn(
				ExcessiveProcessesWarning(self.num_processes, available_cores),
				stacklevel=2
			)
		if self.debug:
			print(f"[DEBUG] Initialized TSVConverter with {self.num_processes} processes.")

	def _extract_nested_data(self, row: Dict[str, Any]) -> Dict[str, Any]:
		"""Extract data from a nested dictionary."""
		current_level = row
		for key in self.nested_key:
			if not isinstance(current_level, dict) or key not in current_level:
				raise NestedKeyError(
					f"Failed to extract data at nested key path {self.nested_key}. "
					f"Current level: {current_level}"
				)
			current_level = current_level[key]
		if self.debug:
			print(f"[DEBUG] Extracted nested data: {current_level}")
		return current_level

	def add_additional_fields(self, additional_fields: AdditionalFields):
		"""Add additional fields to the converter."""
		self.additional_fields.append(additional_fields)

	def _sanitize_value(self, value: Any) -> str:
		"""Sanitize the value by replacing tabs, newlines, and converting JSON to string if needed."""
		if isinstance(value, (dict, list)):
			value = json.dumps(value)  # Convert JSON to string
			if len(value) > self.max_json_length:
				warnings.warn(
					JsonLengthWarning(self.max_json_length, len(value)),
					stacklevel=2
				)
		sanitized = str(value).replace("\t", " ").replace("\n", " ")
		if self.debug:
			print(f"[DEBUG] Sanitized value: {sanitized}")
		return sanitized

	def _process_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
		"""Process a single row, extracting nested data and applying additional fields if necessary."""
		if self.nested_key:
			row = self._extract_nested_data(row)
		if self.additional_fields:
			self._apply_additional_fields(row)
		if self.debug:
			print(f"[DEBUG] Processed row: {row}")
		return row

	def _apply_additional_fields(self, row: Dict[str, Any]):
		"""Apply all additional fields to the given row."""
		for additional_field in self.additional_fields:
			if callable(additional_field.value):  # If it's a function
				# Build function arguments from input mapping
				function_args = {
					func_arg: row[source_field]
					for func_arg, source_field in additional_field.input_mapping.items()
					if source_field in row
				}

				if self.debug:
					print(f"[DEBUG] Function args: {function_args}")
					print(f"[DEBUG] Static args: {additional_field.static_args}")

				# Check that all required arguments are provided
				missing_args = set(additional_field.input_mapping.values()) - set(row.keys())
				if missing_args:
					raise MissingFieldError(f"Required fields for function are missing: {missing_args}")

				# Add static arguments
				function_args.update(additional_field.static_args)

				# Call the function and store the result
				result = additional_field.value(**function_args)

				if self.debug:
					print(f"[DEBUG] Function result: {result}")

				# Apply output mapping
				if isinstance(result, dict):
					for out_key, out_value in result.items():
						mapped_field = additional_field.output_mapping.get(out_key, out_key)
						row[mapped_field] = out_value
				else:
					raise ValueError("Function result must be a dictionary with keys matching output_mapping.")
			else:  # If it's a constant value
				# Directly add constant value to all output fields
				for output_field in additional_field.output_fields:
					row[output_field] = additional_field.value
		if self.debug:
			print(f"[DEBUG] Applied additional fields: {row}")
		pass

	def _process_chunk(self, chunk: List[Dict[str, Any]]) -> str:
		"""Process a chunk of data and convert it to TSV lines."""
		buffer = StringIO()
		for row in chunk:
			processed_row = self._process_row(row)
			line = []

			# Process only fields from fields_mapping
			for key, tsv_field in self.fields_mapping.items():
				if key in self.not_null_fields and key not in processed_row:
					raise MissingFieldError(f"Field '{field}' is missing in row: {processed_row}")

				value = processed_row.get(key, self.missing_value_placeholder)
				sanitized_value = self._sanitize_value(value)
				line.append(sanitized_value)

				if self.debug:
					print(f"[DEBUG] line by fields_mapping with key {key} and tsv_field {tsv_field}: {line}")

			# Append additional fields
			for additional_field in self.additional_fields:

				# constant values
				for output_field in additional_field.output_fields:
					value = processed_row.get(output_field, self.missing_value_placeholder)
					sanitized_value = self._sanitize_value(value)
					line.append(sanitized_value)

					if self.debug:
						print(f"[DEBUG] line with constant additional field {output_field}: {line}")

				# dynamic values from function
				for output_field in additional_field.output_mapping.values():
					if output_field in processed_row:
						value = processed_row.get(output_field, self.missing_value_placeholder)
						sanitized_value = self._sanitize_value(value)
						line.append(sanitized_value)
					else:
						raise MissingFieldError(f"Field '{output_field}' is missing in row: {processed_row}")

					if self.debug:
						print(f"[DEBUG] line with additional field from function {output_field}: {line}")

			buffer.write("\t".join(line) + "\n")
		return buffer.getvalue()

	def _split_data(self, data: List[Dict[str, Any]], num_chunks: int) -> List[List[Dict[str, Any]]]:
		"""Split data into chunks for parallel processing."""
		chunk_size = max(1, len(data) // num_chunks)
		split_data = [data[i * chunk_size: (i + 1) * chunk_size] for i in range(num_chunks)]
		if self.debug:
			print(f"[DEBUG] Split data into {len(split_data)} chunks.")
		return split_data

	def convert(self, data: List[Dict[str, Any]]) -> str:
		"""Main method to convert data to TSV."""

		# Make header
		header = [self.fields_mapping[key] for key in self.fields_mapping]
		for additional_field in self.additional_fields:
			if callable(additional_field.value):
				header.extend(additional_field.output_mapping.values())
			else:
				header.extend(additional_field.output_fields)
		if self.debug:
			print(f"[DEBUG] Header: {header}")

		final_buffer = StringIO()

		# Make chunks
		chunks = self._split_data(data, self.num_processes)
		with Pool(self.num_processes) as pool:
			results = pool.map(self._process_chunk, chunks)

		# Add header
		final_buffer.write("\t".join(header) + "\n")

		# Combine all chunks
		for result in results:
			final_buffer.write(result)

		if self.debug:
			print(f"[DEBUG] Final TSV size: {final_buffer.tell()} bytes.")

		return final_buffer.getvalue()
