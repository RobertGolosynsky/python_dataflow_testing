import operator
import random

from typing import List

from loguru import logger

from coverage_metrics.util import percent
from experiment.suites.collect_test_suite import SubTestSuite
import itertools


class AugmentedSubTestSuite(SubTestSuite):
    def __init__(self, test_cases, coverage, covered_items, all_coverage_items=None):
        super().__init__(test_cases, coverage, covered_items, all_coverage_items=all_coverage_items)
        self.extra_test_cases = set()
        self.augmenting_coverage = 0

    def add_augmenting_test_case(self, node_id):
        self.extra_test_cases.add(node_id)

    def set_augmenting_coverage(self, value):
        self.augmenting_coverage = value

    def __hash__(self):
        if len(self.extra_test_cases) > 0:
            return hash(self.test_cases) + hash(self.extra_test_cases)
        else:
            return super().__hash__()

    def __eq__(self, other):
        if len(self.extra_test_cases) > 0:
            return super.__eq__(self, o=other) \
                   and frozenset(self.extra_test_cases) == frozenset(other.extra_test_cases)
        else:
            return super.__eq__(self, o=other)


def generate_max_coverage_test_suites(data,
                                      n,
                                      total_coverage_items: set,
                                      consecutive_failures_allowed=100
                                      ) -> List[AugmentedSubTestSuite]:
    total_coverage_items_count = len(total_coverage_items)
    if total_coverage_items_count == 0:
        return []
    suites = set()
    failure_count = 0
    while len(suites) < n:
        if failure_count > consecutive_failures_allowed:
            break
        suite = generate_suite_of_max_coverage(data)
        if suite is None:
            # can't have a test suite of this coverage boundary
            failure_count += 1
            continue
        covered_items = set()
        for node_id in suite:
            covered_items.update(data[node_id])
        covered_items = frozenset(covered_items)

        coverage = percent(covered_items, total_coverage_items)
        ts = AugmentedSubTestSuite(suite, coverage, covered_items, total_coverage_items)
        if ts not in suites:
            failure_count = 0
            suites.add(ts)
        else:
            failure_count += 1
    suites = list(sorted(suites, key=operator.attrgetter("coverage"), reverse=True))
    return suites


def add_test_cases_increasing_coverage(suites: List[AugmentedSubTestSuite], data, total_items):
    augmented_suites = set()
    for suite in suites:
        next_node = augment_test_suite(suite, data)

        suite.add_augmenting_test_case(next_node)
        covered_augmenting_items = [data[node_id] for node_id in
                                    itertools.chain([suite.extra_test_cases, suite.test_cases])]
        suite.set_augmenting_coverage(percent(covered_augmenting_items, total_items))
        augmented_suites.add(suite)
    return augmented_suites


def augment_test_suite(suite: AugmentedSubTestSuite, data):
    covered_items = {item for node_id in suite.test_cases for item in data[node_id]}
    next_node = pick_next_node(data, suite.test_cases, covered_items)
    if not next_node:
        return None
    else:
        return next_node


def generate_suite_of_max_coverage(node_ids_coverage_items: dict):
    node_ids = list(node_ids_coverage_items.keys())

    initial_node = random.choice(node_ids)
    suite = {initial_node}

    covered_items = set()
    covered_items.update(node_ids_coverage_items[initial_node])

    while True:
        node_id = pick_next_node(node_ids_coverage_items, suite, covered_items)
        if node_id is None:
            return suite

        node_coverage = node_ids_coverage_items[node_id]
        covered_items = covered_items | node_coverage
        suite.add(node_id)

        if len(suite) == len(node_ids):
            logger.warning("Used up all test cases")
            return None


def pick_next_node(node_ids_coverage_items: dict,
                   filter_out_node_ids: set,
                   covered_items: set):
    filtered_ids = {node_id: cov_items_set for node_id, cov_items_set in node_ids_coverage_items.items()
                    if node_id not in filter_out_node_ids}
    node_ids_maximising = [node_id for node_id, cov_items_set in filtered_ids.items()
                           if len(cov_items_set - covered_items) > 0]
    if node_ids_maximising:
        return random.choice(node_ids_maximising)
    else:
        return None
