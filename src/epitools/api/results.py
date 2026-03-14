"""
api/results.py - Unified rich result classes for EpiTools public API.

This module provides a consistent result interface across all EpiTools modules.
Every public function returns a subclass of EpiResult, ensuring:
    - Consistent .to_dict() / .to_json() / .to_dataframe() serialization
    - Rich __repr__ for notebooks and REPL
    - plot() method wired to the viz layer (Plotly by default)
    - Metadata (confidence level, method, warnings) always accessible
"""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from abc import ABC, abstractmethod

import numpy as np


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class EpiResult(ABC):
    """
    Abstract base class for all EpiTools result objects.

    All public-API results inherit from this class and share:
        - Serialization: to_dict(), to_json(), to_dataframe()
        - Metadata: confidence, method, warnings
        - Visualization: plot()
    """

    _viz_function: Optional[str] = None

    @abstractmethod
    def __repr__(self) -> str: ...

    def __str__(self) -> str:
        return self.__repr__()

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dictionary of all result fields."""
        ...

    def to_json(self, indent: int = 2) -> str:
        """Serialize result to a JSON string."""
        return json.dumps(self._json_safe(self.to_dict()), indent=indent)

    def to_dataframe(self):
        """Return a pandas DataFrame summary of the result."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for to_dataframe(). pip install pandas")
        return pd.DataFrame([self._flatten(self.to_dict())])

    def plot(self, backend: str = "plotly", **kwargs):
        """
        Render a visualization of this result.

        Args:
            backend: 'plotly' (default, interactive) or 'matplotlib' (publication).
            **kwargs: Passed to the underlying plot function.
        """
        if self._viz_function is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} does not have an associated plot function."
            )
        # Import viz dynamically — works regardless of package name
        try:
            from epitools import viz as _viz
        except ImportError:
            try:
                import viz as _viz  # dev / editable install fallback
            except ImportError:
                raise ImportError(
                    "EpiTools viz module not found. "
                    "Make sure the package is installed: pip install -e ."
                )
        func = getattr(_viz, self._viz_function, None)
        if func is None:
            raise AttributeError(
                f"viz.{self._viz_function} not found in epitools.viz. "
                f"Available: {[x for x in dir(_viz) if x.startswith('plot_')]}"
            )
        fig = func(self, backend=backend, **kwargs)

        # Auto-open in browser for Plotly figures in script context
        if backend == "plotly":
            try:
                import plotly.io as pio
                # Only force browser renderer if running as a script (not notebook)
                _in_notebook = False
                try:
                    from IPython import get_ipython
                    _in_notebook = get_ipython() is not None
                except ImportError:
                    pass
                if not _in_notebook:
                    pio.renderers.default = "browser"
            except ImportError:
                pass

        return fig

    @staticmethod
    def _json_safe(obj: Any) -> Any:
        """Recursively convert numpy types to native Python."""
        if isinstance(obj, dict):
            return {k: EpiResult._json_safe(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [EpiResult._json_safe(i) for i in obj]
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return None if np.isnan(obj) else float(obj)
        if isinstance(obj, np.ndarray):
            return EpiResult._json_safe(obj.tolist())
        if isinstance(obj, float) and np.isnan(obj):
            return None
        return obj

    @staticmethod
    def _flatten(d: Dict, parent_key: str = "", sep: str = ".") -> Dict:
        """Flatten nested dict for DataFrame export."""
        items: List[Tuple] = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(EpiResult._flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def _ci_str(self, lower: float, upper: float, digits: int = 3) -> str:
        fmt = f"{{:.{digits}f}}"
        return f"({fmt.format(lower)}\u2013{fmt.format(upper)})"


# ---------------------------------------------------------------------------
# Confidence interval container
# ---------------------------------------------------------------------------

@dataclass
class ConfidenceInterval:
    """
    Container for a confidence interval.

    Attributes:
        lower:      Lower bound.
        upper:      Upper bound.
        confidence: Confidence level (e.g. 0.95).
        method:     Method used to compute the interval.
    """
    lower: float
    upper: float
    confidence: float = 0.95
    method: str = "wald"

    def __repr__(self) -> str:
        return f"CI{int(self.confidence * 100)}% [{self.lower:.4f}, {self.upper:.4f}] ({self.method})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lower": self.lower,
            "upper": self.upper,
            "confidence": self.confidence,
            "method": self.method,
        }

    def contains(self, value: float) -> bool:
        """Return True if value falls within the interval."""
        return self.lower <= value <= self.upper


# ---------------------------------------------------------------------------
# Association measures  (RR, OR, RD, IRR...)
# ---------------------------------------------------------------------------

@dataclass
class AssociationResult(EpiResult):
    """
    Result for a single association measure (RR, OR, RD...).

    Attributes:
        measure:    Name of the measure (e.g. 'risk_ratio').
        estimate:   Point estimate.
        ci:         ConfidenceInterval object.
        p_value:    P-value for the null hypothesis.
        null_value: Null hypothesis value (1.0 for ratios, 0.0 for differences).
        method:     Statistical method used.
        n_total:    Total sample size.
        metadata:   Extra key/value pairs (exposed/unexposed counts, etc.).
    """
    measure: str
    estimate: float
    ci: ConfidenceInterval
    p_value: Optional[float] = None
    null_value: float = 1.0
    method: str = "wald"
    n_total: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    _viz_function = "plot_association"

    def __repr__(self) -> str:
        label = self.measure.replace("_", " ").title()
        sig = ""
        if self.p_value is not None:
            p_str = "<0.001" if self.p_value < 0.001 else f"{self.p_value:.3f}"
            sig = f"  p={p_str}"
        return f"{label}: {self.estimate:.3f} {self._ci_str(self.ci.lower, self.ci.upper)}{sig}"

    @property
    def significant(self) -> bool:
        """True if the CI does not contain the null value."""
        return not self.ci.contains(self.null_value)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "measure": self.measure,
            "estimate": self.estimate,
            "ci_lower": self.ci.lower,
            "ci_upper": self.ci.upper,
            "confidence": self.ci.confidence,
            "method": self.method,
            "p_value": self.p_value,
            "null_value": self.null_value,
            "significant": self.significant,
            "n_total": self.n_total,
            **self.metadata,
        }


# ---------------------------------------------------------------------------
# Proportion / descriptive
# ---------------------------------------------------------------------------

@dataclass
class ProportionResult(EpiResult):
    """
    Result for a proportion or rate with confidence interval.

    Attributes:
        proportion:  Point estimate.
        ci:          ConfidenceInterval.
        numerator:   Event count.
        denominator: Population at risk.
        label:       Human-readable label (e.g. 'attack_rate').
        metadata:    Extra context.
    """
    proportion: float
    ci: ConfidenceInterval
    numerator: Optional[int] = None
    denominator: Optional[int] = None
    label: str = "proportion"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        base = (
            f"{self.label.replace('_', ' ').title()}: {self.proportion:.4f} "
            f"{self._ci_str(self.ci.lower, self.ci.upper)}"
        )
        if self.numerator is not None and self.denominator is not None:
            base += f"  [{self.numerator}/{self.denominator}]"
        return base

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "proportion": self.proportion,
            "ci_lower": self.ci.lower,
            "ci_upper": self.ci.upper,
            "confidence": self.ci.confidence,
            "method": self.ci.method,
            "numerator": self.numerator,
            "denominator": self.denominator,
            **self.metadata,
        }


