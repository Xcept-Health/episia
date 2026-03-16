"""
viz/plotters/__init__.py - Episia plotting backends.

Quick start::

    from episia.viz.plotters import get_plotter, PlotlyPlotter, MatplotlibPlotter

    # Default (Plotly, interactive)
    plotter = get_plotter()
    fig = plotter.plot_epicurve(result)
    fig.show()

    # Publication quality (Matplotlib)
    plotter = get_plotter("matplotlib")
    fig = plotter.plot_model(result, config=PlotConfig.publication())
    plotter.save(fig, "figure1", fmt=OutputFormat.PDF)
"""

from .base_plotter import (
    AnimationConfig,
    AnimationType,
    BasePlotter,
    OutputFormat,
    PlotConfig,
    UnsupportedAnimationError,
)
from .plotly_plotter import PlotlyPlotter
from .mpl_plotter import MatplotlibPlotter
from .browser_plotter import save_html, to_react_props, to_json


_BACKENDS = {
    "plotly":      PlotlyPlotter,
    "matplotlib":  MatplotlibPlotter,
    "mpl":         MatplotlibPlotter,   # alias
}


def get_plotter(
    backend: str = "plotly",
    config: PlotConfig = None,
) -> BasePlotter:
    """
    Factory  return a plotter instance for the requested backend.

    Args:
        backend: 'plotly' (default) or 'matplotlib' / 'mpl'.
        config:  Default PlotConfig for the instance.

    Returns:
        BasePlotter subclass instance.

    Raises:
        ValueError: Unknown backend name.
    """
    cls = _BACKENDS.get(backend.lower())
    if cls is None:
        raise ValueError(
            f"Unknown backend '{backend}'. "
            f"Available: {list(_BACKENDS.keys())}"
        )
    return cls(config=config)


__all__ = [
    # Backends
    "PlotlyPlotter",
    "MatplotlibPlotter",
    # Base
    "BasePlotter",
    "PlotConfig",
    "AnimationConfig",
    "AnimationType",
    "OutputFormat",
    "UnsupportedAnimationError",
    # Browser utils
    "save_html",
    "to_react_props",
    "to_json",
    # Factory
    "get_plotter",
]