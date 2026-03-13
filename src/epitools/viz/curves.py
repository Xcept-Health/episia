"""
viz/curves.py - Epidemic curve and trend visualizations for EpiTools.

Public functions
----------------
    plot_epicurve   — bar chart of cases over time, optional trend overlay
    plot_trend      — trend line only (linear / LOESS / moving average)
    plot_incidence  — incidence rate over time with optional CI band
    plot_doubling   — log-scale growth with doubling time annotation

All functions accept both the internal EpidemicCurve / TimeSeriesResult
objects from stats.time_series and the unified TimeSeriesResult from
api.results. Raw numpy arrays are also accepted for convenience.

Backend selection
-----------------
    backend="plotly"      (default) — interactive, web-ready
    backend="matplotlib"  — publication quality, static
"""

from __future__ import annotations

from typing import Any, List, Optional, Union

import numpy as np

from .plotters import get_plotter, PlotConfig, AnimationConfig, AnimationType
from .plotters.base_plotter import OutputFormat


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _coerce_times_values(
    source: Any,
    times: Optional[np.ndarray],
    values: Optional[np.ndarray],
) -> tuple:
    """
    Extract (times, values, trend, trend_method) from various input types.
    Accepts:
        - api.results.TimeSeriesResult
        - stats.time_series.EpidemicCurve
        - stats.time_series.TimeSeriesResult
        - raw arrays (times + values required)
    """
    trend = None
    trend_method = None
    doubling_time = None

    if source is not None:
        # api.results.TimeSeriesResult
        if hasattr(source, "times") and hasattr(source, "values"):
            times  = source.times
            values = source.values
            trend  = getattr(source, "trend", None)
            trend_method  = getattr(source, "trend_method", None)
            doubling_time = getattr(source, "doubling_time", None)

        # stats.time_series.EpidemicCurve
        elif hasattr(source, "dates") and hasattr(source, "counts"):
            times  = source.dates
            values = source.counts

        # stats.time_series.TimeSeriesResult
        elif hasattr(source, "dates") and hasattr(source, "observed"):
            times  = source.dates
            values = source.observed
            trend  = getattr(source, "trend", None)
            trend_method = getattr(source, "method", None)

    if times is None or values is None:
        raise ValueError(
            "Provide either a result object or explicit times and values arrays."
        )

    times  = np.asarray(times)
    values = np.asarray(values, dtype=float)
    return times, values, trend, trend_method, doubling_time


# ---------------------------------------------------------------------------
# plot_epicurve
# ---------------------------------------------------------------------------

def plot_epicurve(
    result: Any = None,
    *,
    times: Optional[np.ndarray] = None,
    values: Optional[np.ndarray] = None,
    title: str = "Epidemic Curve",
    xlabel: str = "Period",
    ylabel: str = "Cases",
    backend: str = "plotly",
    theme: str = "scientific",
    animate: bool = False,
    config: Optional[PlotConfig] = None,
) -> Any:
    """
    Plot an epidemic curve (cases over time) as a bar chart.

    Args:
        result:   TimeSeriesResult, EpidemicCurve, or None (use times/values).
        times:    Array of time labels (used if result is None).
        values:   Array of case counts (used if result is None).
        title:    Figure title.
        xlabel:   X-axis label.
        ylabel:   Y-axis label.
        backend:  'plotly' (default) or 'matplotlib'.
        theme:    Theme name.
        animate:  If True, bars build up frame by frame (Plotly only).
        config:   Full PlotConfig override — supersedes individual args.

    Returns:
        plotly.graph_objects.Figure or matplotlib.figure.Figure

    Examples::

        # From a TimeSeriesResult
        fig = plot_epicurve(result, title="Ebola 2014 — Guinea")
        fig.show()

        # From raw arrays
        fig = plot_epicurve(times=weeks, values=counts, animate=True)

        # Publication export
        fig = plot_epicurve(result, backend="matplotlib")
        fig.savefig("figure1.pdf", dpi=300, bbox_inches="tight")
    """
    t, v, trend, trend_method, _ = _coerce_times_values(result, times, values)

    # Build a lightweight proxy that plotters can consume
    class _Proxy:
        pass

    proxy = _Proxy()
    proxy.times        = t
    proxy.values       = v
    proxy.trend        = trend
    proxy.trend_method = trend_method

    if config is None:
        anim_cfg = (
            AnimationConfig.frame_buildup(len(t))
            if animate else AnimationConfig.default()
        )
        config = PlotConfig(
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            theme=theme,
            animation=anim_cfg,
        )

    plotter = get_plotter(backend)
    return plotter.plot_epicurve(proxy, config=config)


