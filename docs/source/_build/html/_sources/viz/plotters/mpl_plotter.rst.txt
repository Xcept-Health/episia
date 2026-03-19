mpl_plotter Module
==================

Matplotlib rendering backend for Episia.

This backend produces publication-quality static figures suitable for
journals, theses, and reports. No animations are supported.

Class
-----

.. autoclass:: episia.viz.plotters.mpl_plotter.MatplotlibPlotter
   :members:
   :undoc-members:
   :show-inheritance:

Examples
--------

Basic usage::

    from episia.viz.plotters import get_plotter

    # Get Matplotlib backend
    plotter = get_plotter("matplotlib")

    # Create publication-quality figure
    fig = plotter.plot_roc(result)
    
    # Save at high resolution
    plotter.save(fig, "roc_curve.pdf", dpi=300)

Journal-ready figures::

    from episia.viz.plotters.base_plotter import PlotConfig

    # Configure for journal submission
    config = PlotConfig.publication(
        title="Figure 2: ROC Curve Analysis",
        width=700,
        height=500
    )

    fig = plotter.plot_forest(result, config=config)
    plotter.save(fig, "forest_plot.svg")  # Vector format

Multiple panels::

    # Create multi-panel figure (requires manual subplot handling)
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot on first subplot
    plotter.plot_model(result, config=PlotConfig(width=600, height=400))
    # Manual subplot management needed for complex layouts

Supported formats::

    from episia.viz.plotters.base_plotter import OutputFormat

    # All standard formats supported
    plotter.save(fig, "output.png", fmt=OutputFormat.PNG)   # Raster
    plotter.save(fig, "output.svg", fmt=OutputFormat.SVG)   # Vector
    plotter.save(fig, "output.pdf", fmt=OutputFormat.PDF)   # Vector