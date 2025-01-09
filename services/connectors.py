from dataclasses import dataclass, field
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.errors import ElasticSearchError
from typing import List
import logging


@dataclass
class ElasticSearchConnector:
	"""
	A connector for interacting with an Elasticsearch cluster.

	This class provides functionality to connect to Elasticsearch using either
	standard credentials or AWS IAM authentication. It also includes a method
	to fetch data in batches using the scroll API.

	Attributes:
	host (str): The Elasticsearch host address.
	port (int): The Elasticsearch port.
	use_iam (bool): Whether to use AWS IAM authentication.
	aws_profile (str, optional): The AWS profile name for authentication.
	aws_region (str, optional): The AWS region for IAM authentication.
	aws_service (str): The AWS service, defaults to 'es'.
	client (Elasticsearch): The initialized Elasticsearch client.
	"""
	host: str
	port: int
	use_iam: bool
	aws_profile: str = None
	aws_region: str = None
	aws_service: str = 'es'
	client: Elasticsearch = field(init=False)

	def __post_init__(self):
		# Initialize Elasticsearch client with optional IAM authentication
		if self.use_iam:
			# Set up AWS session and retrieve credentials
			session = boto3.Session(profile_name=self.aws_profile, region_name=self.aws_region)
			credentials = session.get_credentials()
			access_key = credentials.access_key
			secret_key = credentials.secret_key
			# Create AWS4Auth object for secure HTTP requests
			awsauth = AWS4Auth(
				access_key,
				secret_key,
				self.aws_region,
				self.aws_service
			)
			# Initialize Elasticsearch client with secure settings
			self.client = Elasticsearch(
				hosts=[{'host': self.host, 'port': self.port}],
				http_auth=awsauth,
				use_ssl=True,
				verify_certs=True,
				connection_class=RequestsHttpConnection
			)
		else:
			# Initialize Elasticsearch client without IAM authentication
			self.client = Elasticsearch(hosts=[{'host': self.host, 'port': self.port}])

	def fetch_data(
			self, index: str, query: dict, source_fields: List[str],
			batch_size: int, scroll: str
	):
		"""
		Fetch data from an Elasticsearch index in batches using scroll API.

		:param index: Name of the Elasticsearch index
		:param query: Query to filter the data
		:param source_fields: List of fields to retrieve from documents
		:param batch_size: Number of documents to fetch per batch
		:param scroll: Duration for keeping the search context alive
		"""
		logging.info(f"Fetching data from index: {index} with batch size: {batch_size}")
		# Add source fields to the query
		query["_source"] = source_fields
		try:
			# Perform initial search query
			response = self.client.search(index=index, body=query, scroll=scroll, size=batch_size)
		except Exception as e:
			# Raise a custom error if the query fails
			raise ElasticSearchError(f"Failed to scroll Elasticsearch data: {str(e)}")
		# Retrieve scroll ID and initial batch of hits
		scroll_id = response.get('_scroll_id')
		hits = response.get('hits')['hits']
		# Yield results in batches
		while hits:
			yield hits
			try:
				# Fetch the next batch of results using the scroll API
				response = self.client.scroll(scroll_id=scroll_id, scroll=scroll)
			except Exception as e:
				# Raise a custom error if scrolling fails
				raise ElasticSearchError(f"Failed to scroll Elasticsearch data: {str(e)}")
			# Update scroll ID and hits for the next iteration
			scroll_id = response.get('_scroll_id')
			hits = response.get('hits')['hits']