# ---------------------------------------------------------------------------
# plot_trend
# ---------------------------------------------------------------------------

def plot_trend(
    result: Any = None,
    *,
    times: Optional[np.ndarray] = None,
    values: Optional[np.ndarray] = None,
    show_observed: bool = True,
    title: str = "Trend Analysis",
    xlabel: str = "Period",
    ylabel: str = "Value",
    backend: str = "plotly",
    theme: str = "scientific",
    config: Optional[PlotConfig] = None,
) -> Any:
    """
    Plot a trend line with optional observed values overlay.

    Args:
        result:         TimeSeriesResult with a trend array, or raw input.
        show_observed:  If True, plot observed values as scatter points.
        title:          Figure title.
        xlabel / ylabel: Axis labels.
        backend:        'plotly' or 'matplotlib'.
        theme:          Theme name.
        config:         Full PlotConfig override.

    Returns:
        Figure object.

    Examples::

        fig = plot_trend(result, show_observed=True, title="Weekly incidence trend")
    """
    t, v, trend, trend_method, _ = _coerce_times_values(result, times, values)

    if config is None:
        config = PlotConfig(
            title=title, xlabel=xlabel, ylabel=ylabel, theme=theme,
        )

    pal = _get_palette(theme)

    if backend == "plotly":
        import plotly.graph_objects as go
        fig = go.Figure()

        if show_observed:
            fig.add_trace(go.Scatter(
                x=list(t), y=list(v),
                mode="markers",
                marker=dict(color=pal[0], size=6, opacity=0.6),
                name="Observed",
            ))

        if trend is not None:
            fig.add_trace(go.Scatter(
                x=list(t), y=list(trend),
                mode="lines",
                line=dict(color=pal[1], width=2.5),
                name=trend_method or "Trend",
            ))
        else:
            # Fallback: linear regression
            _t_num = np.arange(len(t), dtype=float)
            slope, intercept = np.polyfit(_t_num, v, 1)
            fitted = slope * _t_num + intercept
            fig.add_trace(go.Scatter(
                x=list(t), y=list(fitted),
                mode="lines",
                line=dict(color=pal[1], width=2.5, dash="dash"),
                name="Linear trend",
            ))

        from .plotters.plotly_plotter import _layout
        fig.update_layout(_layout(config))
        return fig

    else:
        import matplotlib.pyplot as plt
        from .themes.registry import apply_mpl_theme
        apply_mpl_theme(theme)

        fig, ax = plt.subplots(figsize=(config.width / 100, config.height / 100),
                               facecolor="white")
        if show_observed:
            ax.scatter(range(len(t)), v, color=pal[0], s=30, alpha=0.6,
                       label="Observed", zorder=3)

        trend_y = trend if trend is not None else np.polyval(
            np.polyfit(np.arange(len(t)), v, 1), np.arange(len(t))
        )
        ax.plot(range(len(t)), trend_y, color=pal[1], linewidth=2.5,
                label=trend_method or "Trend")

        ax.set_xticks(range(len(t)))
        ax.set_xticklabels([str(x) for x in t], rotation=45, ha="right",
                           fontsize=config.font_size - 2)
        ax.set_xlabel(xlabel, fontsize=config.font_size)
        ax.set_ylabel(ylabel, fontsize=config.font_size)
        ax.set_title(title, fontsize=config.font_size + 2, fontweight="bold")
        if config.show_legend:
            ax.legend(fontsize=config.font_size - 1)
        fig.tight_layout()
        return fig


