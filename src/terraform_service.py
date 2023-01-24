import json
import os

from python_terraform import Terraform


class TerraformService:
    def __init__(self, gcp_service):
        gcp_service.__create_bucket_if_it_doesnt_exist(
            "min-permission-solver-terraform-state"
        )
        service_account = gcp_service.get_service_account()
        self.__write_variable_file(service_account)
        self.terraform = self.__initialize_terraform()
        self.__import_service_account_if_it_isnt_imported(service_account)

    @staticmethod
    def __write_variable_file(service_account):
        variables = {
            "project": service_account["projectId"],
            "service_account_id": service_account["email"].split("@")[0],
        }
        variables_file = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../terraform/variables.json")
        )
        with open(variables_file, "w") as outfile:
            json.dump(variables, outfile)

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

    def __import_service_account_if_it_isnt_imported(self, service_account):
        return_code, stdout, stderr = self.terraform.cmd(
            "state show", "google_service_account.this"
        )

        if return_code == 0:
            return

        return_code, stdout, stderr = self.terraform.import_cmd(
            "google_service_account.this",
            service_account["name"],
        )

        if return_code != 0:
            raise Exception(f"Failed to import service account: {stderr}")

    def update_permissions_in_service_account(self, permissions):
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
