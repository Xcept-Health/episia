"""
viz/themes/registry.py - Theme management for EpiTools visualizations.

Manages both Matplotlib .mplstyle themes and Plotly layout templates.
Provides a unified set_theme() / get_theme() API used by both backends.

Available themes
----------------
    scientific  — publication-ready, clean, high-contrast (default)
    minimal     — ultra-clean, no grid, maximum whitespace
    dark        — dark background for dashboards and presentations
    colorblind  — Wong (2011) accessible palette + distinct line styles
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import matplotlib as _mpl

# ---------------------------------------------------------------------------
# Theme registry
# ---------------------------------------------------------------------------

_THEME_DIR = os.path.join(os.path.dirname(__file__))

# All built-in theme names
AVAILABLE_THEMES: List[str] = ["scientific", "minimal", "dark", "colorblind"]

# Currently active theme (module-level state)
_active_theme: str = "scientific"

# Plotly colour palettes per theme (mirrors plotly_plotter._PALETTES)
_PLOTLY_PALETTES: Dict[str, List[str]] = {
    "scientific":  ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd",
                    "#8c564b", "#e377c2", "#7f7f7f"],
    "minimal":     ["#333333", "#888888", "#bbbbbb", "#555555", "#aaaaaa"],
    "dark":        ["#64b5f6", "#ef5350", "#66bb6a", "#ffa726", "#ab47bc",
                    "#26c6da", "#d4e157", "#ff7043"],
    "colorblind":  ["#0072B2", "#E69F00", "#56B4E9", "#009E73", "#F0E442",
                    "#D55E00", "#CC79A7", "#999999"],
}

# Plotly paper/plot background per theme
_PLOTLY_BG: Dict[str, Dict[str, str]] = {
    "scientific":  {"paper": "#ffffff", "plot": "#ffffff", "font": "#222222"},
    "minimal":     {"paper": "#ffffff", "plot": "#ffffff", "font": "#333333"},
    "dark":        {"paper": "#1e1e2e", "plot": "#1e1e2e", "font": "#eeeeee"},
    "colorblind":  {"paper": "#ffffff", "plot": "#ffffff", "font": "#222222"},
}

# Matplotlib built-in fallbacks when .mplstyle file is empty / missing
_MPL_FALLBACKS: Dict[str, str] = {
    "scientific":  "seaborn-v0_8-paper",
    "minimal":     "seaborn-v0_8-white",
    "dark":        "dark_background",
    "colorblind":  "seaborn-v0_8-colorblind",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def set_theme(theme: str) -> None:
    """
    Set the active EpiTools theme globally.

    Applies the corresponding Matplotlib style immediately.
    Plotly figures will pick it up on next plot call.

    Args:
        theme: One of 'scientific', 'minimal', 'dark', 'colorblind'.

    Raises:
        ValueError: Unknown theme name.

    Example::

        from epitools.viz.themes.registry import set_theme
        set_theme("dark")
    """
    global _active_theme
    _validate(theme)
    _active_theme = theme
    _apply_mpl(theme)


def get_theme() -> str:
    """Return the currently active theme name."""
    return _active_theme


def get_available_themes() -> List[str]:
    """Return list of all available theme names."""
    return AVAILABLE_THEMES.copy()


def get_palette(theme: Optional[str] = None) -> List[str]:
    """
    Return the colour palette for a given theme (or the active theme).

    Args:
        theme: Theme name. Defaults to active theme.

    Returns:
        List of hex colour strings.
    """
    t = theme or _active_theme
    _validate(t)
    return _PLOTLY_PALETTES[t].copy()


def get_plotly_layout(theme: Optional[str] = None) -> Dict[str, Any]:
    """
    Return a base Plotly layout dict for a given theme.

    Intended for use inside plotly_plotter — provides consistent
    background colours and font colours per theme.

    Args:
        theme: Theme name. Defaults to active theme.

    Returns:
        Dict suitable for go.Figure(layout=...) or fig.update_layout().
    """
    t = theme or _active_theme
    _validate(t)
    bg = _PLOTLY_BG[t]
    return {
        "paper_bgcolor": bg["paper"],
        "plot_bgcolor":  bg["plot"],
        "font":          {"color": bg["font"]},
        "colorway":      _PLOTLY_PALETTES[t],
    }


def apply_mpl_theme(theme: Optional[str] = None) -> None:
    """
    Apply Matplotlib style for the given (or active) theme.

    Called automatically by MatplotlibPlotter before each plot.
    Can be called manually to affect any subsequent plt calls.

    Args:
        theme: Theme name. Defaults to active theme.
    """
    t = theme or _active_theme
    _validate(t)
    _apply_mpl(t)


def register_theme(
    name: str,
    palette: List[str],
    mplstyle_path: Optional[str] = None,
    bg_paper: str = "#ffffff",
    bg_plot: str = "#ffffff",
    font_color: str = "#222222",
) -> None:
    """
    Register a custom theme at runtime.

    Args:
        name:           Theme identifier (must be unique).
        palette:        List of hex colour strings (min 4).
        mplstyle_path:  Path to a .mplstyle file (optional).
        bg_paper:       Plotly paper background colour.
        bg_plot:        Plotly plot background colour.
        font_color:     Default font colour for Plotly.

    Raises:
        ValueError: palette has fewer than 4 colours.

    Example::

        register_theme(
            "xcept",
            palette=["#0d6efd", "#dc3545", "#198754", "#ffc107"],
            bg_paper="#f8f9fa",
        )
        set_theme("xcept")
    """
    if len(palette) < 4:
        raise ValueError("palette must have at least 4 colours.")

    AVAILABLE_THEMES.append(name)
    _PLOTLY_PALETTES[name] = palette
    _PLOTLY_BG[name] = {
        "paper": bg_paper, "plot": bg_plot, "font": font_color,
    }

    if mplstyle_path:
        _MPL_FALLBACKS[name] = mplstyle_path   # treated as a path by _apply_mpl
    else:
        _MPL_FALLBACKS[name] = "default"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _validate(theme: str) -> None:
    if theme not in AVAILABLE_THEMES:
        raise ValueError(
            f"Unknown theme '{theme}'. "
            f"Available: {AVAILABLE_THEMES}"
        )


def _apply_mpl(theme: str) -> None:
    """Apply Matplotlib style — .mplstyle file first, fallback to built-in."""
    style_path = os.path.join(_THEME_DIR, f"{theme}.mplstyle")

    if os.path.isfile(style_path) and os.path.getsize(style_path) > 0:
        try:
            _mpl.style.use(style_path)
            return
        except Exception:
            pass   # fall through to built-in

    fallback = _MPL_FALLBACKS.get(theme, "default")

    # fallback might be a file path (custom theme) or a built-in style name
    if os.path.isfile(str(fallback)):
        try:
            _mpl.style.use(fallback)
            return
        except Exception:
            pass

    try:
        _mpl.style.use(fallback)
    except Exception:
        _mpl.style.use("default")