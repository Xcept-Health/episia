"""
viz/plotters/browser_plotter.py - Browser export utilities for Episia.

Not a full backend. PlotlyPlotter handles all rendering.
This module provides convenience functions to export Plotly figures
as standalone HTML files or JSON for embedding in React / web frontends.

Usage::

    from episia.viz.plotters.browser_plotter import save_html, to_react_props

    fig = plotter.plot_model(result)
    save_html(fig, "outbreak_model.html")

    # React integration
    props = to_react_props(fig)
    # Pass props["data"] and props["layout"] to <Plot /> from react-plotly.js
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional


def save_html(
    fig: Any,
    path: str,
    title: str = "Episia Figure",
    include_plotlyjs: bool = True,
    full_html: bool = True,
) -> str:
    """
    Export a Plotly figure as a standalone HTML file.

    Args:
        fig:             plotly.graph_objects.Figure instance.
        path:            Destination path (.html appended if missing).
        title:           HTML page <title>.
        include_plotlyjs: Embed plotly.js bundle (larger file, fully offline).
                         Set False to load from CDN (smaller, needs internet).
        full_html:       Wrap in full <html> document (True) or div only (False).

    Returns:
        Absolute path to the written file.
    """
    if not path.endswith(".html"):
        path = path + ".html"
    path = os.path.abspath(path)

    html = fig.to_html(
        full_html=full_html,
        include_plotlyjs="cdn" if not include_plotlyjs else True,
        config={"responsive": True, "displaylogo": False},
    )

    # Inject custom title
    if full_html and title:
        html = html.replace("<title>", f"<title>{title}  ", 1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    return path


def to_react_props(fig: Any) -> Dict[str, Any]:
    """
    Serialize a Plotly figure into props for react-plotly.js <Plot />.

    Returns a dict with keys:
        "data"    list of trace dicts
        "layout"  layout dict
        "config"  recommended config dict

    Usage in React::

        import Plot from 'react-plotly.js';
        const props = await fetchEpisiaProps('/api/plot/epicurve');
        <Plot data={props.data} layout={props.layout} config={props.config} />

    Args:
        fig: plotly.graph_objects.Figure instance.

    Returns:
        Dict with "data", "layout", "config".
    """
    fig_dict = json.loads(fig.to_json())
    return {
        "data":   fig_dict.get("data", []),
        "layout": fig_dict.get("layout", {}),
        "config": {
            "responsive":   True,
            "displaylogo":  False,
            "modeBarButtonsToRemove": ["sendDataToCloud", "lasso2d"],
        },
    }


def to_json(fig: Any, indent: Optional[int] = None) -> str:
    """
    Serialize a Plotly figure to a JSON string.

    Useful for REST API responses or caching.

    Args:
        fig:    plotly.graph_objects.Figure instance.
        indent: JSON indentation (None for compact).

    Returns:
        JSON string.
    """
    if indent is None:
        return fig.to_json()
    return json.dumps(json.loads(fig.to_json()), indent=indent)


__all__ = ["save_html", "to_react_props", "to_json"]