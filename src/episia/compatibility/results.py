"""
episia.compatibility.results - Result objects for coding robustness analysis.

CodingRobustnessResult holds all metrics produced by CodingComparator
and exposes the standard Episia interface via EpiResult base class:
    .summary(), .plot(), .to_dataframe(), .to_dict(), .to_json()

No duplication: reuses EpiResult and ConfidenceInterval from episia.api.results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from episia.api.results import ConfidenceInterval, EpiResult


# Per-measure delta

@dataclass
class MeasureDelta:
    """Delta between two coding versions for a single epidemiological measure."""

    measure: str          # e.g. "risk_ratio", "odds_ratio", "prevalence"
    value_v1: float
    value_v2: float
    ci_v1: Optional[ConfidenceInterval] = None
    ci_v2: Optional[ConfidenceInterval] = None

    
    # Convenience constructors
    
    @classmethod
    def from_values(
        cls,
        measure: str,
        value_v1: float,
        value_v2: float,
        ci_lower_v1: Optional[float] = None,
        ci_upper_v1: Optional[float] = None,
        ci_lower_v2: Optional[float] = None,
        ci_upper_v2: Optional[float] = None,
        method: str = "wald",
    ) -> "MeasureDelta":
        """Build a MeasureDelta from raw lower/upper CI bounds."""
        ci_v1 = (
            ConfidenceInterval(lower=ci_lower_v1, upper=ci_upper_v1, method=method)
            if ci_lower_v1 is not None and ci_upper_v1 is not None
            else None
        )
        ci_v2 = (
            ConfidenceInterval(lower=ci_lower_v2, upper=ci_upper_v2, method=method)
            if ci_lower_v2 is not None and ci_upper_v2 is not None
            else None
        )
        return cls(measure=measure, value_v1=value_v1, value_v2=value_v2,
                   ci_v1=ci_v1, ci_v2=ci_v2)

    
    # Derived properties

    @property
    def absolute_delta(self) -> float:
        return self.value_v2 - self.value_v1

    @property
    def relative_delta(self) -> float:
        if self.value_v1 == 0:
            return float("nan")
        return (self.value_v2 - self.value_v1) / abs(self.value_v1)

    @property
    def conclusion_changed(self) -> bool:
        """
        True when the two CIs do not overlap, meaning the coding version
        materially changes the epidemiological conclusion.
        Falls back to a 10 % relative threshold when CIs are absent.
        """
        if self.ci_v1 is None or self.ci_v2 is None:
            import math
            return not math.isnan(self.relative_delta) and abs(self.relative_delta) > 0.10
        return (self.ci_v1.upper < self.ci_v2.lower or
                self.ci_v2.upper < self.ci_v1.lower)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "measure": self.measure,
            "value_v1": self.value_v1,
            "value_v2": self.value_v2,
            "absolute_delta": self.absolute_delta,
            "relative_delta_pct": self.relative_delta * 100,
            "conclusion_changed": bool(self.conclusion_changed),
        }
        if self.ci_v1:
            d["ci_lower_v1"] = self.ci_v1.lower
            d["ci_upper_v1"] = self.ci_v1.upper
        if self.ci_v2:
            d["ci_lower_v2"] = self.ci_v2.lower
            d["ci_upper_v2"] = self.ci_v2.upper
        return d

    def __repr__(self) -> str:
        direction = "+" if self.absolute_delta >= 0 else ""
        return (
            f"MeasureDelta({self.measure}: "
            f"{self.value_v1:.4f} -> {self.value_v2:.4f} "
            f"[{direction}{self.absolute_delta:.4f}, "
            f"{self.relative_delta * 100:+.1f}%]"
            f"{' CONCLUSION CHANGED' if self.conclusion_changed else ''})"
        )

# Main result object — inherits EpiResult for the standard Episia interface

@dataclass
class CodingRobustnessResult(EpiResult):
    """
    Full robustness report produced by CodingComparator.

    Inherits from EpiResult: .to_dict(), .to_json(), .to_dataframe(), .plot().

    Attributes
    ----------
    coding_system_v1 : str
        Label for the first coding system (e.g. "ICD-10").
    coding_system_v2 : str
        Label for the second coding system (e.g. "ICD-11").
    n_v1 : int
        Number of cases (outcome == 1) in dataset v1.
    n_v2 : int
        Number of cases (outcome == 1) in dataset v2.
    deltas : list[MeasureDelta]
        One entry per computed epidemiological measure.
    robustness_score : float
        Proportion of measures whose conclusions are STABLE (0-1).
    unstable_measures : list[str]
        Names of measures where conclusions changed.
    metadata : dict
        Free-form metadata (dataset shape, column names, …).
    """

    coding_system_v1: str = "V1"
    coding_system_v2: str = "V2"
    n_v1: int = 0
    n_v2: int = 0
    deltas: List[MeasureDelta] = field(default_factory=list)
    robustness_score: float = 1.0
    unstable_measures: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    
    # EpiResult interface
    
    def __repr__(self) -> str:
        return (
            f"CodingRobustnessResult("
            f"{self.coding_system_v1} vs {self.coding_system_v2}, "
            f"robustness={self.robustness_score:.2f}, "
            f"unstable={len(self.unstable_measures)}/{len(self.deltas)})"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "coding_system_v1": self.coding_system_v1,
            "coding_system_v2": self.coding_system_v2,
            "n_v1": self.n_v1,
            "n_v2": self.n_v2,
            "robustness_score": self.robustness_score,
            "unstable_measures": self.unstable_measures,
            "deltas": [d.to_dict() for d in self.deltas],
            "metadata": self.metadata,
        }

    def to_dataframe(self) -> pd.DataFrame:
        """Return deltas as a tidy DataFrame (one row per measure)."""
        rows = []
        for d in self.deltas:
            row = {
                "measure": d.measure,
                f"value_{self.coding_system_v1}": d.value_v1,
                f"value_{self.coding_system_v2}": d.value_v2,
                "absolute_delta": d.absolute_delta,
                "relative_delta_pct": d.relative_delta * 100,
                "conclusion_changed": bool(d.conclusion_changed),
            }
            rows.append(row)
        return pd.DataFrame(rows)

    def plot(self, backend: str = "plotly"):
        """
        Forest-style bar plot showing measure values side by side.

        Parameters
        ----------
        backend : {"plotly", "matplotlib"}
        """
        df = self.to_dataframe()
        if df.empty:
            raise ValueError("No deltas to plot.")

        v1_col = f"value_{self.coding_system_v1}"
        v2_col = f"value_{self.coding_system_v2}"

        if backend == "plotly":
            return self._plot_plotly(df, v1_col, v2_col)
        elif backend == "matplotlib":
            return self._plot_matplotlib(df, v1_col, v2_col)
        else:
            raise ValueError(f"Unknown backend: {backend!r}. Use 'plotly' or 'matplotlib'.")

    
    # Human-readable summary
    
    def summary(self) -> str:
        """Human-readable summary of the robustness analysis."""
        lines = [
            "Coding Robustness Analysis",
            "=" * 42,
            f"  V1 ({self.coding_system_v1}) cases : {self.n_v1}",
            f"  V2 ({self.coding_system_v2}) cases : {self.n_v2}",
            f"  Case delta                : {self.n_v2 - self.n_v1:+d} "
            f"({(self.n_v2 - self.n_v1) / max(self.n_v1, 1) * 100:+.1f}%)",
            "",
            f"  Robustness score          : {self.robustness_score:.2f}",
            f"  Measures computed         : {len(self.deltas)}",
            f"  Conclusions changed       : {len(self.unstable_measures)}",
        ]
        if self.unstable_measures:
            lines.append(
                f"  Unstable measures         : {', '.join(self.unstable_measures)}"
            )
        lines += ["", "  Per-measure deltas:"]
        for d in self.deltas:
            lines.append(f"    {d}")
        return "\n".join(lines)

    
    # Private plot helpers

    def _plot_plotly(self, df: pd.DataFrame, v1_col: str, v2_col: str):
        try:
            import plotly.graph_objects as go
        except ImportError as exc:
            raise ImportError("plotly is required for backend='plotly'.") from exc

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name=self.coding_system_v1,
            x=df["measure"], y=df[v1_col],
            marker_color="#4C8CBF",
        ))
        fig.add_trace(go.Bar(
            name=self.coding_system_v2,
            x=df["measure"], y=df[v2_col],
            marker_color="#E07B54",
        ))
        fig.update_layout(
            title="Epidemiological Measures: Coding Robustness",
            xaxis_title="Measure",
            yaxis_title="Value",
            barmode="group",
            template="plotly_white",
        )
        return fig

    def _plot_matplotlib(self, df: pd.DataFrame, v1_col: str, v2_col: str):
        try:
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError as exc:
            raise ImportError("matplotlib is required for backend='matplotlib'.") from exc

        x = np.arange(len(df))
        width = 0.35
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(x - width / 2, df[v1_col], width,
               label=self.coding_system_v1, color="#4C8CBF")
        ax.bar(x + width / 2, df[v2_col], width,
               label=self.coding_system_v2, color="#E07B54")
        ax.set_xticks(x)
        ax.set_xticklabels(df["measure"], rotation=30, ha="right")
        ax.set_ylabel("Value")
        ax.set_title("Epidemiological Measures: Coding Robustness")
        ax.legend()
        fig.tight_layout()
        return fig