import json
import os
import time
import logging
from functools import cache

from python_terraform import Terraform
from google.auth.transport.requests import Request as AuthRequest
from google.oauth2.id_token import fetch_id_token
from google.cloud import functions_v1
from google.cloud import pubsub_v1
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from google.cloud.storage.client import Client as StorageClient

import requests


class PermissionTester:
    def __init__(self, cloud_function_name):
        credentials = GoogleCredentials.get_application_default()
        self.iam_service = discovery.build("iam", "v1", credentials=credentials)

        self.cloud_function = self.__get_cloud_function(cloud_function_name)
        self.project = self.cloud_function.name.split("/")[1]
        self.service_account = self.__get_service_account(
            self.cloud_function.service_account_email
        )

        self.__write_variable_file()

        self.__create_bucket_if_it_doesnt_exist("min-permission-solver-terraform-state")
        self.terraform = self.__initialize_terraform()
        self.__import_service_account_if_it_isnt_imported()

        self.subscriber_client = pubsub_v1.SubscriberClient()
        self.subscription_name = self.subscriber_client.subscription_path(
            "doit-ipt-apis-dev-e2e0",
            "person-api-webhook-5a5e7a18-cd48-44e5-b241-d84b97484fda",
        )

    @staticmethod
    def __get_cloud_function(cloud_function_name):
        client = functions_v1.CloudFunctionsServiceClient()
        return client.get_function(name=cloud_function_name)

    def __get_service_account(self, service_account_email):
        service_account_name = (
            f"projects/{self.project}/serviceAccounts/{service_account_email}"
        )

        return (
            self.iam_service.projects()
            .serviceAccounts()
            .get(name=service_account_name)
            .execute()
        )

    @staticmethod
    def __create_bucket_if_it_doesnt_exist(bucket_name):
        storage_client = StorageClient()
        bucket = storage_client.bucket(bucket_name)
        if not bucket.exists():
            storage_client.create_bucket(bucket)

    @staticmethod
    def __initialize_terraform():
        terraform_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../terraform")
        )
        terraform = Terraform(working_dir=terraform_dir)
        return_code, stdout, stderr = terraform.init()

        if return_code != 0:
            raise Exception(f"Failed to initialize terraform: {stderr}")

        return terraform

    def __write_variable_file(self):
        variables = {
            "project": self.project,
            "service_account_id": self.service_account["email"].split("@")[0],
        }
        variables_file = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../terraform/variables.json")
        )
        with open(variables_file, "w") as outfile:
            json.dump(variables, outfile)

    def __import_service_account_if_it_isnt_imported(self):
        return_code, stdout, stderr = self.terraform.cmd(
            "state show", "google_service_account.this"
        )

        if return_code == 0:
            return

        return_code, stdout, stderr = self.terraform.import_cmd(
            "google_service_account.this",
            self.service_account["name"],
        )

        if return_code != 0:
            raise Exception(f"Failed to import service account: {stderr}")

    def get_testable_permissions(self):
        query_testable_permissions_request_body = {
            "fullResourceName": f"//cloudresourcemanager.googleapis.com/projects/{self.project}",
            "pageSize": 1000,
        }

        permissions = []

        while True:
            request = self.iam_service.permissions().queryTestablePermissions(
                body=query_testable_permissions_request_body
            )
            response = request.execute()

            permissions.extend(
                p["name"]
                for p in response["permissions"]
                if p.get("customRolesSupportLevel") != "NOT_SUPPORTED"
            )

            if "nextPageToken" not in response:
                break
            query_testable_permissions_request_body["pageToken"] = response[
                "nextPageToken"
            ]

        return tuple(permissions)

    @cache
    def does_function_pass_with_permissions(self, permissions):
        logging.info(f"Updating role with new list of {len(permissions)} permissions")
        self.__update_permissions_in_service_account(permissions)
        logging.info("Waiting two minutes for permissions to update in GCP")
        time.sleep(120)
        result = self.__does_cloud_function_return_ok()

        try:
            self.__clean_up()
        except Exception as e:
            logging.debug(f"Failed to clean up subscription: {e}")

        return result

    def __update_permissions_in_service_account(self, permissions):
        permissions_json = {
            "permission_lists": list(self.__divide_into_sized_chunks(permissions, 1000))
        }
        permissions_file = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../terraform/permissions.json")
        )
        with open(permissions_file, "w") as outfile:
            json.dump(permissions_json, outfile)

        return_code, stdout, stderr = self.terraform.apply(skip_plan=True)

        if return_code != 0:
            raise Exception(f"Failed to update permissions: {stderr}")

    @staticmethod
    def __divide_into_sized_chunks(full_list, size):
        for i in range(0, len(full_list), size):
            yield full_list[i : i + size]

    def __does_cloud_function_return_ok(self):
        function_url = self.cloud_function.https_trigger.url

        auth_token = fetch_id_token(AuthRequest(), function_url)
        auth_header = {"Authorization": f"Bearer {auth_token}"}

        response = requests.get(url=function_url, headers=auth_header)
        logging.info(f"GCP Function Response: {response.status_code} - {response.text}")

        return response.ok

    def __clean_up(self):
        """
        If your cloud function requires cleanup after it's run, and you don't want to
        or can't do the cleanup within the cloud function, implement it here.
        """
        pass
