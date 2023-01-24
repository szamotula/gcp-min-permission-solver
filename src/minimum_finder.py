import logging


class MinimumFinder:
    def __init__(self, permission_tester):
        self.permission_tester = permission_tester

    def find_smallest_permission_set(self):
        passing_permissions = self.permission_tester.get_testable_permissions()
        number_of_splits = 2

        while True:
            logging.info(
                f"Testing {len(passing_permissions)} permissions with {number_of_splits} splits:"
            )
            logging.info(passing_permissions)

            if number_of_splits > len(passing_permissions):
                return passing_permissions

            permission_splits = list(
                self.__split_into_chunks(passing_permissions, number_of_splits)
            )

            for split_number in range(number_of_splits):

                permission_split = permission_splits[split_number]
                if self.permission_tester.do_permissions_work(permission_split):
                    passing_permissions = permission_split
                    number_of_splits = 2
                    print(f"New reduced set of permissions: {passing_permissions}")
                    break

                permission_complement = self.__get_complement(
                    passing_permissions, permission_split
                )
                if self.permission_tester.do_permissions_work(permission_complement):
                    passing_permissions = permission_complement
                    number_of_splits = 2
                    print(f"New reduced set of permissions: {passing_permissions}")
                    break
            else:
                number_of_splits += 1

    @staticmethod
    def __split_into_chunks(permissions, chunk_count):
        start = 0
        for i in range(chunk_count):
            subset = permissions[
                start : start + (len(permissions) - start) // (chunk_count - i)
            ]
            start = start + len(subset)
            yield subset

    @staticmethod
    def __get_complement(full_permissions, partial_permissions):
        partial_permission_set = set(partial_permissions)

        complement_permissions = []
        for permission in full_permissions:
            if permission not in partial_permission_set:
                complement_permissions.append(permission)

        return tuple(complement_permissions)
