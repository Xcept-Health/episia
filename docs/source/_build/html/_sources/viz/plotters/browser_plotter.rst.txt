browser_plotter Module
======================

Browser export utilities for Episia.

This module provides convenience functions for exporting Plotly figures
to HTML and JSON formats for web integration.

Functions
---------

.. autofunction:: episia.viz.plotters.browser_plotter.save_html
.. autofunction:: episia.viz.plotters.browser_plotter.to_react_props
.. autofunction:: episia.viz.plotters.browser_plotter.to_json

Examples
--------

Export to standalone HTML::

    from episia.viz.plotters.browser_plotter import save_html

    fig = plotter.plot_model(result)
    path = save_html(
        fig,
        "covid_model.html",
        title="COVID-19 SEIR Model",
        include_plotlyjs=True  # Embed plotly.js (offline capable)
    )

React integration::

    from episia.viz.plotters.browser_plotter import to_react_props

    # In Python backend
    fig = plotter.plot_epicurve(result)
    props = to_react_props(fig)

    # Send to React frontend (e.g., via JSON API)
    import json
    response = json.dumps(props)

    # In React component:
    # <Plot data={props.data} layout={props.layout} config={props.config} />

JSON serialization::

    from episia.viz.plotters.browser_plotter import to_json

    # For caching or API responses
    json_str = to_json(fig, indent=2)  # Pretty printed
    
    # Store in database or send to client
    with open("figure_cache.json", "w") as f:
        f.write(json_str)