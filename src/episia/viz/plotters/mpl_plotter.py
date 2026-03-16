"""
viz/plotters/mpl_plotter.py - Matplotlib rendering backend for Episia.

Purpose: publication-quality static figures only.
    - No animations (use PlotlyPlotter for interactive / animated output)
    - Respects .mplstyle theme files
    - Returns matplotlib Figure objects  saveable at any DPI
    - Suitable for journal submissions, theses, reports

Supported output formats: PNG, SVG, PDF (via fig.savefig)
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



# Theme helpers

# Colour palettes mirroring plotly_plotter for consistency
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
    "scientific": "white",
    "minimal":    "white",
    "dark":       "#1e1e2e",
    "colorblind": "white",
}

_FONT_COLOR: Dict[str, str] = {
    "scientific": "#222222",
    "minimal":    "#333333",
    "dark":       "#eeeeee",
    "colorblind": "#222222",
}

# Path to theme files relative to this file
import os as _os
_THEME_DIR = _os.path.join(_os.path.dirname(__file__), "..", "themes")


def _apply_theme(theme: str) -> None:
    """Apply .mplstyle file if it exists, else use a safe built-in fallback."""
    import matplotlib as mpl
    style_path = _os.path.join(_THEME_DIR, f"{theme}.mplstyle")
    if _os.path.isfile(style_path) and _os.path.getsize(style_path) > 0:
        mpl.style.use(style_path)
    else:
        # Safe fallback for empty/missing style files
        fallback = {
            "scientific": "seaborn-v0_8-paper",
            "minimal":    "seaborn-v0_8-whitegrid",
            "dark":       "dark_background",
            "colorblind": "seaborn-v0_8-colorblind",
        }
        try:
            mpl.style.use(fallback.get(theme, "default"))
        except Exception:
            mpl.style.use("default")


def _palette(cfg: PlotConfig) -> List[str]:
    return cfg.palette or _PALETTES.get(cfg.theme, _PALETTES["scientific"])


def _px_to_in(px: int, dpi: int = 100) -> float:
    return px / dpi


def _style_axes(ax, cfg: PlotConfig) -> None:
    """Apply common axes styling."""
    fc = _FONT_COLOR.get(cfg.theme, "#222222")
    ax.set_facecolor(_BG.get(cfg.theme, "white"))
    ax.tick_params(colors=fc, labelsize=cfg.font_size - 1)
    for spine in ax.spines.values():
        spine.set_edgecolor("#cccccc" if cfg.theme != "dark" else "#444466")
    if not cfg.show_grid:
        ax.grid(False)
    else:
        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6,
                color="#dddddd" if cfg.theme != "dark" else "#333355")
        ax.set_axisbelow(True)



# MatplotlibPlotter

class MatplotlibPlotter(BasePlotter):
    """
    Matplotlib rendering backend  static, publication-quality figures.

    Returns matplotlib.figure.Figure objects.

    No animations are supported. Use PlotlyPlotter for animated output.
    Call .save() or fig.savefig(path, dpi=300) to export.
    """

    BACKEND_NAME = "matplotlib"
    SUPPORTED_ANIMATIONS: Tuple[AnimationType, ...] = ()   # none

    #  epicurve

    def plot_epicurve(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        Epidemic curve  bar chart suitable for publication.
        Trend line overlaid if available.
        """
        import matplotlib.pyplot as plt

        cfg = self._resolve_config(config)
        self._check_animation(cfg)   # raises if animation requested
        _apply_theme(cfg.theme)
        pal = _palette(cfg)
        fc  = _FONT_COLOR.get(cfg.theme, "#222222")

        fig, ax = plt.subplots(
            figsize=(_px_to_in(cfg.width), _px_to_in(cfg.height)),
            facecolor=_BG.get(cfg.theme, "white"),
        )

        times  = list(result.times)
        values = list(result.values)

        ax.bar(times, values, color=pal[0], alpha=0.85, edgecolor="none",
               label="Cases")

        if result.trend is not None:
            ax.plot(times, list(result.trend),
                    color=pal[1], linewidth=2, linestyle="--",
                    label=result.trend_method or "Trend")

        ax.set_xlabel(cfg.xlabel or "Period", color=fc, fontsize=cfg.font_size)
        ax.set_ylabel(cfg.ylabel or "Cases",  color=fc, fontsize=cfg.font_size)

        if cfg.title:
            ax.set_title(cfg.title, color=fc, fontsize=cfg.font_size + 2,
                         fontweight="bold")
        if cfg.subtitle:
            ax.set_title(f"{cfg.title}\n{cfg.subtitle}", color=fc,
                         fontsize=cfg.font_size + 2)

        if cfg.show_legend and result.trend is not None:
            ax.legend(fontsize=cfg.font_size - 1)

        _style_axes(ax, cfg)
        fig.tight_layout()
        return fig

    #  model

    def plot_model(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        Compartmental model trajectories  clean multi-line plot.
        R₀ and peak annotations included.
        """
        import matplotlib.pyplot as plt

        cfg = self._resolve_config(config)
        self._check_animation(cfg)
        _apply_theme(cfg.theme)
        pal = _palette(cfg)
        fc  = _FONT_COLOR.get(cfg.theme, "#222222")

        fig, ax = plt.subplots(
            figsize=(_px_to_in(cfg.width), _px_to_in(cfg.height)),
            facecolor=_BG.get(cfg.theme, "white"),
        )

        t = result.t
        for i, (name, arr) in enumerate(result.compartments.items()):
            ax.plot(t, arr, color=pal[i % len(pal)], linewidth=2.2,
                    label=name)

        # Peak annotation
        if result.peak_infected is not None and result.peak_time is not None:
            ax.axvline(result.peak_time, color="#999999", linewidth=1,
                       linestyle=":", alpha=0.8)
            ax.annotate(
                f"Peak: {result.peak_infected:,.0f}\nt={result.peak_time:.1f}",
                xy=(result.peak_time, result.peak_infected),
                xytext=(result.peak_time + (t[-1] - t[0]) * 0.04,
                        result.peak_infected * 0.92),
                fontsize=cfg.font_size - 2,
                color=fc,
                arrowprops=dict(arrowstyle="->", color="#999999", lw=0.8),
            )

        # R0 box
        if result.r0 is not None:
            ax.text(
                0.02, 0.97, f"R₀ = {result.r0:.2f}",
                transform=ax.transAxes,
                fontsize=cfg.font_size - 1,
                verticalalignment="top",
                color=fc,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                          edgecolor="#cccccc", alpha=0.8),
            )

        ax.set_xlabel(cfg.xlabel or "Time",       color=fc, fontsize=cfg.font_size)
        ax.set_ylabel(cfg.ylabel or "Population", color=fc, fontsize=cfg.font_size)
        ax.set_title(cfg.title or f"{result.model_type} Model",
                     color=fc, fontsize=cfg.font_size + 2, fontweight="bold")

        if cfg.show_legend:
            ax.legend(fontsize=cfg.font_size - 1, framealpha=0.8)

        _style_axes(ax, cfg)
        fig.tight_layout()
        return fig

    #  ROC

    def plot_roc(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        ROC curve  square axes, AUC annotation, optimal threshold marker.
        Publication-ready with equal aspect ratio.
        """
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D

        cfg = self._resolve_config(config)
        self._check_animation(cfg)
        _apply_theme(cfg.theme)
        pal = _palette(cfg)
        fc  = _FONT_COLOR.get(cfg.theme, "#222222")

        size = _px_to_in(min(cfg.width, cfg.height))
        fig, ax = plt.subplots(figsize=(size, size),
                               facecolor=_BG.get(cfg.theme, "white"))

        # Fill under curve
        ax.fill_between(result.fpr, result.tpr, alpha=0.08, color=pal[0])
        ax.plot(result.fpr, result.tpr, color=pal[0], linewidth=2.5,
                label=f"AUC = {result.auc:.3f}")

        # Reference diagonal
        ax.plot([0, 1], [0, 1], color="#aaaaaa", linewidth=1,
                linestyle="--", label="Random")

        # Optimal threshold
        opt_fpr = 1 - result.optimal_point.get("specificity", 0)
        opt_tpr = result.optimal_point.get("sensitivity", 0)
        ax.scatter([opt_fpr], [opt_tpr], color=pal[1], s=80,
                   zorder=5, label=f"Optimal (t={result.optimal_threshold:.3f})")
        ax.annotate(
            f"  Sens={opt_tpr:.3f}\n  Spec={1-opt_fpr:.3f}",
            xy=(opt_fpr, opt_tpr),
            xytext=(opt_fpr + 0.05, opt_tpr - 0.07),
            fontsize=cfg.font_size - 2,
            color=fc,
        )

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.02)
        ax.set_aspect("equal")
        ax.set_xlabel(cfg.xlabel or "False Positive Rate (1 − Specificity)",
                      color=fc, fontsize=cfg.font_size)
        ax.set_ylabel(cfg.ylabel or "True Positive Rate (Sensitivity)",
                      color=fc, fontsize=cfg.font_size)
        ax.set_title(cfg.title or "ROC Curve",
                     color=fc, fontsize=cfg.font_size + 2, fontweight="bold")

        if cfg.show_legend:
            ax.legend(fontsize=cfg.font_size - 1, loc="lower right",
                      framealpha=0.85)

        _style_axes(ax, cfg)
        fig.tight_layout()
        return fig

    #  forest

    def plot_forest(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        Forest plot  horizontal CI lines, suitable for meta-analysis tables.
        """
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

        cfg = self._resolve_config(config)
        self._check_animation(cfg)
        _apply_theme(cfg.theme)
        pal = _palette(cfg)
        fc  = _FONT_COLOR.get(cfg.theme, "#222222")

        # Collect rows (same logic as PlotlyPlotter)
        rows: List[Dict] = []

        if hasattr(result, "stratum_results") and result.stratum_results:
            for s in result.stratum_results:
                rows.append(dict(
                    label=s.metadata.get("label", s.measure),
                    est=s.estimate, lo=s.ci.lower, hi=s.ci.upper,
                    p=s.p_value, pooled=False,
                ))
            rows.append(dict(
                label="Pooled (MH)", est=result.mh_estimate,
                lo=result.ci.lower, hi=result.ci.upper,
                p=result.p_value, pooled=True,
            ))
        elif hasattr(result, "coefficients"):
            for var, coef in result.coefficients.items():
                lo, hi = result.ci_table.get(var, (coef, coef))
                rows.append(dict(
                    label=var, est=coef, lo=lo, hi=hi,
                    p=result.p_values.get(var), pooled=False,
                ))
        else:
            rows.append(dict(
                label=getattr(result, "measure", "estimate"),
                est=result.estimate,
                lo=result.ci.lower, hi=result.ci.upper,
                p=result.p_value, pooled=False,
            ))

        n = len(rows)
        row_height = max(0.45, 4.5 / n)
        fig_h = max(3.5, n * row_height + 1.2)

        fig, ax = plt.subplots(
            figsize=(_px_to_in(cfg.width), fig_h),
            facecolor=_BG.get(cfg.theme, "white"),
        )

        null_val = 1.0 if all(r["est"] > 0.01 for r in rows) else 0.0
        ax.axvline(null_val, color="#999999", linewidth=1,
                   linestyle="--", alpha=0.7)

        for i, row in enumerate(rows):
            y = n - 1 - i
            color  = pal[1] if row["pooled"] else pal[0]
            marker = "D" if row["pooled"] else "s"
            ms     = 9  if row["pooled"] else 7

            # CI whisker
            ax.plot([row["lo"], row["hi"]], [y, y],
                    color=color, linewidth=1.8, solid_capstyle="round")
            # Point estimate
            ax.plot(row["est"], y, marker=marker, color=color,
                    markersize=ms, zorder=5)

            # Separator before pooled
            if row["pooled"]:
                ax.axhline(y + 0.5, color="#cccccc", linewidth=0.8,
                           linestyle="-")

            # p-value text
            if row.get("p") is not None:
                pv = row["p"]
                p_str = "p<0.001" if pv < 0.001 else f"p={pv:.3f}"
                ax.text(row["hi"] * 1.02, y, f"  {p_str}",
                        va="center", fontsize=cfg.font_size - 2, color=fc)

        ax.set_yticks(range(n))
        ax.set_yticklabels([r["label"] for r in reversed(rows)],
                           fontsize=cfg.font_size - 1, color=fc)
        ax.set_xlabel(cfg.xlabel or "Estimate",
                      color=fc, fontsize=cfg.font_size)
        ax.set_title(cfg.title or "Forest Plot",
                     color=fc, fontsize=cfg.font_size + 2, fontweight="bold")
        ax.set_ylim(-0.7, n - 0.3)

        _style_axes(ax, cfg)
        ax.yaxis.grid(False)
        fig.tight_layout()
        return fig

    #  association

    def plot_association(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        Single association measure  horizontal CI with reference line.
        Compact figure, suitable as an inline element in a report.
        """
        import matplotlib.pyplot as plt

        cfg   = self._resolve_config(config)
        self._check_animation(cfg)
        _apply_theme(cfg.theme)
        pal   = _palette(cfg)
        fc    = _FONT_COLOR.get(cfg.theme, "#222222")
        label = result.measure.replace("_", " ").title()

        fig, ax = plt.subplots(
            figsize=(_px_to_in(cfg.width), 1.8),
            facecolor=_BG.get(cfg.theme, "white"),
        )

        # CI whisker
        ax.plot([result.ci.lower, result.ci.upper], [0, 0],
                color=pal[0], linewidth=4, solid_capstyle="round")
        # Point estimate
        ax.plot(result.estimate, 0, "D", color=pal[1],
                markersize=12, zorder=5)

        # Null reference
        ax.axvline(result.null_value, color="#999999",
                   linewidth=1, linestyle="--")

        # Annotation
        p_str = ""
        if result.p_value is not None:
            p_str = ("p<0.001" if result.p_value < 0.001
                     else f"p={result.p_value:.3f}")
        ci_str = (f"{int(result.ci.confidence*100)}% CI "
                  f"[{result.ci.lower:.3f}, {result.ci.upper:.3f}]")
        sig = "Significant" if result.significant else "NS"
        ax.text(
            0.99, 0.5,
            f"{result.estimate:.3f}  {ci_str}\n{p_str}  {sig}",
            transform=ax.transAxes, ha="right", va="center",
            fontsize=cfg.font_size - 1, color=fc,
        )

        ax.set_yticks([])
        ax.set_xlabel(cfg.xlabel or label, color=fc, fontsize=cfg.font_size)
        ax.set_title(cfg.title or label,
                     color=fc, fontsize=cfg.font_size + 1, fontweight="bold")

        _style_axes(ax, cfg)
        ax.yaxis.set_visible(False)
        for spine in ["left", "top", "right"]:
            ax.spines[spine].set_visible(False)
        fig.tight_layout()
        return fig

    #  diagnostic

    def plot_diagnostic(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        Diagnostic dashboard: confusion matrix heatmap + metrics bar chart.
        Two-panel layout, publication-ready.
        """
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec

        cfg = self._resolve_config(config)
        self._check_animation(cfg)
        _apply_theme(cfg.theme)
        pal = _palette(cfg)
        fc  = _FONT_COLOR.get(cfg.theme, "#222222")
        bg  = _BG.get(cfg.theme, "white")

        fig = plt.figure(
            figsize=(_px_to_in(cfg.width), _px_to_in(cfg.height)),
            facecolor=bg,
        )
        gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1.4], figure=fig)
        ax_cm  = fig.add_subplot(gs[0])
        ax_bar = fig.add_subplot(gs[1])
        ax_cm.set_facecolor(bg)
        ax_bar.set_facecolor(bg)

        #  Confusion matrix heatmap 
        cm = np.array([
            [result.tn, result.fp],
            [result.fn, result.tp],
        ], dtype=float)

        im = ax_cm.imshow(cm, cmap="Blues", aspect="auto")

        labels = [["TN", "FP"], ["FN", "TP"]]
        for r in range(2):
            for c in range(2):
                ax_cm.text(c, r, f"{labels[r][c]}\n{int(cm[r, c])}",
                           ha="center", va="center",
                           fontsize=cfg.font_size,
                           color="white" if cm[r, c] > cm.max() * 0.6 else fc)

        ax_cm.set_xticks([0, 1])
        ax_cm.set_xticklabels(["Pred Neg", "Pred Pos"],
                               fontsize=cfg.font_size - 1, color=fc)
        ax_cm.set_yticks([0, 1])
        ax_cm.set_yticklabels(["Actual Neg", "Actual Pos"],
                               fontsize=cfg.font_size - 1, color=fc)
        ax_cm.set_title("Confusion Matrix", color=fc,
                         fontsize=cfg.font_size, fontweight="bold")
        ax_cm.tick_params(colors=fc)

        #  Metrics bar chart 
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

        bars = ax_bar.barh(m_labels, m_values, color=colors,
                           edgecolor="none", height=0.6)

        for bar, val in zip(bars, m_values):
            ax_bar.text(
                min(val + 0.02, 0.98), bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center", fontsize=cfg.font_size - 1, color=fc,
            )

        ax_bar.set_xlim(0, 1.15)
        ax_bar.set_xlabel("Value", color=fc, fontsize=cfg.font_size)
        ax_bar.set_title("Performance Metrics", color=fc,
                          fontsize=cfg.font_size, fontweight="bold")
        ax_bar.tick_params(colors=fc)
        ax_bar.invert_yaxis()

        _style_axes(ax_bar, cfg)
        ax_bar.yaxis.grid(False)

        if cfg.title:
            fig.suptitle(cfg.title, fontsize=cfg.font_size + 3,
                         fontweight="bold", color=fc)

        fig.tight_layout()
        return fig

    #  contingency

    def plot_contingency(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        2x2 contingency table  annotated heatmap with summary table.
        """
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec

        cfg = self._resolve_config(config)
        self._check_animation(cfg)
        _apply_theme(cfg.theme)
        pal = _palette(cfg)
        fc  = _FONT_COLOR.get(cfg.theme, "#222222")
        bg  = _BG.get(cfg.theme, "white")

        if hasattr(result, "table"):
            tbl = result.table
        else:
            tbl = result

        a, b, c, d = tbl.a, tbl.b, tbl.c, tbl.d
        total = a + b + c + d

        fig = plt.figure(
            figsize=(_px_to_in(cfg.width), _px_to_in(cfg.height)),
            facecolor=bg,
        )
        gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1.2], figure=fig,
                               wspace=0.35)
        ax_tbl  = fig.add_subplot(gs[0])
        ax_text = fig.add_subplot(gs[1])

        # Heatmap
        cells = np.array([[d, c], [b, a]], dtype=float)
        cell_labels = [
            [f"TN (d)\n{d}\n{d/total:.1%}", f"Exp Non-cases (c)\n{c}\n{c/total:.1%}"],
            [f"Unexp Cases (b)\n{b}\n{b/total:.1%}", f"Exp Cases (a)\n{a}\n{a/total:.1%}"],
        ]
        ax_tbl.imshow(cells, cmap="Blues", aspect="auto")
        for r in range(2):
            for col in range(2):
                ax_tbl.text(col, r, cell_labels[r][col],
                            ha="center", va="center",
                            fontsize=cfg.font_size - 2,
                            color="white" if cells[r, col] > cells.max() * 0.6 else fc)

        ax_tbl.set_xticks([0, 1])
        ax_tbl.set_xticklabels(["Unexposed", "Exposed"],
                                fontsize=cfg.font_size - 1, color=fc)
        ax_tbl.set_yticks([0, 1])
        ax_tbl.set_yticklabels(["Non-cases", "Cases"],
                                fontsize=cfg.font_size - 1, color=fc)
        ax_tbl.set_title("2×2 Table", color=fc,
                          fontsize=cfg.font_size + 1, fontweight="bold")
        ax_tbl.tick_params(colors=fc)

        # Summary text panel
        rr  = tbl.risk_ratio()
        or_ = tbl.odds_ratio()
        chi = tbl.chi_square()

        summary_lines = [
            ("Risk (exposed)",   f"{tbl.risk_exposed:.4f}"),
            ("Risk (unexposed)", f"{tbl.risk_unexposed:.4f}"),
            ("Risk Ratio",
             f"{rr.estimate:.3f}  [{rr.ci_lower:.3f}–{rr.ci_upper:.3f}]"),
            ("Odds Ratio",
             f"{or_.estimate:.3f}  [{or_.ci_lower:.3f}–{or_.ci_upper:.3f}]"),
            ("χ² p-value",      f"{chi['p_value']:.4f}"),
            ("N total",         f"{total}"),
        ]

        ax_text.axis("off")
        ax_text.set_facecolor(bg)

        y_start = 0.92
        line_h  = 0.13
        for i, (label, value) in enumerate(summary_lines):
            y = y_start - i * line_h
            ax_text.text(0.02, y, label + ":", transform=ax_text.transAxes,
                         fontsize=cfg.font_size - 1, color="#888888",
                         va="top")
            ax_text.text(0.55, y, value, transform=ax_text.transAxes,
                         fontsize=cfg.font_size - 1, color=fc,
                         va="top", fontweight="bold")

        ax_text.set_title("Summary", color=fc,
                           fontsize=cfg.font_size + 1, fontweight="bold")

        if cfg.title:
            fig.suptitle(cfg.title, fontsize=cfg.font_size + 3,
                         fontweight="bold", color=fc, y=1.01)

        fig.tight_layout()
        return fig

    #  save

    def save(
        self,
        fig: Any,
        path: str,
        fmt: OutputFormat = OutputFormat.PNG,
        dpi: int = 300,
    ) -> str:
        """
        Save a Matplotlib figure at publication quality.

        Default DPI is 300 (journal standard).
        Supports PNG, SVG, PDF.
        """
        import os

        if fmt in (OutputFormat.HTML, OutputFormat.JSON,
                   OutputFormat.GIF, OutputFormat.MP4):
            raise UnsupportedAnimationError(
                f"MatplotlibPlotter.save() does not support {fmt.value}. "
                "Use PlotlyPlotter for HTML/JSON output."
            )

        ext = f".{fmt.value}"
        if not path.endswith(ext):
            path = path + ext
        path = os.path.abspath(path)

        fig.savefig(path, dpi=dpi, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        return path



# Exports

__all__ = ["MatplotlibPlotter"]