# ---------------------------------------------------------------------------
# Sample size & power
# ---------------------------------------------------------------------------

@dataclass
class SampleSizeResult(EpiResult):
    """
    Result for a sample size or statistical power calculation.

    Attributes:
        n_total:      Total required sample size.
        n_per_group:  Per-group size for balanced designs.
        n_cases:      Cases required (case-control designs).
        n_controls:   Controls required.
        power:        Achieved or requested power.
        alpha:        Significance level.
        effect_size:  Effect size used.
        design:       Study design name.
        method:       Calculation method.
        assumptions:  Input parameters for traceability.
        note:         Optional interpretive note.
    """
    n_total: Optional[int] = None
    n_per_group: Optional[int] = None
    n_cases: Optional[int] = None
    n_controls: Optional[int] = None
    power: Optional[float] = None
    alpha: float = 0.05
    effect_size: Optional[float] = None
    design: str = ""
    method: str = ""
    assumptions: Dict[str, Any] = field(default_factory=dict)
    note: Optional[str] = None

    def __repr__(self) -> str:
        lines = [f"Sample Size \u2014 {self.design}"]
        if self.n_per_group is not None:
            lines.append(f"  Per group : {self.n_per_group:,}")
        if self.n_total is not None:
            lines.append(f"  Total     : {self.n_total:,}")
        if self.n_cases is not None:
            lines.append(f"  Cases     : {self.n_cases:,}  Controls: {self.n_controls:,}")
        if self.power is not None:
            lines.append(f"  Power     : {self.power:.1%}  \u03b1={self.alpha}")
        if self.note:
            lines.append(f"  Note      : {self.note}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "design": self.design,
            "method": self.method,
            "n_total": self.n_total,
            "n_per_group": self.n_per_group,
            "n_cases": self.n_cases,
            "n_controls": self.n_controls,
            "power": self.power,
            "alpha": self.alpha,
            "effect_size": self.effect_size,
            "assumptions": self.assumptions,
            "note": self.note,
        }


