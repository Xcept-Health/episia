regression Module
=================

Regression models for epidemiological analysis.

This module provides functions for fitting and interpreting
regression models commonly used in epidemiology, including
logistic regression for binary outcomes and Poisson regression
for count data.

Classes
-------

.. autoclass:: episia.stats.regression.RegressionType
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.stats.regression.ModelSelection
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.stats.regression.RegressionResult
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __repr__

Functions
---------

.. autofunction:: episia.stats.regression.logistic_regression
.. autofunction:: episia.stats.regression.poisson_regression
.. autofunction:: episia.stats.regression.likelihood_ratio_test
.. autofunction:: episia.stats.regression.hosmer_lemeshow_test
.. autofunction:: episia.stats.regression.calculate_vif
.. autofunction:: episia.stats.regression.stepwise_selection
.. autofunction:: episia.stats.regression.roc_auc_from_logistic
.. autofunction:: episia.stats.regression.interaction_term

Examples
--------

Logistic regression::

    import numpy as np
    from episia.stats.regression import logistic_regression

    # Data: exposure, age, outcome
    X = np.array([[1, 25], [1, 30], [1, 35], [0, 40], [0, 45], [0, 50]])
    y = np.array([1, 1, 0, 0, 0, 1])

    result = logistic_regression(
        X, y,
        variable_names=['exposed', 'age'],
        add_intercept=True
    )

    print(result.summary())
    
    # Extract odds ratios
    for i, var in enumerate(result.variable_names):
        print(f"{var}: OR={result.odds_ratios[i]:.2f} "
              f"(95% CI: {result.ci_lower[i]:.2f}-{result.ci_upper[i]:.2f})")

Poisson regression::

    from episia.stats.regression import poisson_regression

    # Count data with offset (log person-time)
    X = np.array([[1, 0], [1, 1], [0, 0], [0, 1]])
    y = np.array([5, 12, 3, 8])
    offset = np.log([100, 100, 100, 100])  # person-time

    result = poisson_regression(
        X, y, offset=offset,
        variable_names=['exposed', 'age']
    )
    print(result.summary())

Likelihood ratio test::

    from episia.stats.regression import likelihood_ratio_test

    # Full model vs reduced model
    lrt = likelihood_ratio_test(full_model, reduced_model)
    print(f"LR test: χ²={lrt['lr_statistic']:.3f}, p={lrt['p_value']:.4f}")

Multicollinearity check::

    vif = calculate_vif(X)
    for var, value in vif.items():
        print(f"{var}: VIF={value:.2f}")