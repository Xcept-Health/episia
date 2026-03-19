utils Module
============

Shared utility functions for Episia visualizations.

These utilities are used internally by the viz modules but are exported
for advanced users who want to build custom plots with consistent styling.

Functions
---------

Color utilities
^^^^^^^^^^^^^^^

.. autofunction:: episia.viz.utils.hex_to_rgb
.. autofunction:: episia.viz.utils.hex_to_rgba_str
.. autofunction:: episia.viz.utils.adjust_alpha

Scale utilities
^^^^^^^^^^^^^^^

.. autofunction:: episia.viz.utils.nice_log_ticks
.. autofunction:: episia.viz.utils.symlog_range

CI band utilities
^^^^^^^^^^^^^^^^^

.. autofunction:: episia.viz.utils.ci_band_xy

Annotation utilities
^^^^^^^^^^^^^^^^^^^^

.. autofunction:: episia.viz.utils.p_value_label
.. autofunction:: episia.viz.utils.significance_stars

Figure sizing
^^^^^^^^^^^^^

.. autofunction:: episia.viz.utils.auto_height
.. autofunction:: episia.viz.utils.px_to_inches

Examples
--------

Creating consistent colors::

    from episia.viz.utils import hex_to_rgba_str

    # Convert hex to rgba with transparency
    rgba = hex_to_rgba_str("#1f77b4", alpha=0.3)
    # Returns: "rgba(31,119,180,0.3)"

Log scale ticks::

    from episia.viz.utils import nice_log_ticks

    # Generate clean ticks for range 1 to 10000
    ticks = nice_log_ticks(1, 10000)
    # Returns: [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000]

P-value formatting::

    from episia.viz.utils import p_value_label, significance_stars

    print(p_value_label(0.023))  # "p=0.023"
    print(significance_stars(0.023))  # "*"

    print(p_value_label(0.0005))  # "p<0.001"
    print(significance_stars(0.0005))  # "***"

CI band polygon::

    from episia.viz.utils import ci_band_xy

    x_poly, y_poly = ci_band_xy(
        x=time_points,
        lower=ci_lower,
        upper=ci_upper
    )
    # Ready for plotly fill="toself"