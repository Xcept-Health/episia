"""
viz/themes/__init__.py - EpiTools theme system.

Quick start::

    from epitools.viz.themes import set_theme, get_available_themes

    set_theme("dark")          # applies globally to all subsequent plots
    set_theme("colorblind")    # accessible Wong palette + distinct line styles

    # Register a custom theme
    from epitools.viz.themes import register_theme
    register_theme("xcept", palette=["#0d6efd","#dc3545","#198754","#ffc107"])
    set_theme("xcept")
"""

from .registry import (
    AVAILABLE_THEMES,
    set_theme,
    get_theme,
    get_available_themes,
    get_palette,
    get_plotly_layout,
    apply_mpl_theme,
    register_theme,
)

__all__ = [
    "AVAILABLE_THEMES",
    "set_theme",
    "get_theme",
    "get_available_themes",
    "get_palette",
    "get_plotly_layout",
    "apply_mpl_theme",
    "register_theme",
]