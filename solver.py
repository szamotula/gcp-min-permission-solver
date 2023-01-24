import argparse
import logging
import sys

from src.minimum_finder import MinimumFinder
from src.permission_tester import PermissionTester


# Setup:
# GOOGLE_APPLICATION_CREDENTIALS environment variable must be set to the path of a service account key file
# Needs bucket, iam, and function permissions
# Pass in the name of the cloud function to test
# storage.buckets.create, or take name of TF bucket as input
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
        help="Logging level. Default is WARNING.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=args.log_level)

    permission_tester = PermissionTester(args.function_name)
    minimum_finder = MinimumFinder(permission_tester)

    minimum_permissions = minimum_finder.find_smallest_permission_set()
    print(f"Minimal set of permissions: {minimum_permissions}")


if __name__ == "__main__":
    main(sys.argv[1:])
