from enum import Enum

# from coverage_metrics.coverage_metric_enum import CoverageMetric


class DataFrameType(Enum):
    FIXED_SIZE = "FIXED_SIZE"
    FIXED_COVERAGE = "FIXED_COVERAGE"


METRIC = "Metric"
SUITE_SIZE = "Suite size"
SUITE_COVERAGE = "Coverage"
SUITE_COVERAGE_BIN = "Coverage bins (%)"
MUTATION_SCORE = "Mutants\nkilled"
BUG_REVEALED_SCORE = "Bugs\nrevealed"
