import unittest
from unittest.mock import MagicMock


from gcp_service import GcpService
from permission_tester import PermissionTester
from terraform_service import TerraformService


class TestPermissionTester(unittest.TestCase):
    def setUp(self) -> None:
        self.gcp_service_mock = MagicMock(GcpService)
        self.terraform_service_mock = MagicMock(TerraformService)
        self.permission_tester = PermissionTester(
            self.gcp_service_mock,
            self.terraform_service_mock,
            1,
        )

    def test_get_testable_permissions(self):
        self.gcp_service_mock.query_testable_permissions = MagicMock(
            side_effect=[
                {
                    "permissions": [
                        {"name": "permission1", "customRolesSupportLevel": "SUPPORTED"},
                        {"name": "permission2"},
                    ],
                    "nextPageToken": "token",
                },
                {
                    "permissions": [
                        {"name": "permission3", "customRolesSupportLevel": "SUPPORTED"},
                        {
                            "name": "permission4",
                            "customRolesSupportLevel": "NOT_SUPPORTED",
                        },
                    ]
                },
            ]
        )

        permissions = self.permission_tester.get_testable_permissions()
        self.assertEqual(("permission1", "permission2", "permission3"), permissions)

    def test_does_function_pass_with_permissions_passes(self):
        self.gcp_service_mock.does_cloud_function_return_ok = MagicMock(
            return_value=True
        )
        result = self.permission_tester.does_function_pass_with_permissions(
            ("a", "b", "c")
        )
        self.assertTrue(result)

    def test_does_function_pass_with_permissions_fails(self):
        self.gcp_service_mock.does_cloud_function_return_ok = MagicMock(
            return_value=False
        )
        result = self.permission_tester.does_function_pass_with_permissions(
            ("a", "b", "c")
        )
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
