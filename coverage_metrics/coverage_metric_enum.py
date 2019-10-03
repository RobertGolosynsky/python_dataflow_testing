from enum import Enum



class CoverageMetric(Enum):
    STATEMENT = "Statement"
    BRANCH = "Branch"

    M_ONLY = "Only intramethod"
    IC_ONLY = "Only interclass"
    IM_ONLY = "Only intermethod"

    M_AND_IM = "Intramethod and interclass"
    M_AND_IC = "Intramethod and intermethod"
    IM_AND_IC = "Intermethod and interclass"

    ALL_PAIRS = "All pairs"

    ALL_C_USES = "All computational uses"
    ALL_P_USES = "All predicate uses"

    def __str__(self):
        return self._value_

    def __repr__(self):
        return self._value_

#
# METRIC_NAMES = {
#     CoverageMetric.STATEMENT: "Statement",
#     CoverageMetric.BRANCH: "Branch",
#     CoverageMetric.M_ONLY: "Only intramethod",
#     CoverageMetric.IC_ONLY: "Only interclass",
#     CoverageMetric.IM_ONLY: "Only intermethod",
#     CoverageMetric.M_AND_IC: "Intramethod and interclass",
#     CoverageMetric.M_AND_IM: "Intramethod and intermethod",
#     CoverageMetric.IM_AND_IC: "Intermethod and interclass",
#     CoverageMetric.ALL_PAIRS: "All pairs",
# }
