"""
viz/plotters/plotly_plotter.py - Plotly rendering backend for EpiTools.

Default backend — produces interactive HTML figures suitable for:
    - Notebooks (Jupyter / JupyterLab)
    - Web frontends (React via plotly.js / JSON serialization)
    - Standalone HTML exports

Supported animations
--------------------
    FRAME_BY_FRAME  plot_epicurve, plot_forest, plot_diagnostic
    CONTINUOUS      plot_model, plot_roc
    PLAY_PAUSE      plot_epicurve, plot_model
    SLIDER          plot_model (parameter sweep)

All plot methods accept an optional PlotConfig. If omitted, the
instance default_config is used.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .base_plotter import (
    AnimationConfig,
    AnimationType,
    BasePlotter,
    OutputFormat,
    PlotConfig,
    UnsupportedAnimationError,
)


# ---------------------------------------------------------------------------
# Colour palettes per theme
# ---------------------------------------------------------------------------

_PALETTES: Dict[str, List[str]] = {
    "scientific":  ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd",
                    "#8c564b", "#e377c2", "#7f7f7f"],
    "minimal":     ["#333333", "#888888", "#bbbbbb", "#555555", "#aaaaaa"],
    "dark":        ["#64b5f6", "#ef5350", "#66bb6a", "#ffa726", "#ab47bc",
                    "#26c6da", "#d4e157", "#ff7043"],
    "colorblind":  ["#0072B2", "#E69F00", "#56B4E9", "#009E73", "#F0E442",
                    "#D55E00", "#CC79A7", "#999999"],
}

_BG: Dict[str, str] = {
    "scientific": "#ffffff",
    "minimal":    "#ffffff",
    "dark":       "#1e1e2e",
    "colorblind": "#ffffff",
}

_GRID: Dict[str, str] = {
    "scientific": "#e5e5e5",
    "minimal":    "#f0f0f0",
    "dark":       "#333355",
    "colorblind": "#e5e5e5",
}

_FONT_COLOR: Dict[str, str] = {
    "scientific": "#222222",
    "minimal":    "#333333",
    "dark":       "#eeeeee",
    "colorblind": "#222222",
}


# ---------------------------------------------------------------------------
# Helper: build Plotly layout dict
# ---------------------------------------------------------------------------

def _layout(cfg: PlotConfig, **overrides) -> Dict:
    theme   = cfg.theme
    bg      = _BG.get(theme, "#ffffff")
    grid_c  = _GRID.get(theme, "#e5e5e5")
    font_c  = _FONT_COLOR.get(theme, "#222222")

    title_text = cfg.title
    if cfg.subtitle:
        title_text += f"<br><sup>{cfg.subtitle}</sup>"

    base = dict(
        title=dict(text=title_text, font=dict(size=cfg.font_size + 3, color=font_c)),
        xaxis=dict(
            title=cfg.xlabel,
            showgrid=cfg.show_grid,
            gridcolor=grid_c,
            zeroline=False,
            color=font_c,
        ),
        yaxis=dict(
            title=cfg.ylabel,
            showgrid=cfg.show_grid,
            gridcolor=grid_c,
            zeroline=False,
            color=font_c,
        ),
        plot_bgcolor=bg,
        paper_bgcolor=bg,
        font=dict(size=cfg.font_size, color=font_c),
        legend=dict(visible=cfg.show_legend, bgcolor="rgba(0,0,0,0)"),
        width=cfg.width,
        height=cfg.height,
        margin=dict(l=60, r=30, t=70, b=60),
    )
    base.update(overrides)
    return base


def _palette(cfg: PlotConfig) -> List[str]:
    if cfg.palette:
        return cfg.palette
    return _PALETTES.get(cfg.theme, _PALETTES["scientific"])


# ---------------------------------------------------------------------------
# Helper: build animation frames + layout buttons
# ---------------------------------------------------------------------------

def _make_play_pause_buttons(anim: AnimationConfig) -> List[Dict]:
    """Return updatemenus list with Play / Pause buttons."""
    return [
        dict(
            type="buttons",
            showactive=False,
            y=0,
            x=0.5,
            xanchor="center",
            yanchor="top",
            buttons=[
                dict(
                    label="Play",
                    method="animate",
                    args=[
                        None,
                        dict(
                            frame=dict(duration=anim.frame_ms, redraw=True),
                            transition=dict(duration=anim.transition_ms,
                                            easing=anim.easing),
                            fromcurrent=True,
                            loop=anim.loop,
                        ),
                    ],
                ),
                dict(
                    label="Pause",
                    method="animate",
                    args=[[None], dict(frame=dict(duration=0, redraw=False),
                                       mode="immediate")],
                ),
            ],
        )
    ]


def _make_slider(labels: List[str], anim: AnimationConfig,
                 prefix: str = "t=") -> Dict:
    """Return a Plotly slider dict over animation frames."""
    steps = [
        dict(
            args=[[str(i)],
                  dict(frame=dict(duration=anim.frame_ms, redraw=True),
                       mode="immediate",
                       transition=dict(duration=anim.transition_ms))],
            label=str(lab),
            method="animate",
        )
        for i, lab in enumerate(labels)
    ]
    return dict(
        active=0,
        currentvalue=dict(prefix=prefix, visible=True, xanchor="center"),
        pad=dict(b=10, t=50),
        steps=steps,
    )


# ---------------------------------------------------------------------------
# PlotlyPlotter
# ---------------------------------------------------------------------------

class PlotlyPlotter(BasePlotter):
    """
    Plotly rendering backend.

    Returns plotly.graph_objects.Figure objects.
    Call .show() to display, .to_json() to serialize for React/JS.

    Animations supported
    --------------------
    FRAME_BY_FRAME : plot_epicurve, plot_forest, plot_diagnostic
    CONTINUOUS     : plot_model, plot_roc
    PLAY_PAUSE     : plot_epicurve, plot_model
    SLIDER         : plot_model
    """

    BACKEND_NAME = "plotly"
    SUPPORTED_ANIMATIONS = (
        AnimationType.FRAME_BY_FRAME,
        AnimationType.CONTINUOUS,
        AnimationType.PLAY_PAUSE,
        AnimationType.SLIDER,
    )

    # ------------------------------------------------------------------ epicurve

    def plot_epicurve(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        Epidemic curve — bar chart of cases over time.

        Animation (FRAME_BY_FRAME / PLAY_PAUSE):
            Bars build up period by period from left to right.
        """
        import plotly.graph_objects as go

        cfg   = self._resolve_config(config)
        self._check_animation(cfg)
        anim  = cfg.animation
        color = _palette(cfg)[0]

        times  = list(result.times)
        values = list(result.values)
        n      = len(times)

        if not anim.enabled:
            traces = [
                go.Bar(
                    x=times, y=values,
                    marker_color=color,
                    name="Cases",
                )
            ]
            if result.trend is not None:
                traces.append(go.Scatter(
                    x=times, y=list(result.trend),
                    mode="lines",
                    line=dict(color=_palette(cfg)[1], width=2, dash="dash"),
                    name=result.trend_method or "Trend",
                ))
            layout = _layout(
                cfg,
                xaxis_title=cfg.xlabel or "Period",
                yaxis_title=cfg.ylabel or "Cases",
                bargap=0.15,
            )
            return go.Figure(data=traces, layout=layout)

        # --- animated version ------------------------------------------------
        # Frame i shows bars for periods 0..i
        frames = []
        for i in range(n):
            frame_data = [
                go.Bar(x=times[: i + 1], y=values[: i + 1], marker_color=color)
            ]
            frames.append(go.Frame(data=frame_data, name=str(i)))

        fig = go.Figure(
            data=[go.Bar(x=times[:1], y=values[:1], marker_color=color)],
            frames=frames,
        )
        layout = _layout(
            cfg,
            xaxis=dict(
                title=cfg.xlabel or "Period",
                range=[-0.5, n - 0.5],
                showgrid=cfg.show_grid,
            ),
            yaxis=dict(
                title=cfg.ylabel or "Cases",
                range=[0, max(values) * 1.1],
                showgrid=cfg.show_grid,
            ),
            updatemenus=_make_play_pause_buttons(anim) if cfg.show_legend else [],
            sliders=[_make_slider([str(t) for t in times], anim, prefix="Period: ")],
        )
        fig.update_layout(layout)
        return fig

    # ------------------------------------------------------------------ model

    def plot_model(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        Compartmental model trajectories (SIR / SEIR / SEIRD…).

        Animation (CONTINUOUS / PLAY_PAUSE / SLIDER):
            Lines draw from t=0 forward, one frame per time step.
            SLIDER adds an interactive time scrubber.
        """
        import plotly.graph_objects as go

        cfg   = self._resolve_config(config)
        self._check_animation(cfg)
        anim  = cfg.animation
        pal   = _palette(cfg)

        t            = list(result.t)
        compartments = result.compartments   # dict name -> array
        names        = list(compartments.keys())
        n_steps      = len(t)

        if not anim.enabled:
            traces = []
            for i, (name, arr) in enumerate(compartments.items()):
                traces.append(go.Scatter(
                    x=t, y=list(arr),
                    mode="lines",
                    name=name,
                    line=dict(color=pal[i % len(pal)], width=2.5),
                ))

            annotations = []
            if result.r0 is not None:
                annotations.append(dict(
                    x=0.02, y=0.97, xref="paper", yref="paper",
                    text=f"R₀ = {result.r0:.2f}",
                    showarrow=False,
                    font=dict(size=cfg.font_size, color=_FONT_COLOR.get(cfg.theme)),
                    bgcolor="rgba(255,255,255,0.7)",
                    bordercolor="#cccccc",
                    borderwidth=1,
                ))

            layout = _layout(
                cfg,
                title=cfg.title or f"{result.model_type} Model",
                xaxis_title=cfg.xlabel or "Time",
                yaxis_title=cfg.ylabel or "Population",
                annotations=annotations,
            )
            return go.Figure(data=traces, layout=layout)

        # --- animated: one frame per time step -------------------------------
        frames = []
        for i in range(1, n_steps + 1):
            frame_traces = []
            for j, (name, arr) in enumerate(compartments.items()):
                frame_traces.append(go.Scatter(
                    x=t[:i], y=list(arr[:i]),
                    mode="lines",
                    name=name,
                    line=dict(color=pal[j % len(pal)], width=2.5),
                ))
            frames.append(go.Frame(data=frame_traces, name=str(i - 1)))

        # Initial frame: first point only
        init_traces = [
            go.Scatter(
                x=t[:1], y=list(arr[:1]),
                mode="lines", name=name,
                line=dict(color=pal[j % len(pal)], width=2.5),
            )
            for j, (name, arr) in enumerate(compartments.items())
        ]

        fig = go.Figure(data=init_traces, frames=frames)

        extra: Dict = {}
        if anim.anim_type == AnimationType.SLIDER:
            extra["sliders"] = [_make_slider(
                [f"{v:.1f}" for v in t], anim, prefix="t = "
            )]

        layout = _layout(
            cfg,
            title=cfg.title or f"{result.model_type} Model",
            xaxis=dict(
                title=cfg.xlabel or "Time",
                range=[t[0], t[-1]],
                showgrid=cfg.show_grid,
            ),
            yaxis=dict(
                title=cfg.ylabel or "Population",
                showgrid=cfg.show_grid,
            ),
            updatemenus=_make_play_pause_buttons(anim),
            **extra,
        )
        fig.update_layout(layout)
        return fig

    # ------------------------------------------------------------------ ROC

    def plot_roc(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        ROC curve with AUC annotation and optimal threshold marker.

        Animation (CONTINUOUS):
            The curve traces itself from (0,0) to (1,1) point by point,
            simulating a threshold sweep from high to low.
        """
        import plotly.graph_objects as go

        cfg   = self._resolve_config(config)
        self._check_animation(cfg)
        anim  = cfg.animation
        pal   = _palette(cfg)

        fpr  = list(result.fpr)
        tpr  = list(result.tpr)
        n    = len(fpr)

        # Reference diagonal
        diag = go.Scatter(
            x=[0, 1], y=[0, 1],
            mode="lines",
            line=dict(color="#aaaaaa", width=1, dash="dot"),
            showlegend=False,
            hoverinfo="skip",
        )

        # Optimal threshold marker
        opt_fpr = 1 - result.optimal_point.get("specificity", 0)
        opt_tpr = result.optimal_point.get("sensitivity", 0)
        marker  = go.Scatter(
            x=[opt_fpr], y=[opt_tpr],
            mode="markers+text",
            marker=dict(color=pal[1], size=10, symbol="star"),
            text=[f"  threshold={result.optimal_threshold:.3f}"],
            textposition="middle right",
            name="Optimal",
            textfont=dict(color=_FONT_COLOR.get(cfg.theme)),
        )

        auc_annotation = dict(
            x=0.97, y=0.05, xref="paper", yref="paper",
            text=f"AUC = {result.auc:.3f}",
            showarrow=False,
            font=dict(size=cfg.font_size + 1, color=_FONT_COLOR.get(cfg.theme)),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#cccccc",
            borderwidth=1,
            align="right",
        )

        if not anim.enabled:
            roc_trace = go.Scatter(
                x=fpr, y=tpr,
                mode="lines",
                name=f"ROC (AUC={result.auc:.3f})",
                line=dict(color=pal[0], width=2.5),
                fill="tozeroy",
                fillcolor=f"rgba({int(pal[0][1:3],16)},"
                          f"{int(pal[0][3:5],16)},"
                          f"{int(pal[0][5:7],16)},0.08)",
            )
            layout = _layout(
                cfg,
                title=cfg.title or "ROC Curve",
                xaxis_title=cfg.xlabel or "False Positive Rate (1 − Specificity)",
                yaxis_title=cfg.ylabel or "True Positive Rate (Sensitivity)",
                xaxis=dict(range=[0, 1], constrain="domain"),
                yaxis=dict(range=[0, 1.02], scaleanchor="x", scaleratio=1),
                annotations=[auc_annotation],
            )
            return go.Figure(data=[diag, roc_trace, marker], layout=layout)

        # --- animated: threshold sweep ---------------------------------------
        frames = []
        for i in range(2, n + 1):
            frames.append(go.Frame(
                data=[
                    diag,
                    go.Scatter(
                        x=fpr[:i], y=tpr[:i],
                        mode="lines",
                        line=dict(color=pal[0], width=2.5),
                        fill="tozeroy",
                        fillcolor=f"rgba({int(pal[0][1:3],16)},"
                                  f"{int(pal[0][3:5],16)},"
                                  f"{int(pal[0][5:7],16)},0.08)",
                        showlegend=False,
                    ),
                    marker,
                ],
                name=str(i - 2),
            ))

        fig = go.Figure(
            data=[diag, go.Scatter(x=fpr[:2], y=tpr[:2], mode="lines",
                                   line=dict(color=pal[0], width=2.5)), marker],
            frames=frames,
        )
        layout = _layout(
            cfg,
            title=cfg.title or "ROC Curve",
            xaxis=dict(title=cfg.xlabel or "False Positive Rate",
                       range=[0, 1], showgrid=cfg.show_grid),
            yaxis=dict(title=cfg.ylabel or "True Positive Rate",
                       range=[0, 1.02], showgrid=cfg.show_grid),
            updatemenus=_make_play_pause_buttons(anim),
            annotations=[auc_annotation],
        )
        fig.update_layout(layout)
        return fig

    # ------------------------------------------------------------------ forest

    def plot_forest(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        Forest plot for stratified (MH) or regression results.

        Animation (FRAME_BY_FRAME):
            Rows appear one by one from top to bottom.
        """
        import plotly.graph_objects as go

        cfg  = self._resolve_config(config)
        self._check_animation(cfg)
        anim = cfg.animation
        pal  = _palette(cfg)

        # Collect rows -------------------------------------------------
        rows: List[Dict] = []

        # StratifiedResult
        if hasattr(result, "stratum_results") and result.stratum_results:
            for s in result.stratum_results:
                rows.append(dict(
                    label=s.metadata.get("label", s.measure),
                    est=s.estimate,
                    lo=s.ci.lower,
                    hi=s.ci.upper,
                    p=s.p_value,
                ))
            # Pooled row
            rows.append(dict(
                label="Pooled (MH)",
                est=result.mh_estimate,
                lo=result.ci.lower,
                hi=result.ci.upper,
                p=result.p_value,
                pooled=True,
            ))

        # RegressionResult
        elif hasattr(result, "coefficients"):
            for var, coef in result.coefficients.items():
                lo, hi = result.ci_table.get(var, (coef, coef))
                rows.append(dict(
                    label=var,
                    est=coef,
                    lo=lo,
                    hi=hi,
                    p=result.p_values.get(var),
                ))

        # Single AssociationResult fallback
        else:
            rows.append(dict(
                label=getattr(result, "measure", "estimate"),
                est=result.estimate,
                lo=result.ci.lower,
                hi=result.ci.upper,
                p=result.p_value,
            ))

        n_rows = len(rows)
        y_pos  = list(range(n_rows - 1, -1, -1))  # top to bottom

        def _build_traces(subset_rows, subset_y):
            traces = []
            for row, y in zip(subset_rows, subset_y):
                is_pooled = row.get("pooled", False)
                color     = pal[1] if is_pooled else pal[0]
                size      = 14 if is_pooled else 10
                symbol    = "diamond" if is_pooled else "square"

                # CI line
                traces.append(go.Scatter(
                    x=[row["lo"], row["hi"]], y=[y, y],
                    mode="lines",
                    line=dict(color=color, width=2),
                    showlegend=False,
                    hoverinfo="skip",
                ))
                # Point estimate
                if row.get("p") is not None:
                    _pv = row["p"]
                    _pf = "<0.001" if _pv < 0.001 else f"{_pv:.3f}"
                    p_str = f"p={_pf}"
                else:
                    p_str = ""
                traces.append(go.Scatter(
                    x=[row["est"]], y=[y],
                    mode="markers",
                    marker=dict(color=color, size=size, symbol=symbol),
                    name=row["label"],
                    hovertemplate=(
                        f"<b>{row['label']}</b><br>"
                        f"Estimate: {row['est']:.3f}<br>"
                        f"95% CI: [{row['lo']:.3f}, {row['hi']:.3f}]<br>"
                        f"{p_str}<extra></extra>"
                    ),
                    showlegend=False,
                ))
            return traces

        # null line (1 for ratios, 0 for differences — infer from estimates)
        null_value = 1.0 if all(r["est"] > 0.01 for r in rows) else 0.0

        base_layout = _layout(
            cfg,
            title=cfg.title or "Forest Plot",
            xaxis_title=cfg.xlabel or "Estimate",
            yaxis=dict(
                tickvals=y_pos,
                ticktext=[r["label"] for r in rows],
                showgrid=False,
                zeroline=False,
                color=_FONT_COLOR.get(cfg.theme),
            ),
            shapes=[dict(
                type="line",
                x0=null_value, x1=null_value,
                y0=-0.5, y1=n_rows - 0.5,
                line=dict(color="#999999", width=1, dash="dot"),
            )],
        )

        if not anim.enabled:
            traces = _build_traces(rows, y_pos)
            return go.Figure(data=traces, layout=base_layout)

        # --- animated: rows appear one by one --------------------------------
        frames = []
        for i in range(1, n_rows + 1):
            frames.append(go.Frame(
                data=_build_traces(rows[:i], y_pos[:i]),
                name=str(i - 1),
            ))

        fig = go.Figure(
            data=_build_traces(rows[:1], y_pos[:1]),
            frames=frames,
        )
        base_layout["updatemenus"] = _make_play_pause_buttons(anim)
        fig.update_layout(base_layout)
        return fig

    # ------------------------------------------------------------------ association

    def plot_association(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        Single association measure — horizontal CI plot with reference line.
        Static (no animation by design).
        """
        import plotly.graph_objects as go

        cfg   = self._resolve_config(config)
        pal   = _palette(cfg)
        label = result.measure.replace("_", " ").title()

        null_value = result.null_value

        fig = go.Figure()

        # CI bar
        fig.add_trace(go.Scatter(
            x=[result.ci.lower, result.ci.upper],
            y=[label, label],
            mode="lines",
            line=dict(color=pal[0], width=4),
            showlegend=False,
            hoverinfo="skip",
        ))

        # Point estimate
        p_str = ""
        if result.p_value is not None:
            p_str = f"p={'<0.001' if result.p_value < 0.001 else f'{result.p_value:.3f}'}"

        fig.add_trace(go.Scatter(
            x=[result.estimate],
            y=[label],
            mode="markers",
            marker=dict(color=pal[1], size=14, symbol="diamond"),
            hovertemplate=(
                f"<b>{label}</b><br>"
                f"Estimate: {result.estimate:.3f}<br>"
                f"{int(result.ci.confidence * 100)}% CI: "
                f"[{result.ci.lower:.3f}, {result.ci.upper:.3f}]<br>"
                f"{p_str}<extra></extra>"
            ),
            showlegend=False,
        ))

        sig_color = pal[2] if result.significant else "#aaaaaa"
        significance = "Significant" if result.significant else "Not significant"

        layout = _layout(
            cfg,
            title=cfg.title or label,
            xaxis_title=cfg.xlabel or "Estimate",
            yaxis=dict(showgrid=False, zeroline=False,
                       color=_FONT_COLOR.get(cfg.theme)),
            height=min(cfg.height, 250),
            shapes=[dict(
                type="line",
                x0=null_value, x1=null_value,
                y0=-0.5, y1=0.5,
                line=dict(color="#999999", width=1, dash="dot"),
            )],
            annotations=[dict(
                x=0.99, y=0.95, xref="paper", yref="paper",
                text=significance,
                showarrow=False,
                font=dict(color=sig_color, size=cfg.font_size),
                align="right",
            )],
        )
        fig.update_layout(layout)
        return fig

    # ------------------------------------------------------------------ diagnostic

    def plot_diagnostic(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        Diagnostic test dashboard: confusion matrix heatmap + metrics bars.

        Animation (FRAME_BY_FRAME):
            Metric bars fill in one by one.
        """
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        cfg  = self._resolve_config(config)
        self._check_animation(cfg)
        anim = cfg.animation
        pal  = _palette(cfg)
        font_c = _FONT_COLOR.get(cfg.theme, "#222222")
        bg     = _BG.get(cfg.theme, "#ffffff")

        # Confusion matrix ------------------------------------------------
        cm_values = [
            [result.tn, result.fp],
            [result.fn, result.tp],
        ]
        cm_text = [
            [f"TN<br>{result.tn}", f"FP<br>{result.fp}"],
            [f"FN<br>{result.fn}", f"TP<br>{result.tp}"],
        ]
        cm_trace = go.Heatmap(
            z=cm_values,
            text=cm_text,
            texttemplate="%{text}",
            x=["Predicted Neg", "Predicted Pos"],
            y=["Actual Neg", "Actual Pos"],
            colorscale=[[0, "#d6e8ff"], [1, pal[0]]],
            showscale=False,
            hoverinfo="text",
        )

        # Metrics bar chart -----------------------------------------------
        metrics = {
            "Sensitivity": result.sensitivity,
            "Specificity": result.specificity,
            "PPV":         result.ppv,
            "NPV":         result.npv,
            "Accuracy":    result.accuracy,
            "Youden J":    result.youden,
        }
        m_labels = list(metrics.keys())
        m_values = list(metrics.values())
        colors   = [pal[i % len(pal)] for i in range(len(m_labels))]

        # Subplot layout
        fig = make_subplots(
            rows=1, cols=2,
            column_widths=[0.4, 0.6],
            subplot_titles=["Confusion Matrix", "Performance Metrics"],
        )
        fig.add_trace(cm_trace, row=1, col=1)

        if not anim.enabled:
            fig.add_trace(go.Bar(
                x=m_labels, y=m_values,
                marker_color=colors,
                text=[f"{v:.3f}" for v in m_values],
                textposition="outside",
                showlegend=False,
            ), row=1, col=2)
        else:
            # Initial: first metric only
            fig.add_trace(go.Bar(
                x=m_labels[:1], y=m_values[:1],
                marker_color=colors[:1],
                text=[f"{m_values[0]:.3f}"],
                textposition="outside",
                showlegend=False,
            ), row=1, col=2)

            # Frames: add one metric per frame
            frames = []
            for i in range(1, len(m_labels) + 1):
                frames.append(go.Frame(
                    data=[
                        cm_trace,
                        go.Bar(
                            x=m_labels[:i], y=m_values[:i],
                            marker_color=colors[:i],
                            text=[f"{v:.3f}" for v in m_values[:i]],
                            textposition="outside",
                        ),
                    ],
                    name=str(i - 1),
                ))
            fig.frames = frames
            fig.update_layout(
                updatemenus=_make_play_pause_buttons(anim)
            )

        fig.update_layout(
            title=cfg.title or "Diagnostic Test Performance",
            plot_bgcolor=bg,
            paper_bgcolor=bg,
            font=dict(size=cfg.font_size, color=font_c),
            width=cfg.width,
            height=cfg.height,
            yaxis2=dict(range=[0, 1.15], showgrid=cfg.show_grid,
                        gridcolor=_GRID.get(cfg.theme, "#e5e5e5")),
        )
        return fig

    # ------------------------------------------------------------------ contingency

    def plot_contingency(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        2x2 contingency table — annotated heatmap with risk summary.
        Static (no animation by design).
        """
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        cfg    = self._resolve_config(config)
        pal    = _palette(cfg)
        font_c = _FONT_COLOR.get(cfg.theme, "#222222")
        bg     = _BG.get(cfg.theme, "#ffffff")

        # Extract table cells
        if hasattr(result, "table"):
            tbl = result.table
        else:
            tbl = result

        a, b, c, d = tbl.a, tbl.b, tbl.c, tbl.d
        total = a + b + c + d

        cells = [[d, c], [b, a]]
        texts = [
            [f"TN (d)<br><b>{d}</b><br>{d/total:.1%}",
             f"Exposed Non-cases (c)<br><b>{c}</b><br>{c/total:.1%}"],
            [f"Unexposed Cases (b)<br><b>{b}</b><br>{b/total:.1%}",
             f"Exposed Cases (a)<br><b>{a}</b><br>{a/total:.1%}"],
        ]

        fig = make_subplots(
            rows=1, cols=2,
            column_widths=[0.55, 0.45],
            subplot_titles=["2×2 Table", "Summary"],
        )

        fig.add_trace(go.Heatmap(
            z=cells,
            text=texts,
            texttemplate="%{text}",
            x=["Unexposed", "Exposed"],
            y=["Non-cases", "Cases"],
            colorscale=[[0, "#f0f7ff"], [1, pal[0]]],
            showscale=False,
            hoverinfo="text",
        ), row=1, col=1)

        # Summary metrics
        rr_result  = tbl.risk_ratio()
        or_result  = tbl.odds_ratio()
        chi2       = tbl.chi_square()

        summary_labels = ["Risk Exposed", "Risk Unexposed", "Risk Ratio",
                          "Odds Ratio", "χ² p-value"]
        summary_values = [
            f"{tbl.risk_exposed:.3f}",
            f"{tbl.risk_unexposed:.3f}",
            f"{rr_result.estimate:.3f} ({rr_result.ci_lower:.3f}–{rr_result.ci_upper:.3f})",
            f"{or_result.estimate:.3f} ({or_result.ci_lower:.3f}–{or_result.ci_upper:.3f})",
            f"{chi2['p_value']:.4f}",
        ]

        fig.add_trace(go.Table(
            header=dict(
                values=["<b>Measure</b>", "<b>Value</b>"],
                fill_color=pal[0],
                font=dict(color="white", size=cfg.font_size),
                align="left",
            ),
            cells=dict(
                values=[summary_labels, summary_values],
                fill_color=[[bg, bg] * 3],
                font=dict(color=font_c, size=cfg.font_size - 1),
                align="left",
                height=28,
            ),
        ), row=1, col=2)

        fig.update_layout(
            title=cfg.title or "2×2 Contingency Table",
            plot_bgcolor=bg,
            paper_bgcolor=bg,
            font=dict(size=cfg.font_size, color=font_c),
            width=cfg.width,
            height=cfg.height,
        )
        return fig

    # ------------------------------------------------------------------ save

    def save(
        self,
        fig: Any,
        path: str,
        fmt: OutputFormat = OutputFormat.PNG,
        dpi: int = 150,
    ) -> str:
        """
        Save a Plotly figure to disk.

        Supports: PNG, SVG, PDF (via kaleido), HTML, JSON.
        """
        import os
        ext = f".{fmt.value}"
        if not path.endswith(ext):
            path = path + ext
        path = os.path.abspath(path)

        if fmt == OutputFormat.HTML:
            fig.write_html(path)
        elif fmt == OutputFormat.JSON:
            with open(path, "w") as f:
                f.write(fig.to_json())
        else:
            # PNG / SVG / PDF require kaleido
            try:
                fig.write_image(path, scale=dpi / 72)
            except Exception as e:
                raise RuntimeError(
                    f"Could not save as {fmt.value}. "
                    f"Install kaleido: pip install kaleido\n{e}"
                )
        return path


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ["PlotlyPlotter"]