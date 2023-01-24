import requests
import logging

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from google.cloud.storage.client import Client as StorageClient
from google.cloud import functions_v1
from google.auth.transport.requests import Request as AuthRequest
from google.oauth2.id_token import fetch_id_token


class GcpService:
    def __init__(self, cloud_function_name):
        self.cloud_function = self.__get_cloud_function(cloud_function_name)
        credentials = GoogleCredentials.get_application_default()
        self.iam_service = discovery.build("iam", "v1", credentials=credentials)

    @staticmethod
    def __get_cloud_function(cloud_function_name):
        cloud_function_client = functions_v1.CloudFunctionsServiceClient()
        return cloud_function_client.get_function(name=cloud_function_name)

    def get_service_account(self):
        project = self.cloud_function.project_id
        service_account_email = self.cloud_function.service_account_email

        service_account_name = (
            f"projects/{project}/serviceAccounts/{service_account_email}"
        )

        return (
            self.iam_service.projects()
            .serviceAccounts()
            .get(name=service_account_name)
            .execute()
        )

    @staticmethod
    def create_bucket_if_it_doesnt_exist(bucket_name):
        storage_client = StorageClient()
        bucket = storage_client.bucket(bucket_name)
        if not bucket.exists():
            storage_client.create_bucket(bucket)

    def query_testable_permissions(self, next_page_token=None):
        project = self.cloud_function.project_id
        request_body = {
            "fullResourceName": f"//cloudresourcemanager.googleapis.com/projects/{project}",
            "pageSize": 1000,
        }

        if next_page_token:
            request_body["pageToken"] = next_page_token

        request = self.iam_service.permissions().queryTestablePermissions(
            body=request_body
        )
        return request.execute()

    def does_cloud_function_return_ok(self):
        function_url = self.cloud_function.https_trigger.url

        auth_token = fetch_id_token(AuthRequest(), function_url)
        auth_header = {"Authorization": f"Bearer {auth_token}"}

        response = requests.get(url=function_url, headers=auth_header)
        logging.info(f"GCP Function Response: {response.status_code} - {response.text}")

        return response.ok
