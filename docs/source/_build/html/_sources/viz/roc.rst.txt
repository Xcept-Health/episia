roc Module
==========

ROC curve visualizations.

This module provides functions for plotting ROC curves, comparing multiple
models, and precision-recall curves for imbalanced datasets.

Functions
---------

.. autofunction:: episia.viz.roc.plot_roc
.. autofunction:: episia.viz.roc.plot_roc_compare
.. autofunction:: episia.viz.roc.plot_precision_recall

Examples
--------

Single ROC curve::

    from episia.stats.diagnostic import roc_analysis
    from episia.viz.roc import plot_roc

    # Perform ROC analysis
    roc_result = roc_analysis(y_true, y_scores)

    # Plot with AUC annotation
    fig = plot_roc(roc_result, title="Diagnostic Test Performance")
    fig.show()

Animated ROC curve::

    # Animated threshold sweep
    fig = plot_roc(
        roc_result,
        animate=True,
        title="ROC Curve - Threshold Sweep"
    )

Comparing multiple models::

    from episia.viz.roc import plot_roc_compare

    models = [roc_logistic, roc_rf, roc_xgb]
    labels = ["Logistic Regression", "Random Forest", "XGBoost"]

    fig = plot_roc_compare(
        models,
        labels=labels,
        title="Model Comparison - ROC Curves"
    )

Precision-recall curve::

    from episia.viz.roc import plot_precision_recall

    fig = plot_precision_recall(
        y_true,
        y_scores,
        label="Logistic Regression",
        title="Precision-Recall Curve (Imbalanced Data)"
    )