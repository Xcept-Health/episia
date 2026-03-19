plotly_plotter Module
=====================

Plotly rendering backend for Episia.

This is the default backend, producing interactive HTML figures suitable for
notebooks, web applications, and standalone HTML exports.

Class
-----

.. autoclass:: episia.viz.plotters.plotly_plotter.PlotlyPlotter
   :members:
   :undoc-members:
   :show-inheritance:

Animation Support
-----------------

The Plotly backend supports:

- **FRAME_BY_FRAME**: Bars/build-up for epidemic curves and forest plots
- **CONTINUOUS**: Smooth line drawing for model trajectories and ROC curves
- **PLAY_PAUSE**: Auto-play with controls
- **SLIDER**: Interactive time slider for model simulations

Examples
--------

Basic usage::

    from episia.viz.plotters import get_plotter

    # Get Plotly backend (default)
    plotter = get_plotter("plotly")

    # Plot with default settings
    fig = plotter.plot_epicurve(result)
    fig.show()

    # Plot with custom configuration
    from episia.viz.plotters.base_plotter import PlotConfig

    config = PlotConfig.dark(title="Ebola Outbreak 2014")
    fig = plotter.plot_model(result, config=config)

Animated plots::

    from episia.viz.plotters.base_plotter import AnimationConfig

    # Create animated epidemic curve
    anim_config = PlotConfig(
        title="Weekly Cases Buildup",
        animation=AnimationConfig.frame_buildup(n_frames=52)
    )
    fig = plotter.plot_epicurve(result, config=anim_config)

    # Smooth trajectory animation
    smooth_config = PlotConfig(
        title="SEIR Model Simulation",
        animation=AnimationConfig.smooth(duration_ms=5000)
    )
    fig = plotter.plot_model(result, config=smooth_config)

Saving figures::

    from episia.viz.plotters.base_plotter import OutputFormat

    # Save as interactive HTML
    plotter.save(fig, "output.html", fmt=OutputFormat.HTML)

    # Save as static image (requires kaleido)
    plotter.save(fig, "figure", fmt=OutputFormat.PNG, dpi=300)

Web integration::

    # Serialize for React/JavaScript
    import json
    fig_json = fig.to_json()
    
    # Or use browser utilities
    from episia.viz.plotters.browser_plotter import to_react_props

    props = to_react_props(fig)
    # Pass props['data'] and props['layout'] to react-plotly.js