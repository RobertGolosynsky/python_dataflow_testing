import operator
import random

from typing import List

from coverage_metrics.util import percent


class SubTestSuite:
    def __init__(self, test_cases, coverage, covered_items, all_coverage_items=None):
        if not isinstance(test_cases, tuple):
            test_cases = tuple(test_cases)
        self.test_cases = test_cases

        self.coverage = coverage

        if not isinstance(covered_items, frozenset):
            covered_items = frozenset(covered_items)
        self.covered_items = covered_items

        self.all_coverage_items = all_coverage_items

    def __hash__(self):
        return hash(self.test_cases) + hash(self.coverage) + hash(self.covered_items)

    def __eq__(self, other):
        return self.test_cases == other.test_cases \
               and self.coverage == other.coverage \
               and self.covered_items == other.covered_items


def generate_test_suites_fixed_size(data,
                                    n,
                                    total_coverage_items: set,
                                    exact_size,
                                    check_unique_items_covered=True,
                                    consecutive_failures_allowed=20
                                    ) -> List[SubTestSuite]:
    suites = set()
    suites_cases = set()
    covered_item_sets = set()
    failure_count = 0
    while len(suites) < n:
        if failure_count > consecutive_failures_allowed:
            break
        suite = generate_suite_of_fixed_size(data, exact_size)
        covered_items = set()
        for node_id in suite:
            covered_items.update(data[node_id])
        covered_items = frozenset(covered_items)
        if check_unique_items_covered:
            covers_unique_items = covered_items not in covered_item_sets
            should_check_further = covers_unique_items
            # print("covers_unique_items", covers_unique_items)
        else:
            should_check_further = True
        # if frozenset(suite) in suites_cases:
        # print("Duplicate test suite")
        if should_check_further:
            coverage = percent(covered_items, total_coverage_items)
            ts = SubTestSuite(suite, coverage, covered_items)
            if ts not in suites:
                failure_count = 0
                suites.add(ts)
                covered_item_sets.add(covered_items)
                suites_cases.add(frozenset(suite))
            else:
                failure_count += 1
            # else:
            #     print("Created a duplicate test suite")
        else:
            failure_count += 1
    suites = list(sorted(suites, key=operator.attrgetter("coverage"), reverse=True))
    return suites


def generate_test_suites_fixed_coverage(data,
                                        n,
                                        total_coverage_items: set,
                                        coverage_boundary,
                                        check_unique_items_covered=True,
                                        consecutive_failures_allowed=20
                                        ) -> List[SubTestSuite]:
    suites = set()
    suites_cases = set()
    covered_item_sets = set()
    total_coverage_items_count = len(total_coverage_items)
    failure_count = 0
    while len(suites) < n:
        if failure_count > consecutive_failures_allowed:
            break
        suite = generate_suite_of_fixed_coverage(data, total_coverage_items_count, coverage_boundary)
        if suite is None:
            # can't have a test suite of this coverage boundary
            break
        covered_items = set()
        for node_id in suite:
            covered_items.update(data[node_id])
        covered_items = frozenset(covered_items)
        if check_unique_items_covered:
            covers_unique_items = covered_items not in covered_item_sets
            should_check_further = covers_unique_items
            # print("covers_unique_items", covers_unique_items)
        else:
            should_check_further = True
        # if frozenset(suite) in suites_cases:
        # print("Duplicate test suite")
        if should_check_further:
            coverage = percent(covered_items, total_coverage_items)
            ts = SubTestSuite(suite, coverage, covered_items, total_coverage_items)
            if ts not in suites:
                failure_count = 0
                suites.add(ts)
                covered_item_sets.add(covered_items)
                suites_cases.add(frozenset(suite))
            else:
                failure_count += 1
            # else:
            #     print("Created a duplicate test suite")
        else:
            failure_count += 1
    suites = list(sorted(suites, key=operator.attrgetter("coverage"), reverse=True))
    return suites


def random_suites(node_ids, exact_size, n, give_up_after=200):
    suites = set()
    failed = 0
    while len(suites) < n:
        sample = frozenset(random.sample(node_ids, exact_size))
        if sample not in suites:
            suites.add(sample)
        else:
            failed += 1
            if failed > give_up_after:
                break

    return [SubTestSuite(node_ids, 0, frozenset()) for node_ids in suites]


def generate_suite_of_fixed_size(node_ids_coverage_items: dict, exact_size):
    node_ids = list(node_ids_coverage_items.keys())
    if exact_size > len(node_ids):
        return []

    initial_node = random.choice(node_ids)
    suite = {initial_node}

    covered_items = set()
    covered_items.update(node_ids_coverage_items[initial_node])
    for _ in range(exact_size - 1):
        node_id = pick_next_node(node_ids_coverage_items, suite, covered_items)
        suite.add(node_id)
        node_coverage = node_ids_coverage_items[node_id]
        # prev_covered = len(covered_items)
        covered_items.update(node_coverage)
        # if prev_covered == len(covered_items):
        #     print("Suite of size {} has max coverage possible".format(len(suite)))
    return suite


def generate_suite_of_fixed_coverage(node_ids_coverage_items: dict, total_items, coverage):
    node_ids = list(node_ids_coverage_items.keys())

    initial_node = random.choice(node_ids)
    suite = {initial_node}

    covered_items = set()
    covered_items.update(node_ids_coverage_items[initial_node])
    while len(covered_items) / total_items < coverage:
        if len(suite) == len(node_ids):
            return None
        node_id = pick_next_node(node_ids_coverage_items, suite, covered_items)
        suite.add(node_id)
        node_coverage = node_ids_coverage_items[node_id]
        covered_items.update(node_coverage)
    return suite


def pick_next_node(node_ids_coverage_items: dict,
                   filter_out_node_ids: set,
                   covered_items: set):
    filtered_ids = {node_id: cov_items_set for node_id, cov_items_set in node_ids_coverage_items.items()
                    if node_id not in filter_out_node_ids}
    node_ids_maximising = [node_id for node_id, cov_items_set in filtered_ids.items()
                           if len(cov_items_set - covered_items) > 0]
    if node_ids_maximising:
        # print("Adding case that increases coverage")
        return random.choice(node_ids_maximising)
    else:
        # print("Coverage maximised, adding random case")
        return random.choice(list(filtered_ids.keys()))
