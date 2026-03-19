diagnostic Module
=================

Diagnostic test performance evaluation.

This module provides functions for calculating diagnostic test
performance measures: sensitivity, specificity, predictive values,
likelihood ratios, and ROC curve analysis.

Classes
-------

.. autoclass:: episia.stats.diagnostic.DiagnosticMeasure
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.stats.diagnostic.DiagnosticResult
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __repr__

.. autoclass:: episia.stats.diagnostic.ROCResult
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __repr__

Functions
---------

.. autofunction:: episia.stats.diagnostic.diagnostic_test_2x2
.. autofunction:: episia.stats.diagnostic.diagnostic_from_data
.. autofunction:: episia.stats.diagnostic.roc_analysis
.. autofunction:: episia.stats.diagnostic.likelihood_ratio_ci
.. autofunction:: episia.stats.diagnostic.predictive_values_from_sens_spec
.. autofunction:: episia.stats.diagnostic.fagan_nomogram
.. autofunction:: episia.stats.diagnostic.diagnostic_accuracy_ci
.. autofunction:: episia.stats.diagnostic.compare_diagnostic_tests
.. autofunction:: episia.stats.diagnostic.optimal_threshold_grid_search

Examples
--------

Basic diagnostic test evaluation::

    from episia.stats.diagnostic import diagnostic_test_2x2

    # True positives, False positives, False negatives, True negatives
    result = diagnostic_test_2x2(tp=80, fp=20, fn=10, tn=90)

    print(f"Sensitivity: {result.sensitivity:.3f}")
    print(f"Specificity: {result.specificity:.3f}")
    print(f"PPV: {result.ppv:.3f}")
    print(f"NPV: {result.npv:.3f}")
    print(f"LR+: {result.lr_positive:.3f}")
    print(f"LR-: {result.lr_negative:.3f}")

    # Summary
    print(result.summary())

ROC curve analysis::

    import numpy as np
    from episia.stats.diagnostic import roc_analysis

    # True labels and predicted probabilities
    y_true = np.array([1, 1, 0, 0, 1, 0, 1, 0])
    y_score = np.array([0.9, 0.8, 0.3, 0.2, 0.7, 0.4, 0.6, 0.1])

    roc = roc_analysis(y_true, y_score, method='youden')
    print(roc)
    print(f"AUC: {roc.auc:.3f}")
    print(f"Optimal threshold: {roc.optimal_threshold:.3f}")
    
    # Plot ROC curve
    roc.plot().show()

Fagan's nomogram::

    from episia.stats.diagnostic import fagan_nomogram

    # Pre-test probability 20%, LR+ = 10
    post_prob = fagan_nomogram(pre_test_prob=0.2, lr=10)
    print(f"Post-test probability: {post_prob:.1%}")

Comparing two tests::

    result1 = diagnostic_test_2x2(tp=80, fp=20, fn=10, tn=90)
    result2 = diagnostic_test_2x2(tp=75, fp=15, fn=15, tn=95)
    
    comparison = compare_diagnostic_tests(result1, result2)
    print(f"Sensitivity difference: {comparison['sensitivity_difference']:.3f}")