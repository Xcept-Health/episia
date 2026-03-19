base_plotter Module
===================

Abstract base class and configuration for all Episia plotters.

This module defines the contract that every rendering backend must satisfy,
as well as configuration classes for plots and animations.

Classes
-------

Animation
^^^^^^^^^

.. autoclass:: episia.viz.plotters.base_plotter.AnimationType
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.viz.plotters.base_plotter.AnimationConfig
   :members:
   :undoc-members:
   :show-inheritance:

.. autoexception:: episia.viz.plotters.base_plotter.UnsupportedAnimationError

Plot Configuration
^^^^^^^^^^^^^^^^^^

.. autoclass:: episia.viz.plotters.base_plotter.PlotConfig
   :members:
   :undoc-members:
   :show-inheritance:

Output Format
^^^^^^^^^^^^^

.. autoclass:: episia.viz.plotters.base_plotter.OutputFormat
   :members:
   :undoc-members:
   :show-inheritance:

Base Plotter
^^^^^^^^^^^^

.. autoclass:: episia.viz.plotters.base_plotter.BasePlotter
   :members:
   :undoc-members:
   :show-inheritance:

Examples
--------

Creating a plot configuration::

    from episia.viz.plotters.base_plotter import PlotConfig, AnimationConfig

    # Basic configuration
    config = PlotConfig(
        title="COVID-19 Cases",
        xlabel="Date",
        ylabel="Count",
        width=1000,
        height=600,
        theme="scientific",
        show_grid=True
    )

    # Publication-ready configuration
    pub_config = PlotConfig.publication(
        title="Figure 1: Epidemic Curve",
        width=700,
        height=450
    )

    # Animation configuration
    anim_config = PlotConfig(
        title="Epidemic Progression",
        animation=AnimationConfig.frame_buildup(n_frames=52)
    )

Using the base plotter::

    from episia.viz.plotters.base_plotter import BasePlotter

    class CustomPlotter(BasePlotter):
        BACKEND_NAME = "custom"
        SUPPORTED_ANIMATIONS = (AnimationType.FRAME_BY_FRAME,)

        def plot_epicurve(self, result, config=None):
            # Implementation here
            pass