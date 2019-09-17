import contextlib
import os
import sys
import pytest


class CollectionPlugin:
    def __init__(self):
        self.collected_test_cases = set()

    def pytest_itemcollected(self, item):
        item_path = item.location[0]
        self.collected_test_cases.add(item_path)


def get_collected_cases(pytest_args):
    with open(os.devnull, 'w') as devnull:
        with contextlib.redirect_stdout(devnull):
            with contextlib.redirect_stderr(devnull):
                plugin = CollectionPlugin()
                exit_code = pytest.main(
                    pytest_args,
                    plugins=[plugin],
                )

                return exit_code, plugin.collected_test_cases


if __name__ == "__main__":
    exit_code, collected_nodes_paths = get_collected_cases(sys.argv[1:])
    print("\n".join(collected_nodes_paths))
    print()
    exit(exit_code)
