"""
Episia - Epidemiology Toolbox for Python
Based on OpenEpi algorithms, extended for the African public health context.

Quick start::

    from episia import epi

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
    report.save_html("report.html")

Advanced usage (direct imports)::

    # Models
    from episia.models import SIRModel, SEIRModel, SEIRDModel
    from episia.models import SensitivityAnalysis, ModelCalibrator

    # Stats
    from episia.stats import risk_ratio, odds_ratio, diagnostic_test_2x2
    from episia.stats import roc_analysis, sample_size_risk_ratio

    # Reporting
    from episia import EpiReport
    report = EpiReport(title="My report", author="Dr. Ouedraogo")
    report.add_metrics({"R0": 3.2, "Peak": "42,500"})
    report.save_html("report.html")

    # Visualization
    from episia.viz import plot_epicurve, plot_roc, plot_forest, set_theme
    set_theme("dark")

    # Surveillance data
    from episia.data import SurveillanceDataset, AlertEngine
"""

__version__      = "0.1.0a1"
__author__       = "Fidlouindé Ariel Shadrac Ouedraogo"
__email__        = "arielshadrac@gmail.com"
__organization__ = "Xcept-Health"
__license__      = "MIT"

#  Plotly renderer — auto-configure browser for script environments 
# Prevents raw JSON from being dumped in the terminal when calling fig.show()
# in a non-notebook context (PowerShell, CMD, terminal).
# In Jupyter, the renderer is left as-is so inline display works normally.
try:
    import plotly.io as _pio
    _in_notebook = False
    try:
        from IPython import get_ipython as _get_ipython
        _in_notebook = _get_ipython() is not None
    except ImportError:
        pass
    if not _in_notebook:
        _pio.renderers.default = "browser"
    del _pio, _in_notebook
except ImportError:
    pass

#  Main entry point 
from .api.unified  import epi, EpisiaAPI

#  Reporting — available directly from episia 
from .api.reporting import EpiReport, report_from_result, report_from_model

#  Models 

#  Stats 


#  Surveillance 
from .data.surveillance import SurveillanceDataset, AlertEngine


#  Lazy imports (PEP 562) 
# Heavy modules (scipy, sklearn, plotly, matplotlib) are NOT loaded at startup.
# They load on first use — `from episia import risk_ratio` triggers the load,
# but `from episia import epi` (the common case) stays fast.

_LAZY = {
    # stats
    "risk_ratio": ".stats.contingency",
    "odds_ratio":  ".stats.contingency",
    "proportion_ci": ".stats.descriptive",
    "mean_ci":     ".stats.descriptive",
    "diagnostic_test_2x2": ".stats.diagnostic",
    "roc_analysis": ".stats.diagnostic",
    "sample_size_risk_ratio": ".stats.samplesize",
    "sample_size_single_proportion": ".stats.samplesize",
    # viz
    "set_theme": ".viz.themes.registry",
    "get_available_themes": ".viz.themes.registry",
    "plot_epicurve": ".viz.curves",
    "plot_roc": ".viz.roc",
    "plot_forest": ".viz.forest",
}

def __getattr__(name: str):
    if name in _LAZY:
        import importlib
        module = importlib.import_module(_LAZY[name], package=__name__)
        obj = getattr(module, name)
        # Cache in module globals so next access is O(1)
        globals()[name] = obj
        return obj
    raise AttributeError(f"module 'episia' has no attribute {name!r}")


__all__ = [
    # Entry point
    "epi", "EpisiaAPI",
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