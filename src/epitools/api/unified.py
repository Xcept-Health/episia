"""
api/unified.py - Interface unifiée EpiTools (point d'entrée principal).

Usage::

    from epitools import epi

    # Stats
    result = epi.risk_ratio(a=40, b=10, c=20, d=30)
    result = epi.proportion_ci(k=45, n=200)
    result = epi.diagnostic(tp=80, fp=10, fn=20, tn=90)

    # Modélisation
    model  = epi.seir(N=1_000_000, I0=10, E0=50, beta=0.35,
                      sigma=1/5.2, gamma=1/14)
    result = model.run()
    result.plot().show()

    # Données
    ds = epi.read_csv("cases.csv", date_col="date", cases_col="cas")
    ds.epicurve().plot().show()

    # Rapport
    report = epi.report(result, title="SEIR  Burkina Faso 2024")
    report.save_html("rapport.html")

    # Thème
    epi.set_theme("dark")
"""

from __future__ import annotations

from typing import Any, Optional


class EpiToolsAPI:
    """
    Unified EpiTools API  single entry point for all functionality.

    Instantiated as the module-level `epi` singleton.
    """

    # ── Stats ─────────────────────────────────────────────────────────────

    @staticmethod
    def risk_ratio(*args, **kwargs):
        from ..stats.contingency import risk_ratio
        return risk_ratio(*args, **kwargs)

    @staticmethod
    def odds_ratio(*args, **kwargs):
        from ..stats.contingency import odds_ratio
        return odds_ratio(*args, **kwargs)

    @staticmethod
    def proportion_ci(*args, **kwargs):
        from ..stats.descriptive import proportion_ci
        return proportion_ci(*args, **kwargs)

    @staticmethod
    def mean_ci(*args, **kwargs):
        from ..stats.descriptive import mean_ci
        return mean_ci(*args, **kwargs)

    @staticmethod
    def sample_size(*args, **kwargs):
        from ..stats.samplesize import calculate_sample_size
        return calculate_sample_size(*args, **kwargs)

    @staticmethod
    def diagnostic(*args, **kwargs):
        from ..stats.diagnostic import diagnostic_test_2x2
        return diagnostic_test_2x2(*args, **kwargs)

    # ── Models ────────────────────────────────────────────────────────────

    @staticmethod
    def sir(N: int, I0: float, beta: float, gamma: float,
            t_end: float = 160, **kwargs):
        """Convenience factory for SIRModel."""
        from ..models.sir import SIRModel
        from ..models.parameters import SIRParameters
        p = SIRParameters(N=N, I0=I0, beta=beta, gamma=gamma,
                          t_span=(0, t_end), **kwargs)
        return SIRModel(p)

    @staticmethod
    def seir(N: int, I0: float, E0: float, beta: float,
             sigma: float, gamma: float, t_end: float = 365, **kwargs):
        """Convenience factory for SEIRModel."""
        from ..models.seir import SEIRModel
        from ..models.parameters import SEIRParameters
        p = SEIRParameters(N=N, I0=I0, E0=E0, beta=beta,
                           sigma=sigma, gamma=gamma,
                           t_span=(0, t_end), **kwargs)
        return SEIRModel(p)

    @staticmethod
    def seird(N: int, I0: float, E0: float, beta: float, sigma: float,
              gamma: float, mu: float, t_end: float = 365, **kwargs):
        """Convenience factory for SEIRDModel."""
        from ..models.seird import SEIRDModel
        from ..models.parameters import SEIRDParameters
        p = SEIRDParameters(N=N, I0=I0, E0=E0, beta=beta, sigma=sigma,
                            gamma=gamma, mu=mu,
                            t_span=(0, t_end), **kwargs)
        return SEIRDModel(p)

    # ── Data ──────────────────────────────────────────────────────────────

    @staticmethod
    def read_csv(path, **kwargs):
        from ..data.io import read_csv
        return read_csv(path, **kwargs)

    @staticmethod
    def surveillance_from_csv(path, **kwargs):
        from ..data.surveillance import SurveillanceDataset
        return SurveillanceDataset.from_csv(path, **kwargs)

    # ── Reporting ─────────────────────────────────────────────────────────

    @staticmethod
    def report(result: Any, title: Optional[str] = None, **kwargs):
        """Build a report from any EpiResult or ModelResult."""
        from .reporting import report_from_result, report_from_model
        from .results import ModelResult
        if isinstance(result, ModelResult):
            return report_from_model(result, title=title, **kwargs)
        return report_from_result(result, title=title, **kwargs)

    # ── Viz ───────────────────────────────────────────────────────────────

    @staticmethod
    def set_theme(theme: str) -> None:
        from ..viz.themes.registry import set_theme
        set_theme(theme)

    @staticmethod
    def get_available_themes():
        from ..viz.themes.registry import get_available_themes
        return get_available_themes()

    @staticmethod
    def plot_epicurve(*args, **kwargs):
        from ..viz.curves import plot_epicurve
        return plot_epicurve(*args, **kwargs)

    @staticmethod
    def plot_roc(*args, **kwargs):
        from ..viz.roc import plot_roc
        return plot_roc(*args, **kwargs)

    @staticmethod
    def plot_forest(*args, **kwargs):
        from ..viz.forest import plot_forest
        return plot_forest(*args, **kwargs)

    def __repr__(self) -> str:
        return (
            "EpiTools API  v0.1.0\n"
            "  epi.sir() / epi.seir() / epi.seird()\n"
            "  epi.risk_ratio() / epi.odds_ratio() / epi.proportion_ci()\n"
            "  epi.read_csv() / epi.report() / epi.set_theme()"
        )


# Singleton exporté
epi = EpiToolsAPI()

__all__ = ["EpiToolsAPI", "epi"]