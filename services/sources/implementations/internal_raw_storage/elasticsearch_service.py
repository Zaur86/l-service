from dataclasses import dataclass, field
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from services.sources.base import InternalRawStorageService
from models.queries import ElasticQueryModel
from app.errors.external_errors import ElasticSearchError
import boto3
import logging


@dataclass
class ElasticSearchService(InternalRawStorageService):
    """
    Elasticsearch implementation for internal raw data storage.
    Provides methods for retrieving data in batches using the scroll API.
    """
    host: str
    port: int
    use_iam: bool = False
    aws_profile: str = None
    aws_region: str = None
    aws_service: str = 'es'
    client: Elasticsearch = field(init=False)
    index: str = field(init=False, default=None)
    query: dict = field(init=False, default=None)

    def __post_init__(self):
        """
        Initializes the Elasticsearch client with or without AWS IAM authentication.
        """
        if self.use_iam:
            # Set up AWS session and retrieve credentials
            session = boto3.Session(profile_name=self.aws_profile, region_name=self.aws_region)
            credentials = session.get_credentials()
            # Create AWS4Auth object for secure HTTP requests
            awsauth = AWS4Auth(
                credentials.access_key,
                credentials.secret_key,
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

    def prepare_extraction(self, index: str, query_model: ElasticQueryModel):
        """
         Prepares an Elasticsearch index and query based on the provided query model/

         :param index: The name of the Elasticsearch index where the query will be executed.
         :param query_model: Instance of ElasticQueryModel containing query parameters.
         """
        self.index = index
        self.query = query_model.build_query()

    def extract_data(self, batch_size: int, scroll: str):
        """
        Extracts data from Elasticsearch in batches using the scroll API.

        :param batch_size: Number of documents to fetch per batch.
        :param scroll: Duration for keeping the search context alive.
        :return: Generator yielding batches of documents.
        """
        logging.info(f"Extracting data from index '{self.index}' with batch size {batch_size}")
        try:
            # Perform initial search query
            response = self.client.search(index=self.index, body=self.query, scroll=scroll, size=batch_size)
        except Exception as e:
            raise ElasticSearchError(f"Failed to scroll Elasticsearch data: {str(e)}")

        # Retrieve scroll ID and initial batch of hits
        scroll_id = response.get('_scroll_id')
        hits = response.get('hits', {}).get('hits', [])

        # Yield results in batches
        while hits:
            yield hits
            try:
                # Fetch the next batch of results using the scroll API
                response = self.client.scroll(scroll_id=scroll_id, scroll=scroll)
            except Exception as e:
                raise ElasticSearchError(f"Failed to scroll Elasticsearch data: {str(e)}")
            # Update scroll ID and hits for the next iteration
            scroll_id = response.get('_scroll_id')
            hits = response.get('hits', {}).get('hits', [])
