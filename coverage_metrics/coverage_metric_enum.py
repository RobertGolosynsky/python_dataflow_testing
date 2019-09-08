from enum import Enum


class CoverageMetric(Enum):
    STATEMENT = 1
    BRANCH = 2

    M_ONLY = 3
    IM_ONLY = 4
    IC_ONLY = 5

    M_AND_IM = 6
    M_AND_IC = 7
    IM_AND_IC = 8

    ALL_PAIRS = 9