# ---------------------------------------------------------------------------
# Diagnostic test
# ---------------------------------------------------------------------------

@dataclass
class DiagnosticResult(EpiResult):
    """
    Result for a diagnostic test performance evaluation.

    Attributes:
        sensitivity:    True positive rate.
        specificity:    True negative rate.
        ppv:            Positive predictive value.
        npv:            Negative predictive value.
        lr_positive:    Positive likelihood ratio.
        lr_negative:    Negative likelihood ratio.
        accuracy:       Overall accuracy.
        youden:         Youden's J index.
        tp, fp, fn, tn: Confusion matrix counts.
        prevalence:     Prevalence used (sample or provided).
        ci_sensitivity: CI for sensitivity.
        ci_specificity: CI for specificity.
    """
    sensitivity: float
    specificity: float
    ppv: float
    npv: float
    lr_positive: float
    lr_negative: float
    accuracy: float
    youden: float
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0
    prevalence: Optional[float] = None
    ci_sensitivity: Optional[ConfidenceInterval] = None
    ci_specificity: Optional[ConfidenceInterval] = None

    _viz_function = "plot_diagnostic"

    def __repr__(self) -> str:
        sens_ci = (
            f" {self._ci_str(self.ci_sensitivity.lower, self.ci_sensitivity.upper)}"
            if self.ci_sensitivity else ""
        )
        spec_ci = (
            f" {self._ci_str(self.ci_specificity.lower, self.ci_specificity.upper)}"
            if self.ci_specificity else ""
        )
        return (
            f"Sensitivity : {self.sensitivity:.3f}{sens_ci}\n"
            f"Specificity : {self.specificity:.3f}{spec_ci}\n"
            f"PPV         : {self.ppv:.3f}   NPV: {self.npv:.3f}\n"
            f"LR+         : {self.lr_positive:.3f}  LR-: {self.lr_negative:.3f}\n"
            f"Accuracy    : {self.accuracy:.3f}  Youden: {self.youden:.3f}"
        )

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "sensitivity": self.sensitivity,
            "specificity": self.specificity,
            "ppv": self.ppv,
            "npv": self.npv,
            "lr_positive": self.lr_positive,
            "lr_negative": self.lr_negative,
            "accuracy": self.accuracy,
            "youden": self.youden,
            "prevalence": self.prevalence,
            "confusion_matrix": {
                "tp": self.tp, "fp": self.fp,
                "fn": self.fn, "tn": self.tn,
            },
        }
        if self.ci_sensitivity:
            d["ci_sensitivity"] = self.ci_sensitivity.to_dict()
        if self.ci_specificity:
            d["ci_specificity"] = self.ci_specificity.to_dict()
        return d


# ---------------------------------------------------------------------------
# ROC curve
# ---------------------------------------------------------------------------

@dataclass
class ROCResult(EpiResult):
    """
    Result for ROC curve analysis.

    Attributes:
        fpr:               False positive rates array.
        tpr:               True positive rates array.
        thresholds:        Threshold values array.
        auc:               Area under the curve.
        optimal_threshold: Threshold maximising the chosen criterion.
        optimal_point:     Dict with sens/spec at optimal threshold.
        method:            Criterion for optimal threshold selection.
    """
    fpr: np.ndarray
    tpr: np.ndarray
    thresholds: np.ndarray
    auc: float
    optimal_threshold: float
    optimal_point: Dict[str, float]
    method: str = "youden"

    _viz_function = "plot_roc"

    def __repr__(self) -> str:
        sens = self.optimal_point.get("sensitivity", float("nan"))
        spec = self.optimal_point.get("specificity", float("nan"))
        return (
            f"ROC Curve  AUC: {self.auc:.3f}\n"
            f"Optimal threshold ({self.method}): {self.optimal_threshold:.3f}\n"
            f"  \u2192 Sensitivity: {sens:.3f}  Specificity: {spec:.3f}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "auc": self.auc,
            "optimal_threshold": self.optimal_threshold,
            "optimal_sensitivity": self.optimal_point.get("sensitivity"),
            "optimal_specificity": self.optimal_point.get("specificity"),
            "method": self.method,
            "n_thresholds": len(self.thresholds),
        }


