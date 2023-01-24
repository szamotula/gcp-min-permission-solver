import time
import logging
from functools import cache


class PermissionTester:
    def __init__(self, gcp_service, terraform_service, wait_time=120):
        self.gcp_service = gcp_service
        self.terraform_service = terraform_service
        self.wait_time = wait_time

    def get_testable_permissions(self):
        page_token = None
        permissions = []

        while True:
            response = self.gcp_service.query_testable_permissions(page_token)

            permissions.extend(
                p["name"]
                for p in response["permissions"]
                if p.get("customRolesSupportLevel") != "NOT_SUPPORTED"
            )

            if "nextPageToken" not in response:
                break
            page_token = response["nextPageToken"]

        return tuple(permissions)

    @cache
    def does_function_pass_with_permissions(self, permissions):
        logging.info(f"Updating role with new list of {len(permissions)} permissions")
        self.terraform_service.update_permissions_in_service_account(permissions)
        logging.info(f"Waiting {self.wait_time}s for permissions to update in GCP")
        time.sleep(self.wait_time)
        result = self.gcp_service.does_cloud_function_return_ok()

        try:
            self.__clean_up()
        except Exception as e:
            logging.debug(f"Failed to clean up after function: {e}")

        return result

    def __clean_up(self):
        """
        If your cloud function requires cleanup after it's run, implement it here.
        """
        pass
