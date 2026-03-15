"""
viz/utils.py - Shared utility functions for EpiTools visualizations.

Internal helpers used across viz modules. Not part of the public API
but exported for advanced users who want to build custom plots.
"""

from __future__ import annotations

from typing import List, Optional, Tuple, Union

import numpy as np



# Colour utilities

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert '#rrggbb' to (r, g, b) tuple."""
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def hex_to_rgba_str(hex_color: str, alpha: float = 1.0) -> str:
    """Convert '#rrggbb' to 'rgba(r,g,b,a)' string for Plotly."""
    r, g, b = hex_to_rgb(hex_color)
    return f"rgba({r},{g},{b},{alpha})"


def adjust_alpha(hex_color: str, alpha: float) -> str:
    """Return rgba string with given alpha  convenience wrapper."""
    return hex_to_rgba_str(hex_color, alpha)



# Scale / axis helpers

def nice_log_ticks(vmin: float, vmax: float) -> List[float]:
    """
    Generate clean tick values for a log-scale axis.

    Args:
        vmin: Minimum positive value.
        vmax: Maximum positive value.

    Returns:
        List of tick values (powers of 10 with optional midpoints).
    """
    if vmin <= 0:
        vmin = 1e-6
    lo = int(np.floor(np.log10(vmin)))
    hi = int(np.ceil(np.log10(vmax)))
    ticks = []
    for exp in range(lo, hi + 1):
        ticks.append(10 ** exp)
        if exp < hi:
            ticks.append(2 * 10 ** exp)
            ticks.append(5 * 10 ** exp)
    return sorted(set(t for t in ticks if vmin <= t <= vmax))


def symlog_range(values: np.ndarray, margin: float = 0.05) -> Tuple[float, float]:
    """
    Return (min, max) range for an axis with symmetric margin.

    Args:
        values: Data values.
        margin: Fractional margin to add on each side.

    Returns:
        (axis_min, axis_max) tuple.
    """
    vmin, vmax = float(np.nanmin(values)), float(np.nanmax(values))
    span = vmax - vmin
    pad  = span * margin if span > 0 else abs(vmin) * margin or 0.1
    return vmin - pad, vmax + pad



# Confidence interval band helper

def ci_band_xy(
    x: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
) -> Tuple[List, List]:
    """
    Build (x_filled, y_filled) lists for a filled CI band (Plotly toself).

    Args:
        x:     Time / x-axis values.
        lower: Lower CI bound.
        upper: Upper CI bound.

    Returns:
        (x_poly, y_poly) for go.Scatter(fill='toself').
    """
    x_poly = list(x) + list(x[::-1])
    y_poly = list(upper) + list(lower[::-1])
    return x_poly, y_poly



# Annotation helpers

def p_value_label(p: Optional[float]) -> str:
    """
    Format a p-value as a readable string.

        p < 0.001  → 'p<0.001'
        p < 0.01   → 'p<0.01'
        p < 0.05   → 'p<0.05'
        p >= 0.05  → 'NS (p=x.xxx)'
    """
    if p is None:
        return ""
    if p < 0.001:
        return "p<0.001"
    if p < 0.01:
        return "p<0.01"
    if p < 0.05:
        return f"p={p:.3f}"
    return f"NS (p={p:.3f})"


def significance_stars(p: Optional[float]) -> str:
    """
    Return significance stars for a p-value.

        p < 0.001 → '***'
        p < 0.01  → '**'
        p < 0.05  → '*'
        else      → 'ns'
    """
    if p is None:
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"



# Figure sizing

def auto_height(n_rows: int, row_px: int = 36, min_px: int = 300,
                max_px: int = 900) -> int:
    """
    Calculate a sensible figure height for n_rows of data.

    Args:
        n_rows:  Number of data rows / strata.
        row_px:  Pixels per row.
        min_px:  Minimum figure height.
        max_px:  Maximum figure height.

    Returns:
        Height in pixels.
    """
    return max(min_px, min(max_px, n_rows * row_px + 120))


def px_to_inches(px: int, dpi: int = 100) -> float:
    """Convert pixels to inches for Matplotlib figure sizing."""
    return px / dpi



# Exports

__all__ = [
    "hex_to_rgb",
    "hex_to_rgba_str",
    "adjust_alpha",
    "nice_log_ticks",
    "symlog_range",
    "ci_band_xy",
    "p_value_label",
    "significance_stars",
    "auto_height",
    "px_to_inches",
]