"""
episia.compatibility
--------------------
Tools for cross-system interoperability and coding robustness analysis.

Submodules
----------
coding
    CodingComparator  - quantify the impact of coding differences on
                        epidemiological measures (ICD-10 vs ICD-11, etc.)
comorbidity
    ComorbidityScorer     - compute Charlson / Elixhauser scores for a dataset
    ComorbidityComparator - compare scores between two coding versions
"""

from .coding import CodingComparator, ComparisonMode
from .results import CodingRobustnessResult, MeasureDelta
from .comorbidity import (
    ComorbidityScorer,
    ComorbidityComparator,
    ComorbidityScoreResult,
    ComorbidityComparisonResult,
)

__all__ = [
    # coding
    "CodingComparator",
    "ComparisonMode",
    "CodingRobustnessResult",
    "MeasureDelta",
    # comorbidity
    "ComorbidityScorer",
    "ComorbidityComparator",
    "ComorbidityScoreResult",
    "ComorbidityComparisonResult",
]