registry Module
===============

Theme registry and management for Episia.

This module maintains the global theme state and provides functions for
getting/setting themes, retrieving color palettes, and registering custom themes.

Functions
---------

.. autofunction:: episia.viz.themes.registry.set_theme
.. autofunction:: episia.viz.themes.registry.get_theme
.. autofunction:: episia.viz.themes.registry.get_available_themes
.. autofunction:: episia.viz.themes.registry.get_palette
.. autofunction:: episia.viz.themes.registry.get_plotly_layout
.. autofunction:: episia.viz.themes.registry.apply_mpl_theme
.. autofunction:: episia.viz.themes.registry.register_theme

Data
----

.. autodata:: episia.viz.themes.registry.AVAILABLE_THEMES

Built-in Themes
---------------

.. list-table::
   :header-rows: 1

   * - Theme Name
     - Description
     - Use Case
   * - ``scientific``
     - Clean, high-contrast
     - Default, general purpose
   * - ``minimal``
     - No grid, maximum whitespace
     - Minimalist dashboards
   * - ``dark``
     - Dark background
     - Night mode, presentations
   * - ``colorblind``
     - Accessible palette
     - Colorblind-safe publications

Examples
--------

Basic theme usage::

    from episia.viz.themes import set_theme, get_available_themes

    # Check available themes
    print(get_available_themes())
    # ['scientific', 'minimal', 'dark', 'colorblind']

    # Set theme globally
    set_theme("dark")

    # All subsequent plots will use dark theme
    fig = plot_epicurve(result)  # Uses dark theme

    # Get current theme
    current = get_theme()
    print(current)  # 'dark'

Getting color palettes::

    from episia.viz.themes import get_palette

    # Get palette for specific theme
    colors = get_palette("colorblind")
    print(colors)
    # ['#0072B2', '#E69F00', '#56B4E9', '#009E73', '#F0E442', '#D55E00', ...]

    # Use in custom plots
    import matplotlib.pyplot as plt
    for i, color in enumerate(colors[:3]):
        plt.plot(x, y[i], color=color)

Registering custom themes::

    from episia.viz.themes import register_theme, set_theme

    # Register institutional theme
    register_theme(
        name="xcept_health",
        palette=["#0d6efd", "#dc3545", "#198754", "#ffc107", "#6c757d"],
        mplstyle_path="/path/to/custom.mplstyle",  # optional
        bg_paper="#f8f9fa",
        bg_plot="#ffffff",
        font_color="#212529"
    )

    # Use it immediately
    set_theme("xcept_health")

Applying theme manually::

    from episia.viz.themes import apply_mpl_theme

    # Apply theme to current matplotlib session
    apply_mpl_theme("scientific")

    # All subsequent matplotlib commands use the theme
    import matplotlib.pyplot as plt
    plt.plot(x, y)  # Uses scientific theme styling

Plotly layout extraction::

    from episia.viz.themes import get_plotly_layout

    # Get base layout dict for theme
    layout = get_plotly_layout("minimal")

    # Use in custom Plotly figures
    import plotly.graph_objects as go
    fig = go.Figure(data=data, layout=layout)