# ---------------------------------------------------------------------------
# plot_incidence
# ---------------------------------------------------------------------------

def plot_incidence(
    result: Any = None,
    *,
    times: Optional[np.ndarray] = None,
    rates: Optional[np.ndarray] = None,
    ci_lower: Optional[np.ndarray] = None,
    ci_upper: Optional[np.ndarray] = None,
    per: int = 100_000,
    title: str = "Incidence Rate",
    xlabel: str = "Period",
    ylabel: Optional[str] = None,
    backend: str = "plotly",
    theme: str = "scientific",
    config: Optional[PlotConfig] = None,
) -> Any:
    """
    Plot incidence rate over time with optional confidence interval band.

    Args:
        result:    TimeSeriesResult or EpidemicCurve (rates taken from values).
        times:     Time labels array.
        rates:     Incidence rate array.
        ci_lower:  Lower CI bound array (optional).
        ci_upper:  Upper CI bound array (optional).
        per:       Population denominator for ylabel label (default 100 000).
        title:     Figure title.
        xlabel:    X-axis label.
        ylabel:    Y-axis label (auto-generated if None).
        backend:   'plotly' or 'matplotlib'.
        theme:     Theme name.
        config:    Full PlotConfig override.

    Returns:
        Figure object.
    """
    t, v, _, _, _ = _coerce_times_values(result, times, rates)
    y_label = ylabel or f"Rate per {per:,}"

    if config is None:
        config = PlotConfig(
            title=title, xlabel=xlabel, ylabel=y_label, theme=theme,
        )

    pal = _get_palette(theme)

    if backend == "plotly":
        import plotly.graph_objects as go
        fig = go.Figure()

        # CI band
        if ci_lower is not None and ci_upper is not None:
            _lo = np.asarray(ci_lower)
            _hi = np.asarray(ci_upper)
            fig.add_trace(go.Scatter(
                x=list(t) + list(t[::-1]),
                y=list(_hi) + list(_lo[::-1]),
                fill="toself",
                fillcolor=f"rgba({_hex_to_rgb(pal[0])},0.15)",
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False,
                hoverinfo="skip",
            ))

        fig.add_trace(go.Scatter(
            x=list(t), y=list(v),
            mode="lines+markers",
            line=dict(color=pal[0], width=2.5),
            marker=dict(size=5),
            name=y_label,
        ))

        from .plotters.plotly_plotter import _layout
        fig.update_layout(_layout(config))
        return fig

    else:
        import matplotlib.pyplot as plt
        from .themes.registry import apply_mpl_theme
        apply_mpl_theme(theme)

        fig, ax = plt.subplots(figsize=(config.width / 100, config.height / 100),
                               facecolor="white")
        x = np.arange(len(t))

        if ci_lower is not None and ci_upper is not None:
            ax.fill_between(x, ci_lower, ci_upper, alpha=0.15,
                            color=pal[0], label="95% CI")

        ax.plot(x, v, color=pal[0], linewidth=2.5,
                marker="o", markersize=4, label=y_label)

        ax.set_xticks(x)
        ax.set_xticklabels([str(s) for s in t], rotation=45, ha="right",
                           fontsize=config.font_size - 2)
        ax.set_xlabel(xlabel, fontsize=config.font_size)
        ax.set_ylabel(y_label, fontsize=config.font_size)
        ax.set_title(title, fontsize=config.font_size + 2, fontweight="bold")
        if config.show_legend:
            ax.legend(fontsize=config.font_size - 1)
        fig.tight_layout()
        return fig


