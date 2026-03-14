"""
EpiTools - Epidemiology Toolbox for Python
Based on OpenEpi algorithms, extended for the African public health context.

Quick start::

    from epitools import epi

    # SEIR model
    model  = epi.seir(N=1_000_000, I0=10, E0=50, beta=0.35,
                      sigma=1/5.2, gamma=1/14)
    result = model.run()
    result.plot().show()

    # Biostatistics
    rr = epi.risk_ratio(a=40, b=10, c=20, d=30)
    print(rr)

    # Report
    report = epi.report(result, title="SEIR — Burkina Faso 2024")
    report.save_html("rapport.html")

Advanced usage (direct imports)::

    # Models
    from epitools.models import SIRModel, SEIRModel, SEIRDModel
    from epitools.models import SensitivityAnalysis, ModelCalibrator

    # Stats
    from epitools.stats import risk_ratio, odds_ratio, diagnostic_test_2x2
    from epitools.stats import roc_analysis, sample_size_risk_ratio

    # Reporting
    from epitools import EpiReport
    report = EpiReport(title="My report", author="Dr. Ouedraogo")
    report.add_metrics({"R0": 3.2, "Peak": "42,500"})
    report.save_html("report.html")

    # Visualization
    from epitools.viz import plot_epicurve, plot_roc, plot_forest, set_theme
    set_theme("dark")

    # Surveillance data
    from epitools.data import SurveillanceDataset, AlertEngine
"""

__version__      = "0.1.0"
__author__       = "Ariel Shadrac Ouedraogo"
__email__        = "arielshadrac@gmail.com"
__organization__ = "Xcept-Health"
__license__      = "MIT"

# ── Main entry point ──────────────────────────────────────────────────────────
from .api.unified  import epi, EpiToolsAPI

# ── Reporting — available directly from epitools ──────────────────────────────
from .api.reporting import EpiReport, report_from_result, report_from_model

# ── Models ────────────────────────────────────────────────────────────────────
from .models import (
    SIRModel, SEIRModel, SEIRDModel,
    SIRParameters, SEIRParameters, SEIRDParameters,
    SensitivityAnalysis, ModelCalibrator,
    ScenarioRunner, ScenarioSet,
)

# ── Stats ─────────────────────────────────────────────────────────────────────
from .stats.contingency  import risk_ratio, odds_ratio
from .stats.descriptive  import proportion_ci, mean_ci
from .stats.diagnostic   import diagnostic_test_2x2, roc_analysis
from .stats.samplesize   import sample_size_risk_ratio, sample_size_single_proportion

# ── Visualization ─────────────────────────────────────────────────────────────
from .viz import (
    set_theme, get_available_themes,
    plot_epicurve, plot_roc, plot_forest,
    plot_incidence, plot_doubling,
)

# ── Surveillance ──────────────────────────────────────────────────────────────
from .data.surveillance import SurveillanceDataset, AlertEngine

__all__ = [
    # Entry point
    "epi", "EpiToolsAPI",
    # Reporting
    "EpiReport", "report_from_result", "report_from_model",
    # Models
    "SIRModel", "SEIRModel", "SEIRDModel",
    "SIRParameters", "SEIRParameters", "SEIRDParameters",
    "SensitivityAnalysis", "ModelCalibrator",
    "ScenarioRunner", "ScenarioSet",
    # Stats
    "risk_ratio", "odds_ratio", "proportion_ci", "mean_ci",
    "diagnostic_test_2x2", "roc_analysis",
    "sample_size_risk_ratio", "sample_size_single_proportion",
    # Viz
    "set_theme", "get_available_themes",
    "plot_epicurve", "plot_roc", "plot_forest",
    "plot_incidence", "plot_doubling",
    # Data
    "SurveillanceDataset", "AlertEngine",
    # Meta
    "__version__",
]