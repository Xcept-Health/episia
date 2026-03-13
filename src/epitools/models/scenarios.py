"""
models/scenarios.py - Multi-scenario runner for compartmental models.

Runs a set of parameter scenarios through a model class and returns
a structured comparison — ready for plotting or tabular export.

Public classes
--------------
    ScenarioRunner  — runs N scenarios and returns ScenarioResults
    ScenarioResults — container for multi-scenario comparison
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Type

import numpy as np

from .base import CompartmentalModel
from .parameters import ModelParameters, ScenarioSet


@dataclass
class ScenarioResults:
    """
    Container for results from multiple model scenarios.

    Attributes:
        labels:      Scenario names.
        results:     Corresponding ModelResult objects.
        metrics_df:  pandas DataFrame of key metrics (lazy, call .to_dataframe()).
    """
    labels:  List[str]
    results: List[Any]   # List[ModelResult]

    def __len__(self) -> int:
        return len(self.labels)

    def __iter__(self):
        return iter(zip(self.labels, self.results))

    def to_dataframe(self):
        """Return a pandas DataFrame comparing key metrics across scenarios."""
        import pandas as pd

        rows = []
        for label, res in zip(self.labels, self.results):
            row = {"scenario": label}
            row.update({
                "r0":            res.r0,
                "peak_infected": res.peak_infected,
                "peak_time":     res.peak_time,
                "final_size":    res.final_size,
            })
            # Optional SEIRD metrics
            if "total_deaths" in res.metadata.get("metrics", {}):
                row["total_deaths"] = res.metadata["metrics"]["total_deaths"]
                row["cfr"]          = res.metadata["metrics"].get("cfr")
            rows.append(row)

        return pd.DataFrame(rows).set_index("scenario")

    def plot(
        self,
        compartment: str = "I",
        backend: str = "plotly",
        theme: str = "scientific",
        title: str = "Scenario Comparison",
    ) -> Any:
        """
        Overlay trajectories for all scenarios on a single figure.

        Args:
            compartment: Compartment to plot (e.g. 'I', 'D', 'R').
            backend:     'plotly' or 'matplotlib'.
            theme:       Theme name.
            title:       Figure title.

        Returns:
            Figure object.
        """
        from ..viz.themes.registry import get_palette
        from ..viz.plotters import PlotConfig, get_plotter

        pal = get_palette(theme)

        if backend == "plotly":
            import plotly.graph_objects as go
            from ..viz.plotters.plotly_plotter import _layout

            config = PlotConfig(title=title, theme=theme, xlabel="Time (days)",
                                ylabel=f"Individuals in {compartment}")
            fig = go.Figure()

            for i, (label, res) in enumerate(zip(self.labels, self.results)):
                comp = res.compartments.get(compartment)
                if comp is None:
                    continue
                fig.add_trace(go.Scatter(
                    x=list(res.t), y=list(comp),
                    mode="lines",
                    name=f"{label} (R₀={res.r0:.2f})",
                    line=dict(color=pal[i % len(pal)], width=2.2),
                ))

            fig.update_layout(_layout(config))
            return fig

        else:
            import matplotlib.pyplot as plt
            from ..viz.themes.registry import apply_mpl_theme
            apply_mpl_theme(theme)

            fig, ax = plt.subplots(figsize=(10, 5), facecolor="white")
            for i, (label, res) in enumerate(zip(self.labels, self.results)):
                comp = res.compartments.get(compartment)
                if comp is None:
                    continue
                ax.plot(res.t, comp, color=pal[i % len(pal)], linewidth=2.2,
                        label=f"{label} (R₀={res.r0:.2f})")

            ax.set_xlabel("Time (days)", fontsize=12)
            ax.set_ylabel(f"Individuals in {compartment}", fontsize=12)
            ax.set_title(title, fontsize=14, fontweight="bold")
            ax.legend(fontsize=10)
            fig.tight_layout()
            return fig

    def __repr__(self) -> str:
        return (
            f"ScenarioResults({len(self.labels)} scenarios: "
            f"{self.labels})"
        )


class ScenarioRunner:
    """
    Run multiple parameter scenarios through a single model class.

    Example::

        from epitools.models.parameters import SIRParameters, ScenarioSet
        from epitools.models.scenarios import ScenarioRunner
        from epitools.models.sir import SIRModel

        scenarios = ScenarioSet([
            ("R0=1.5", SIRParameters(N=1_000_000, I0=10, beta=0.15, gamma=0.1)),
            ("R0=2.5", SIRParameters(N=1_000_000, I0=10, beta=0.25, gamma=0.1)),
            ("R0=3.5", SIRParameters(N=1_000_000, I0=10, beta=0.35, gamma=0.1)),
        ])

        runner = ScenarioRunner(SIRModel)
        results = runner.run(scenarios)

        results.to_dataframe()
        results.plot(compartment="I").show()
    """

    def __init__(
        self,
        model_class: Type[CompartmentalModel],
        solver_kwargs: Optional[Dict[str, Any]] = None,
    ):
        """
        Args:
            model_class:    Model class to instantiate (SIRModel, SEIRModel…).
            solver_kwargs:  Extra kwargs forwarded to model.run().
        """
        self.model_class   = model_class
        self.solver_kwargs = solver_kwargs or {}

    def run(self, scenarios: ScenarioSet) -> ScenarioResults:
        """
        Run all scenarios and return a ScenarioResults container.

        Args:
            scenarios: ScenarioSet of (label, parameters) pairs.

        Returns:
            ScenarioResults ready for plotting or DataFrame export.
        """
        labels  = []
        results = []

        for label, params in scenarios:
            model  = self.model_class(params)
            result = model.run(**self.solver_kwargs)
            labels.append(label)
            results.append(result)

        return ScenarioResults(labels=labels, results=results)


__all__ = ["ScenarioRunner", "ScenarioResults"]