# ---------------------------------------------------------------------------
# plot_doubling
# ---------------------------------------------------------------------------

def plot_doubling(
    result: Any = None,
    *,
    times: Optional[np.ndarray] = None,
    values: Optional[np.ndarray] = None,
    doubling_time: Optional[float] = None,
    title: str = "Growth Curve",
    xlabel: str = "Period",
    ylabel: str = "Cases (log scale)",
    backend: str = "plotly",
    theme: str = "scientific",
    config: Optional[PlotConfig] = None,
) -> Any:
    """
    Plot cumulative cases on a log scale with doubling time annotation.

    Args:
        result:        TimeSeriesResult (doubling_time read from object if present).
        times:         Time labels.
        values:        Cumulative case counts.
        doubling_time: Doubling time in periods (overrides result attribute).
        title / xlabel / ylabel: Labels.
        backend:       'plotly' or 'matplotlib'.
        theme:         Theme name.
        config:        Full PlotConfig override.

    Returns:
        Figure object.
    """
    t, v, _, _, dt_from_result = _coerce_times_values(result, times, values)
    dt = doubling_time or dt_from_result

    if config is None:
        config = PlotConfig(
            title=title, xlabel=xlabel, ylabel=ylabel, theme=theme,
        )

    pal = _get_palette(theme)

    # Safe log transform
    v_log = np.where(v > 0, np.log2(v), np.nan)

    if backend == "plotly":
        import plotly.graph_objects as go
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=list(t), y=list(v),
            mode="lines+markers",
            line=dict(color=pal[0], width=2.5),
            marker=dict(size=5),
            name="Cases",
        ))

        annotations = []
        if dt is not None:
            annotations.append(dict(
                x=0.02, y=0.95, xref="paper", yref="paper",
                text=f"Doubling time: {dt:.1f} periods",
                showarrow=False,
                font=dict(size=config.font_size, color="#333333"),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="#cccccc",
                borderwidth=1,
            ))

        from .plotters.plotly_plotter import _layout
        fig.update_layout(_layout(
            config,
            yaxis=dict(
                type="log",
                title=ylabel,
                showgrid=config.show_grid,
            ),
            annotations=annotations,
        ))
        return fig

    else:
        import matplotlib.pyplot as plt
        from .themes.registry import apply_mpl_theme
        apply_mpl_theme(theme)

        fig, ax = plt.subplots(figsize=(config.width / 100, config.height / 100),
                               facecolor="white")

        valid = v > 0
        ax.semilogy(np.arange(len(t))[valid], v[valid],
                    color=pal[0], linewidth=2.5,
                    marker="o", markersize=4, label="Cases")

        if dt is not None:
            ax.text(0.02, 0.95,
                    f"Doubling time: {dt:.1f} periods",
                    transform=ax.transAxes, fontsize=config.font_size - 1,
                    verticalalignment="top",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                              edgecolor="#cccccc", alpha=0.8))

        ax.set_xticks(np.arange(len(t)))
        ax.set_xticklabels([str(s) for s in t], rotation=45, ha="right",
                           fontsize=config.font_size - 2)
        ax.set_xlabel(xlabel, fontsize=config.font_size)
        ax.set_ylabel(ylabel, fontsize=config.font_size)
        ax.set_title(title, fontsize=config.font_size + 2, fontweight="bold")
        fig.tight_layout()
        return fig


# ---------------------------------------------------------------------------
# Internal colour helpers
# ---------------------------------------------------------------------------

def _get_palette(theme: str) -> List[str]:
    from .themes.registry import get_palette
    return get_palette(theme)


def _hex_to_rgb(hex_color: str) -> str:
    """Convert '#rrggbb' to 'r,g,b' string for rgba()."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r},{g},{b}"


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = [
    "plot_epicurve",
    "plot_trend",
    "plot_incidence",
    "plot_doubling",
]