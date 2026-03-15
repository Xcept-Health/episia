"""
viz/roc.py - ROC curve visualizations for EpiTools.

Public functions
----------------
    plot_roc           single ROC curve with AUC + optimal threshold
    plot_roc_compare   multiple ROC curves on the same axes (model comparison)
    plot_precision_recall  precision-recall curve (complement to ROC)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np

from .plotters import get_plotter, PlotConfig, AnimationConfig
from .themes.registry import get_palette



# plot_roc

def plot_roc(
    result: Any,
    *,
    title: str = "ROC Curve",
    animate: bool = False,
    backend: str = "plotly",
    theme: str = "scientific",
    config: Optional[PlotConfig] = None,
) -> Any:
    """
    Plot a single ROC curve with AUC annotation and optimal threshold marker.

    Args:
        result:   ROCResult from stats.diagnostic.roc_analysis().
        title:    Figure title.
        animate:  Trace the curve from (0,0) to (1,1) (Plotly only).
        backend:  'plotly' (default) or 'matplotlib'.
        theme:    Theme name.
        config:   Full PlotConfig override.

    Returns:
        Figure object.

    Example::

        from epitools.stats.diagnostic import roc_analysis
        from epitools.viz.roc import plot_roc

        result = roc_analysis(y_true, y_score)
        plot_roc(result, title="Malaria RDT  ROC").show()
    """
    if config is None:
        anim = (
            AnimationConfig(
                enabled=True,
                anim_type=__import__(
                    "epitools_main.viz.plotters.base_plotter",
                    fromlist=["AnimationType"]
                ).AnimationType.CONTINUOUS,
                duration_ms=3000,
                frame_ms=40,
            )
            if animate else AnimationConfig.default()
        )
        config = PlotConfig(
            title=title,
            theme=theme,
            animation=anim,
        )

    return get_plotter(backend).plot_roc(result, config=config)



# plot_roc_compare

def plot_roc_compare(
    results: List[Any],
    labels: Optional[List[str]] = None,
    *,
    title: str = "ROC Curve Comparison",
    backend: str = "plotly",
    theme: str = "scientific",
    config: Optional[PlotConfig] = None,
) -> Any:
    """
    Overlay multiple ROC curves for model comparison.

    Args:
        results:  List of ROCResult objects.
        labels:   Display name for each curve (defaults to 'Model 1', 'Model 2'…).
        title:    Figure title.
        backend:  'plotly' or 'matplotlib'.
        theme:    Theme name.
        config:   Full PlotConfig override.

    Returns:
        Figure object.

    Example::

        fig = plot_roc_compare(
            [result_lr, result_rf, result_xgb],
            labels=["Logistic", "Random Forest", "XGBoost"],
        )
    """
    if not results:
        raise ValueError("results list is empty.")

    labels = labels or [f"Model {i+1}" for i in range(len(results))]
    pal    = get_palette(theme)

    if config is None:
        config = PlotConfig(title=title, theme=theme)

    if backend == "plotly":
        import plotly.graph_objects as go
        from .plotters.plotly_plotter import _layout

        fig = go.Figure()

        # Reference diagonal
        fig.add_trace(go.Scatter(
            x=[0, 1], y=[0, 1],
            mode="lines",
            line=dict(color="#aaaaaa", width=1, dash="dot"),
            showlegend=False, hoverinfo="skip",
        ))

        for i, (res, label) in enumerate(zip(results, labels)):
            fig.add_trace(go.Scatter(
                x=list(res.fpr), y=list(res.tpr),
                mode="lines",
                name=f"{label} (AUC={res.auc:.3f})",
                line=dict(color=pal[i % len(pal)], width=2.2),
            ))

        fig.update_layout(_layout(
            config,
            xaxis=dict(title="False Positive Rate", range=[0, 1],
                       showgrid=config.show_grid),
            yaxis=dict(title="True Positive Rate", range=[0, 1.02],
                       showgrid=config.show_grid),
        ))
        return fig

    else:
        import matplotlib.pyplot as plt
        from .themes.registry import apply_mpl_theme
        apply_mpl_theme(theme)

        size = min(config.width, config.height) / 100
        fig, ax = plt.subplots(figsize=(size, size), facecolor="white")

        ax.plot([0, 1], [0, 1], color="#aaaaaa", linewidth=1,
                linestyle="--", label="Random")

        for i, (res, label) in enumerate(zip(results, labels)):
            ax.fill_between(res.fpr, res.tpr, alpha=0.05,
                            color=pal[i % len(pal)])
            ax.plot(res.fpr, res.tpr,
                    color=pal[i % len(pal)], linewidth=2.2,
                    label=f"{label} (AUC={res.auc:.3f})")

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.02)
        ax.set_aspect("equal")
        ax.set_xlabel("False Positive Rate", fontsize=config.font_size)
        ax.set_ylabel("True Positive Rate", fontsize=config.font_size)
        ax.set_title(title, fontsize=config.font_size + 2, fontweight="bold")
        ax.legend(fontsize=config.font_size - 1, loc="lower right")
        fig.tight_layout()
        return fig



# plot_precision_recall

def plot_precision_recall(
    y_true: Any,
    y_score: Any,
    *,
    label: str = "Model",
    title: str = "Precision-Recall Curve",
    backend: str = "plotly",
    theme: str = "scientific",
    config: Optional[PlotConfig] = None,
) -> Any:
    """
    Plot a precision-recall curve.

    More informative than ROC when classes are imbalanced.

    Args:
        y_true:   True binary labels.
        y_score:  Predicted probabilities or scores.
        label:    Curve label.
        title:    Figure title.
        backend:  'plotly' or 'matplotlib'.
        theme:    Theme name.
        config:   Full PlotConfig override.

    Returns:
        Figure object.
    """
    from sklearn.metrics import precision_recall_curve, average_precision_score

    y_true  = np.asarray(y_true)
    y_score = np.asarray(y_score)

    precision, recall, _ = precision_recall_curve(y_true, y_score)
    ap = average_precision_score(y_true, y_score)
    baseline = y_true.mean()

    if config is None:
        config = PlotConfig(title=title, theme=theme)

    pal = get_palette(theme)

    if backend == "plotly":
        import plotly.graph_objects as go
        from .plotters.plotly_plotter import _layout

        fig = go.Figure()

        # Baseline
        fig.add_trace(go.Scatter(
            x=[0, 1], y=[baseline, baseline],
            mode="lines",
            line=dict(color="#aaaaaa", width=1, dash="dot"),
            showlegend=False, hoverinfo="skip",
        ))

        fig.add_trace(go.Scatter(
            x=list(recall), y=list(precision),
            mode="lines",
            fill="tozeroy",
            fillcolor=f"rgba({_hex_to_rgb(pal[0])},0.08)",
            line=dict(color=pal[0], width=2.5),
            name=f"{label} (AP={ap:.3f})",
        ))

        fig.update_layout(_layout(
            config,
            xaxis=dict(title="Recall", range=[0, 1], showgrid=config.show_grid),
            yaxis=dict(title="Precision", range=[0, 1.02],
                       showgrid=config.show_grid),
            annotations=[dict(
                x=0.97, y=0.05, xref="paper", yref="paper",
                text=f"AP = {ap:.3f}",
                showarrow=False,
                font=dict(size=config.font_size + 1),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="#cccccc", borderwidth=1, align="right",
            )],
        ))
        return fig

    else:
        import matplotlib.pyplot as plt
        from .themes.registry import apply_mpl_theme
        apply_mpl_theme(theme)

        fig, ax = plt.subplots(
            figsize=(config.width / 100, config.height / 100),
            facecolor="white",
        )
        ax.axhline(baseline, color="#aaaaaa", linewidth=1, linestyle="--",
                   label="Baseline")
        ax.fill_between(recall, precision, alpha=0.08, color=pal[0])
        ax.plot(recall, precision, color=pal[0], linewidth=2.5,
                label=f"{label} (AP={ap:.3f})")

        ax.text(0.97, 0.05, f"AP = {ap:.3f}",
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=config.font_size - 1,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                          edgecolor="#cccccc", alpha=0.8))

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.05)
        ax.set_xlabel("Recall",    fontsize=config.font_size)
        ax.set_ylabel("Precision", fontsize=config.font_size)
        ax.set_title(title, fontsize=config.font_size + 2, fontweight="bold")
        ax.legend(fontsize=config.font_size - 1)
        fig.tight_layout()
        return fig


def _hex_to_rgb(h: str) -> str:
    h = h.lstrip("#")
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"


__all__ = ["plot_roc", "plot_roc_compare", "plot_precision_recall"]