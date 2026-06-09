"""
episia.compatibility
--------------------
Tools for cross-system interoperability and coding robustness analysis.

Submodules
----------
coding
    CodingComparator  - quantify the impact of coding differences on
                        epidemiological measures (ICD-10 vs ICD-11, etc.)
"""

from .coding import CodingComparator
from .results import CodingRobustnessResult, MeasureDelta
from .comorbidity import ComorbidityScorer, ComorbidityComparator

__all__ = [
    "CodingComparator",
    "CodingRobustnessResult",
    "MeasureDelta",
]   