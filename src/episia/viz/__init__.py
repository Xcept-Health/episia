"""
viz/__init__.py - Episia visualization layer.

Quick start::

    from episia.viz import plot_epicurve, plot_roc, plot_forest
    from episia.viz import set_theme, get_plotter

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

from .contingency_plot import (
    plot_contingency,
    plot_measures,
)
from .curves import (
    plot_doubling,
    plot_epicurve,
    plot_incidence,
    plot_trend,
)
from .forest import (
    plot_forest,
    plot_meta_forest,
)

# Backend factory
from .plotters import (
    AnimationConfig,
    AnimationType,
    MatplotlibPlotter,
    OutputFormat,
    PlotConfig,
    PlotlyPlotter,
    get_plotter,
)
from .roc import (
    plot_precision_recall,
    plot_roc,
    plot_roc_compare,
)
from .themes import (
    get_available_themes,
    get_palette,
    get_theme,
    register_theme,
    set_theme,
)

# Themes
from .utils import (
    auto_height,
    hex_to_rgba_str,
    p_value_label,
    significance_stars,
)

# Model trajectories (SIR / SEIR / SEIRD)


def plot_model(result, backend="plotly", **kwargs):
    """Plot compartmental model trajectories from a ModelResult."""
    plotter = get_plotter(backend)
    from .plotters import PlotConfig
    config = kwargs.pop("config", None) or PlotConfig(
        **kwargs) if kwargs else PlotConfig()
    return plotter.plot_model(result, config=config)


# Curve / time-series plots

# ROC / diagnostic curves

# Forest plots

# Contingency table plots

# Utilities (exported for advanced users)

__all__ = [
    # Themes
    "set_theme", "get_theme", "get_available_themes",
    "get_palette", "register_theme",
    # Plotters
    "get_plotter", "PlotConfig", "AnimationConfig",
    "AnimationType", "OutputFormat",
    "PlotlyPlotter", "MatplotlibPlotter",
    # Models
    "plot_model",
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
