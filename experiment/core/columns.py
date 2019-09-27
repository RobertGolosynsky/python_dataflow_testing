from enum import Enum


class DataFrameType(Enum):
    FIXED_SIZE = "FIXED_SIZE"
    FIXED_COVERAGE = "FIXED_COVERAGE"


METRIC = "Metric"
SUITE_SIZE = "Suite size"
SUITE_COVERAGE = "Coverage"
SUITE_COVERAGE_BIN = "Coverage bins (%)"
MUTATION_SCORE = "Mutants killed (%)"
BUG_REVEALED_SCORE = "Bugs revealed (%)"
