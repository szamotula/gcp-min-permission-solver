import argparse
import logging
import sys

from gcp_service import GcpService
from src.minimum_finder import MinimumFinder
from src.permission_tester import PermissionTester
from terraform_service import TerraformService


def main(argv):
    parser = argparse.ArgumentParser(
        description="Finds the minimum set of permissions needed to run given GCP cloud function."
    )
    parser.add_argument(
        "function_name",
        help="Full name of GCP cloud function of form projects/<project>/locations/<location>/functions/<function>",
    )
    parser.add_argument(
        "-l",
        "--log_level",
        required=False,
        default="WARNING",
        help="Logging level. Default is WARNING.  Set to INFO to see detailed run information.",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=args.log_level)

    gcp_service = GcpService(args.function_name)
    terraform_service = TerraformService(gcp_service)
    permission_tester = PermissionTester(gcp_service, terraform_service)
    minimum_finder = MinimumFinder(
        permission_tester.does_function_pass_with_permissions
    )

    all_testable_permissions = permission_tester.get_testable_permissions()

    if not permission_tester.does_function_pass_with_permissions(
        all_testable_permissions
    ):
        logging.error("Function does not work with all testable permissions.")
        return

    minimum_permissions = minimum_finder.find_smallest_permission_set(
        all_testable_permissions
    )
    print(f"Minimal set of permissions: {minimum_permissions}")


if __name__ == "__main__":
    main(sys.argv[1:])