# ---------------------------------------------------------------------------
# Stratified analysis (Mantel-Haenszel)
# ---------------------------------------------------------------------------

@dataclass
class StratifiedResult(EpiResult):
    """
    Result for stratified (Mantel-Haenszel) analysis.

    Attributes:
        measure:         'mh_risk_ratio' or 'mh_odds_ratio'.
        mh_estimate:     Pooled MH estimate.
        ci:              CI for pooled estimate.
        p_value:         P-value for pooled test.
        homogeneity_p:   P-value for Breslow-Day homogeneity test.
        effect_modifier: True if homogeneity rejected (p < 0.05).
        stratum_results: Per-stratum AssociationResult list.
        n_strata:        Number of strata.
    """
    measure: str
    mh_estimate: float
    ci: ConfidenceInterval
    p_value: Optional[float] = None
    homogeneity_p: Optional[float] = None
    effect_modifier: bool = False
    stratum_results: List[AssociationResult] = field(default_factory=list)
    n_strata: int = 0

    _viz_function = "plot_forest"

    def __repr__(self) -> str:
        hom = (
            f"  Homogeneity p={self.homogeneity_p:.3f}"
            if self.homogeneity_p is not None else ""
        )
        em_flag = "  [EFFECT MODIFICATION LIKELY]" if self.effect_modifier else ""
        return (
            f"Mantel-Haenszel {self.measure.replace('_', ' ').title()}\n"
            f"  Pooled : {self.mh_estimate:.3f} {self._ci_str(self.ci.lower, self.ci.upper)}\n"
            f"  Strata : {self.n_strata}{hom}{em_flag}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "measure": self.measure,
            "mh_estimate": self.mh_estimate,
            "ci_lower": self.ci.lower,
            "ci_upper": self.ci.upper,
            "confidence": self.ci.confidence,
            "p_value": self.p_value,
            "homogeneity_p": self.homogeneity_p,
            "effect_modifier": self.effect_modifier,
            "n_strata": self.n_strata,
            "strata": [s.to_dict() for s in self.stratum_results],
        }


# ---------------------------------------------------------------------------
# Epidemic model (SIR / SEIR / SEIRD)
# ---------------------------------------------------------------------------

