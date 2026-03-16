"""
viz/forest.py - Forest plot visualizations for Episia.

Public functions
----------------
    plot_forest         stratified / regression forest plot
    plot_meta_forest    meta-analysis style with heterogeneity stats
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .plotters import get_plotter, PlotConfig, AnimationConfig, AnimationType
from .themes.registry import get_palette



# _collect_rows helper

def _collect_rows(result: Any) -> Tuple[List[Dict], float]:
    """Extract rows and null_value from various result types."""
    rows: List[Dict] = []
    null_value = 1.0

    # StratifiedResult (api.results)
    if hasattr(result, "stratum_results") and result.stratum_results:
        for s in result.stratum_results:
            rows.append(dict(
                label=s.metadata.get("label", s.measure),
                est=s.estimate,
                lo=s.ci.lower,
                hi=s.ci.upper,
                p=s.p_value,
                n=s.n_total,
                pooled=False,
            ))
        rows.append(dict(
            label="Pooled (MH)",
            est=result.mh_estimate,
            lo=result.ci.lower,
            hi=result.ci.upper,
            p=result.p_value,
            n=None,
            pooled=True,
        ))

    # RegressionResult (api.results)
    elif hasattr(result, "coefficients"):
        null_value = 0.0
        for var, coef in result.coefficients.items():
            lo, hi = result.ci_table.get(var, (coef, coef))
            rows.append(dict(
                label=var,
                est=coef,
                lo=lo,
                hi=hi,
                p=result.p_values.get(var),
                n=None,
                pooled=False,
            ))

    # Bare AssociationResult or single-row fallback
    else:
        rows.append(dict(
            label=getattr(result, "measure", "estimate"),
            est=result.estimate,
            lo=result.ci.lower,
            hi=result.ci.upper,
            p=getattr(result, "p_value", None),
            n=getattr(result, "n_total", None),
            pooled=False,
        ))
        null_value = getattr(result, "null_value", 1.0)

    return rows, null_value


def _p_str(p: Optional[float]) -> str:
    if p is None:
        return ""
    return "p<0.001" if p < 0.001 else f"p={p:.3f}"



# plot_forest

def plot_forest(
    result: Any,
    *,
    title: str = "Forest Plot",
    xlabel: str = "Estimate",
    animate: bool = False,
    backend: str = "plotly",
    theme: str = "scientific",
    config: Optional[PlotConfig] = None,
) -> Any:
    """
    Forest plot for stratified or regression results.

    Args:
        result:   StratifiedResult, RegressionResult, or AssociationResult.
        title:    Figure title.
        xlabel:   X-axis label.
        animate:  Rows appear one by one (Plotly only).
        backend:  'plotly' or 'matplotlib'.
        theme:    Theme name.
        config:   Full PlotConfig override.

    Returns:
        Figure object.

    Example::

        from episia.viz.forest import plot_forest
        plot_forest(stratified_result, title="Stratified OR by age group").show()
    """
    if config is None:
        anim = (
            AnimationConfig(enabled=True, anim_type=AnimationType.FRAME_BY_FRAME,
                            frame_ms=300)
            if animate else AnimationConfig.default()
        )
        config = PlotConfig(
            title=title, xlabel=xlabel, theme=theme, animation=anim,
        )

    return get_plotter(backend).plot_forest(result, config=config)



# plot_meta_forest

def plot_meta_forest(
    estimates: List[float],
    ci_lowers: List[float],
    ci_uppers: List[float],
    labels: List[str],
    *,
    weights: Optional[List[float]] = None,
    pooled_estimate: Optional[float] = None,
    pooled_ci: Optional[Tuple[float, float]] = None,
    i_squared: Optional[float] = None,
    tau_squared: Optional[float] = None,
    p_heterogeneity: Optional[float] = None,
    null_value: float = 1.0,
    title: str = "Meta-Analysis Forest Plot",
    xlabel: str = "Effect Estimate",
    backend: str = "plotly",
    theme: str = "scientific",
    config: Optional[PlotConfig] = None,
) -> Any:
    """
    Meta-analysis style forest plot with heterogeneity statistics.

    Marker sizes are proportional to study weights.
    I² and τ² annotations are included when provided.

    Args:
        estimates:        Per-study point estimates.
        ci_lowers:        Per-study lower CI bounds.
        ci_uppers:        Per-study upper CI bounds.
        labels:           Study / stratum labels.
        weights:          Relative weights (e.g. 1/variance). Auto-normalised.
        pooled_estimate:  Pooled (diamond) point estimate.
        pooled_ci:        (lower, upper) for pooled estimate.
        i_squared:        I² heterogeneity statistic (%).
        tau_squared:      τ² between-study variance.
        p_heterogeneity:  P-value for Q heterogeneity test.
        null_value:       Null reference line position (1.0 for ratios).
        title / xlabel:   Labels.
        backend:          'plotly' or 'matplotlib'.
        theme:            Theme name.
        config:           Full PlotConfig override.

    Returns:
        Figure object.
    """
    n = len(estimates)
    if not (len(ci_lowers) == len(ci_uppers) == len(labels) == n):
        raise ValueError("estimates, ci_lowers, ci_uppers, labels must all have same length.")

    # Normalise weights → marker sizes
    if weights is not None:
        w = np.asarray(weights, dtype=float)
        w_norm = (w / w.max()) * 12 + 4   # sizes 4–16
    else:
        w_norm = np.full(n, 8.0)

    if config is None:
        config = PlotConfig(title=title, xlabel=xlabel, theme=theme,
                            height=max(400, n * 32 + 150))

    pal = get_palette(theme)

    # Heterogeneity annotation text
    het_lines = []
    if i_squared is not None:
        het_lines.append(f"I² = {i_squared:.1f}%")
    if tau_squared is not None:
        het_lines.append(f"τ² = {tau_squared:.4f}")
    if p_heterogeneity is not None:
        het_lines.append(_p_str(p_heterogeneity) + " (heterogeneity)")
    het_text = "  |  ".join(het_lines)

    y_positions = list(range(n - 1, -1, -1))

    if backend == "plotly":
        import plotly.graph_objects as go
        from .plotters.plotly_plotter import _layout, _FONT_COLOR

        fc = _FONT_COLOR.get(theme, "#222222")
        fig = go.Figure()

        # Null line
        fig.add_vline(x=null_value, line=dict(color="#999999", width=1,
                                               dash="dot"))

        for i in range(n):
            y = y_positions[i]
            # CI whisker
            fig.add_trace(go.Scatter(
                x=[ci_lowers[i], ci_uppers[i]], y=[y, y],
                mode="lines",
                line=dict(color=pal[0], width=1.8),
                showlegend=False, hoverinfo="skip",
            ))
            # Point estimate
            fig.add_trace(go.Scatter(
                x=[estimates[i]], y=[y],
                mode="markers",
                marker=dict(color=pal[0], size=float(w_norm[i]),
                            symbol="square"),
                name=labels[i],
                hovertemplate=(
                    f"<b>{labels[i]}</b><br>"
                    f"Estimate: {estimates[i]:.3f}<br>"
                    f"95% CI: [{ci_lowers[i]:.3f}, {ci_uppers[i]:.3f}]"
                    "<extra></extra>"
                ),
                showlegend=False,
            ))

        # Pooled diamond
        if pooled_estimate is not None and pooled_ci is not None:
            y_pool = -1
            lo, hi  = pooled_ci
            mid_h   = 0.35
            diamond_x = [lo, pooled_estimate, hi, pooled_estimate, lo]
            diamond_y = [y_pool, y_pool + mid_h, y_pool,
                         y_pool - mid_h, y_pool]
            fig.add_trace(go.Scatter(
                x=diamond_x, y=diamond_y,
                mode="lines",
                fill="toself",
                fillcolor=pal[1],
                line=dict(color=pal[1], width=1),
                name=f"Pooled: {pooled_estimate:.3f} [{lo:.3f}, {hi:.3f}]",
            ))

        annotations = []
        if het_text:
            annotations.append(dict(
                x=0.5, y=-0.12, xref="paper", yref="paper",
                text=het_text, showarrow=False,
                font=dict(size=config.font_size - 1, color=fc),
                align="center",
            ))

        y_min = (-1.8 if pooled_estimate is not None else -0.5)
        fig.update_layout(_layout(
            config,
            yaxis=dict(
                tickvals=y_positions,
                ticktext=labels,
                range=[y_min, n - 0.3],
                showgrid=False, zeroline=False, color=fc,
            ),
            annotations=annotations,
        ))
        return fig

    else:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        from .themes.registry import apply_mpl_theme
        apply_mpl_theme(theme)

        fig_h = max(4.0, n * 0.45 + 1.8)
        fig, ax = plt.subplots(
            figsize=(config.width / 100, fig_h), facecolor="white",
        )

        ax.axvline(null_value, color="#999999", linewidth=1,
                   linestyle="--", alpha=0.7)

        for i in range(n):
            y = y_positions[i]
            ax.plot([ci_lowers[i], ci_uppers[i]], [y, y],
                    color=pal[0], linewidth=1.8)
            ax.plot(estimates[i], y, "s",
                    color=pal[0], markersize=float(w_norm[i]) * 0.7,
                    zorder=5)

        # Pooled diamond
        if pooled_estimate is not None and pooled_ci is not None:
            lo, hi = pooled_ci
            y_pool = -1
            diamond = mpatches.FancyArrow(
                0, 0, 0, 0   # placeholder  use polygon instead
            )
            poly_x = [lo, pooled_estimate, hi, pooled_estimate]
            poly_y = [y_pool, y_pool + 0.35, y_pool, y_pool - 0.35]
            ax.fill(poly_x, poly_y, color=pal[1], zorder=5)
            ax.plot(poly_x + [poly_x[0]], poly_y + [poly_y[0]],
                    color=pal[1], linewidth=1)

        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels, fontsize=config.font_size - 1)
        ax.set_xlabel(xlabel, fontsize=config.font_size)
        ax.set_title(title, fontsize=config.font_size + 2, fontweight="bold")
        if pooled_estimate is not None:
            ax.set_ylim(-1.8, n - 0.3)
        else:
            ax.set_ylim(-0.5, n - 0.3)

        if het_text:
            fig.text(0.5, -0.02, het_text,
                     ha="center", fontsize=config.font_size - 2,
                     style="italic", transform=ax.transAxes)

        ax.yaxis.grid(False)
        fig.tight_layout()
        return fig


__all__ = ["plot_forest", "plot_meta_forest"]