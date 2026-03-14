"""
viz/contingency_plot.py - 2x2 table visualizations for EpiTools.

Public functions
----------------
    plot_contingency   annotated heatmap + summary metrics
    plot_measures      horizontal CI chart for all association measures
"""

from __future__ import annotations

from typing import Any, List, Optional

import numpy as np

from .plotters import get_plotter, PlotConfig
from .themes.registry import get_palette


# ---------------------------------------------------------------------------
# plot_contingency
# ---------------------------------------------------------------------------

def plot_contingency(
    result: Any,
    *,
    title: str = "2×2 Contingency Table",
    backend: str = "plotly",
    theme: str = "scientific",
    config: Optional[PlotConfig] = None,
) -> Any:
    """
    Annotated 2×2 table heatmap with RR, OR, χ² summary.

    Args:
        result:   Table2x2 instance, or AssociationResult with table metadata.
        title:    Figure title.
        backend:  'plotly' or 'matplotlib'.
        theme:    Theme name.
        config:   Full PlotConfig override.

    Returns:
        Figure object.

    Example::

        from epitools.stats.contingency import Table2x2
        from epitools.viz.contingency_plot import plot_contingency

        tbl = Table2x2(40, 10, 20, 30)
        plot_contingency(tbl, title="Exposure A vs Disease B").show()
    """
    if config is None:
        config = PlotConfig(title=title, theme=theme)

    return get_plotter(backend).plot_contingency(result, config=config)


# ---------------------------------------------------------------------------
# plot_measures
# ---------------------------------------------------------------------------

def plot_measures(
    result: Any,
    *,
    measures: Optional[List[str]] = None,
    title: str = "Association Measures",
    backend: str = "plotly",
    theme: str = "scientific",
    config: Optional[PlotConfig] = None,
) -> Any:
    """
    Horizontal CI chart for all association measures from a Table2x2.

    Displays RR, OR, and RD side by side with their confidence intervals.

    Args:
        result:   Table2x2 or AssociationResult.
        measures: Subset of measures to display (default: all).
        title:    Figure title.
        backend:  'plotly' or 'matplotlib'.
        theme:    Theme name.
        config:   Full PlotConfig override.

    Returns:
        Figure object.
    """
    # Extract Table2x2
    if hasattr(result, "table"):
        tbl = result.table
    else:
        tbl = result

    # Compute measures
    rr  = tbl.risk_ratio()
    or_ = tbl.odds_ratio()
    rd  = tbl.risk_difference()

    rows = [
        dict(label="Risk Ratio",       est=rr.estimate,
             lo=rr.ci_lower,  hi=rr.ci_upper,  null=1.0),
        dict(label="Odds Ratio",        est=or_.estimate,
             lo=or_.ci_lower, hi=or_.ci_upper, null=1.0),
        dict(label="Risk Difference",   est=rd["estimate"],
             lo=rd["ci_lower"], hi=rd["ci_upper"], null=0.0),
    ]

    if measures:
        label_map = {r["label"]: r for r in rows}
        rows = [label_map[m] for m in measures if m in label_map]

    if config is None:
        config = PlotConfig(title=title, theme=theme, height=300)

    pal  = get_palette(theme)
    n    = len(rows)
    y_pos = list(range(n - 1, -1, -1))

    if backend == "plotly":
        import plotly.graph_objects as go
        from .plotters.plotly_plotter import _layout, _FONT_COLOR

        fc  = _FONT_COLOR.get(theme, "#222222")
        fig = go.Figure()

        for row, y in zip(rows, y_pos):
            # Null line per measure
            fig.add_shape(
                type="line",
                x0=row["null"], x1=row["null"],
                y0=y - 0.4, y1=y + 0.4,
                line=dict(color="#cccccc", width=1, dash="dot"),
            )
            # CI bar
            fig.add_trace(go.Scatter(
                x=[row["lo"], row["hi"]], y=[y, y],
                mode="lines",
                line=dict(color=pal[0], width=4),
                showlegend=False, hoverinfo="skip",
            ))
            # Point estimate
            fig.add_trace(go.Scatter(
                x=[row["est"]], y=[y],
                mode="markers",
                marker=dict(color=pal[1], size=12, symbol="diamond"),
                name=row["label"],
                hovertemplate=(
                    f"<b>{row['label']}</b><br>"
                    f"Estimate: {row['est']:.3f}<br>"
                    f"95% CI: [{row['lo']:.3f}, {row['hi']:.3f}]"
                    "<extra></extra>"
                ),
                showlegend=False,
            ))

        fig.update_layout(_layout(
            config,
            yaxis=dict(
                tickvals=y_pos,
                ticktext=[r["label"] for r in rows],
                showgrid=False, zeroline=False, color=fc,
            ),
            xaxis_title="Estimate",
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
        for row, y in zip(rows, y_pos):
            ax.axvline(row["null"], color="#cccccc", linewidth=0.8,
                       linestyle="--", ymin=(y - 0.4) / n,
                       ymax=(y + 0.4) / n)
            ax.plot([row["lo"], row["hi"]], [y, y],
                    color=pal[0], linewidth=4, solid_capstyle="round")
            ax.plot(row["est"], y, "D",
                    color=pal[1], markersize=10, zorder=5)
            ax.text(row["hi"] + 0.02, y,
                    f"  {row['est']:.3f} [{row['lo']:.3f}, {row['hi']:.3f}]",
                    va="center", fontsize=config.font_size - 2)

        ax.set_yticks(y_pos)
        ax.set_yticklabels([r["label"] for r in rows],
                            fontsize=config.font_size - 1)
        ax.set_xlabel("Estimate", fontsize=config.font_size)
        ax.set_title(title, fontsize=config.font_size + 2, fontweight="bold")
        ax.yaxis.grid(False)
        fig.tight_layout()
        return fig


__all__ = ["plot_contingency", "plot_measures"]