@dataclass
class ModelResult(EpiResult):
    """
    Result for a compartmental epidemic model simulation.

    Attributes:
        model_type:    'SIR', 'SEIR', 'SEIRD', etc.
        t:             Time array.
        compartments:  Dict of compartment name to array.
        parameters:    Input parameters (beta, gamma, R0...).
        r0:            Basic reproduction number.
        peak_infected: Peak infected count.
        peak_time:     Time of peak infection.
        final_size:    Total proportion infected at end.
        metadata:      Extra simulation context.
    """
    model_type: str
    t: np.ndarray
    compartments: Dict[str, np.ndarray]
    parameters: Dict[str, float]
    r0: Optional[float] = None
    peak_infected: Optional[float] = None
    peak_time: Optional[float] = None
    final_size: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    _viz_function = "plot_model"

    def __repr__(self) -> str:
        lines = [f"{self.model_type} Model"]
        if self.r0 is not None:
            lines.append(f"  R\u2080          : {self.r0:.3f}")
        if self.peak_infected is not None:
            lines.append(f"  Peak infected : {self.peak_infected:,.0f}  at t={self.peak_time:.1f}")
        if self.final_size is not None:
            lines.append(f"  Final size    : {self.final_size:.1%}")
        lines.append(f"  Duration      : {self.t[0]:.0f}\u2013{self.t[-1]:.0f}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_type": self.model_type,
            "parameters": self.parameters,
            "r0": self.r0,
            "peak_infected": self.peak_infected,
            "peak_time": self.peak_time,
            "final_size": self.final_size,
            "t_start": float(self.t[0]),
            "t_end": float(self.t[-1]),
            "n_timepoints": len(self.t),
            "compartment_names": list(self.compartments.keys()),
            **self.metadata,
        }

    def to_dataframe(self):
        """Return time-series DataFrame with one column per compartment."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required. pip install pandas")
        return pd.DataFrame({"t": self.t, **self.compartments})


# ---------------------------------------------------------------------------
# Time series / incidence
# ---------------------------------------------------------------------------

@dataclass
class TimeSeriesResult(EpiResult):
    """
    Result for temporal epidemiological analysis (incidence, trends).

    Attributes:
        times:        Array of time points or period labels.
        values:       Observed values (counts or rates).
        trend:        Fitted trend values (if computed).
        trend_method: Name of trend method used.
        doubling_time: Estimated doubling time (if applicable).
        metadata:     Additional analysis context.
    """
    times: np.ndarray
    values: np.ndarray
    trend: Optional[np.ndarray] = None
    trend_method: Optional[str] = None
    doubling_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    _viz_function = "plot_epicurve"

    def __repr__(self) -> str:
        lines = [f"Time Series  n={len(self.times)} periods"]
        lines.append(f"  Total  : {self.values.sum():.0f}  Peak: {self.values.max():.0f}")
        if self.trend_method:
            lines.append(f"  Trend  : {self.trend_method}")
        if self.doubling_time is not None:
            lines.append(f"  Doubling time: {self.doubling_time:.1f} periods")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_periods": len(self.times),
            "total": float(self.values.sum()),
            "peak": float(self.values.max()),
            "trend_method": self.trend_method,
            "doubling_time": self.doubling_time,
            **self.metadata,
        }

    def to_dataframe(self):
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required. pip install pandas")
        data: Dict[str, Any] = {"time": self.times, "value": self.values}
        if self.trend is not None:
            data["trend"] = self.trend
        return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# Regression
# ---------------------------------------------------------------------------

@dataclass
class RegressionResult(EpiResult):
    """
    Result for logistic or Poisson regression.

    Attributes:
        model_type:   'logistic', 'poisson', 'linear'.
        coefficients: Dict of variable to coefficient.
        odds_ratios:  Dict of variable to OR (logistic only).
        ci_table:     Dict of variable to (lower, upper) CI tuple.
        p_values:     Dict of variable to p-value.
        aic:          Akaike information criterion.
        bic:          Bayesian information criterion.
        n:            Sample size.
        converged:    Whether optimisation converged.
    """
    model_type: str
    coefficients: Dict[str, float]
    p_values: Dict[str, float]
    ci_table: Dict[str, Tuple[float, float]]
    odds_ratios: Optional[Dict[str, float]] = None
    aic: Optional[float] = None
    bic: Optional[float] = None
    n: Optional[int] = None
    converged: bool = True

    _viz_function = "plot_forest"

    def __repr__(self) -> str:
        bic_str = f"{self.bic:.2f}" if self.bic is not None else "\u2014"
        lines = [f"{self.model_type.title()} Regression  n={self.n}"]
        if self.aic is not None:
            lines.append(f"  AIC={self.aic:.2f}  BIC={bic_str}")
        lines.append("  Coefficients (p-value):")
        for var, coef in self.coefficients.items():
            p = self.p_values.get(var, float("nan"))
            sig = "*" if p < 0.05 else " "
            lines.append(f"    {sig} {var:30s}: {coef:+.4f}  p={p:.3f}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_type": self.model_type,
            "n": self.n,
            "aic": self.aic,
            "bic": self.bic,
            "converged": self.converged,
            "coefficients": self.coefficients,
            "p_values": self.p_values,
            "ci_table": {k: list(v) for k, v in self.ci_table.items()},
            "odds_ratios": self.odds_ratios,
        }


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def make_ci(
    lower: float,
    upper: float,
    confidence: float = 0.95,
    method: str = "wald",
) -> ConfidenceInterval:
    """Convenience factory for ConfidenceInterval."""
    return ConfidenceInterval(lower=lower, upper=upper, confidence=confidence, method=method)


def make_association(
    measure: str,
    estimate: float,
    ci_lower: float,
    ci_upper: float,
    confidence: float = 0.95,
    method: str = "wald",
    p_value: Optional[float] = None,
    null_value: float = 1.0,
    n_total: Optional[int] = None,
    **metadata,
) -> AssociationResult:
    """Convenience factory for AssociationResult."""
    return AssociationResult(
        measure=measure,
        estimate=estimate,
        ci=make_ci(ci_lower, ci_upper, confidence, method),
        p_value=p_value,
        null_value=null_value,
        method=method,
        n_total=n_total,
        metadata=metadata,
    )


def make_proportion(
    proportion: float,
    ci_lower: float,
    ci_upper: float,
    numerator: Optional[int] = None,
    denominator: Optional[int] = None,
    label: str = "proportion",
    confidence: float = 0.95,
    method: str = "wilson",
) -> ProportionResult:
    """Convenience factory for ProportionResult."""
    return ProportionResult(
        proportion=proportion,
        ci=make_ci(ci_lower, ci_upper, confidence, method),
        numerator=numerator,
        denominator=denominator,
        label=label,
    )


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = [
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
]