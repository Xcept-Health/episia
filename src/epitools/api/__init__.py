"""
epitools.api - Public API layer for EpiTools.

Modules
-------
    unified    : EpiToolsAPI singleton (epi entry point)
    reporting  : EpiReport builder + report_from_model / report_from_result
    results    : Unified result classes (EpiResult, ModelResult, ROCResult…)
"""

from .reporting import EpiReport, report_from_result, report_from_model
from .results   import (
    EpiResult,
    ConfidenceInterval,
    AssociationResult,
    ProportionResult,
    SampleSizeResult,
    DiagnosticResult,
    ROCResult,
    StratifiedResult,
    ModelResult,
    TimeSeriesResult,
    RegressionResult,
    make_ci,
    make_association,
    make_proportion,
)
from .unified import epi, EpiToolsAPI

__all__ = [
    # Reporting
    "EpiReport",
    "report_from_result",
    "report_from_model",
    # Results
    "EpiResult",
    "ConfidenceInterval",
    "AssociationResult",
    "ProportionResult",
    "SampleSizeResult",
    "DiagnosticResult",
    "ROCResult",
    "StratifiedResult",
    "ModelResult",
    "TimeSeriesResult",
    "RegressionResult",
    "make_ci",
    "make_association",
    "make_proportion",
    # Entry point
    "epi",
    "EpiToolsAPI",
]