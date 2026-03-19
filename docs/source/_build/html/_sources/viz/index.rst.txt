viz Module
==========

Visualization module for Episia - publication-quality plots for epidemiological analysis.

This module provides a comprehensive suite of plotting functions for epidemiological
data, including epidemic curves, model trajectories, ROC curves, forest plots,
contingency tables, and diagnostic test evaluation.

The visualization system supports two backends:
- **Plotly** (default): Interactive, web-ready figures with animation support
- **Matplotlib**: Publication-quality static figures for journals and reports

.. toctree::
   :maxdepth: 2
   :caption: Visualization Submodules:

   curves
   contingency_plot
   roc
   forest
   plotters/index
   themes/index
   utils