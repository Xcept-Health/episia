"""
viz/__init__.py - EpiTools visualization layer.

Quick start::

    from epitools.viz import plot_epicurve, plot_roc, plot_forest
    from epitools.viz import set_theme, get_plotter

    set_theme("dark")

    fig = plot_epicurve(result, animate=True)
    fig.show()

    fig = plot_roc(result, backend="matplotlib")
    fig.savefig("roc.pdf", dpi=300)

Backend selection
-----------------
    All plot functions accept backend='plotly' (default, interactive)
    or backend='matplotlib' (static, publication quality).

    Use get_plotter() for direct backend access and advanced control.
"""

# Themes
from .themes import (
    set_theme,
    get_theme,
    get_available_themes,
    get_palette,
    register_theme,
)

# Backend factory
from .plotters import (
    get_plotter,
    PlotConfig,
    AnimationConfig,
    AnimationType,
    OutputFormat,
    PlotlyPlotter,
    MatplotlibPlotter,
)

# Curve / time-series plots
from .curves import (
    plot_epicurve,
    plot_trend,
    plot_incidence,
    plot_doubling,
)

# ROC / diagnostic curves
from .roc import (
    plot_roc,
    plot_roc_compare,
    plot_precision_recall,
)

# Forest plots
from .forest import (
    plot_forest,
    plot_meta_forest,
)

# Contingency table plots
from .contingency_plot import (
    plot_contingency,
    plot_measures,
)

# Utilities (exported for advanced users)
from .utils import (
    p_value_label,
    significance_stars,
    auto_height,
    hex_to_rgba_str,
)

__all__ = [
    # Themes
    "set_theme", "get_theme", "get_available_themes",
    "get_palette", "register_theme",
    # Plotters
    "get_plotter", "PlotConfig", "AnimationConfig",
    "AnimationType", "OutputFormat",
    "PlotlyPlotter", "MatplotlibPlotter",
    # Curves
    "plot_epicurve", "plot_trend", "plot_incidence", "plot_doubling",
    # ROC
    "plot_roc", "plot_roc_compare", "plot_precision_recall",
    # Forest
    "plot_forest", "plot_meta_forest",
    # Contingency
    "plot_contingency", "plot_measures",
    # Utils
    "p_value_label", "significance_stars", "auto_height", "hex_to_rgba_str",
]