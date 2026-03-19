calibration Module
==================

Parameter calibration for compartmental models.

This module provides tools to fit model parameters to observed incidence
or mortality data using scipy.optimize.minimize.

Classes
-------

.. autoclass:: episia.models.calibration.ModelCalibrator
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.models.calibration.CalibrationResult
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __repr__

Examples
--------

Fitting an SIR model to incidence data::

    import numpy as np
    from episia.models import SIRModel
    from episia.models.parameters import SIRParameters
    from episia.models.calibration import ModelCalibrator

    # Observed weekly cases
    days = np.arange(0, 140, 7)
    observed_cases = np.array([10, 25, 60, 120, 200, 280, 350, 380, 370, 300, 210, 130, 70, 30, 15, 8, 4, 2, 1, 0])

    calibrator = ModelCalibrator(
        model_class=SIRModel,
        param_class=SIRParameters,
        fixed_params={
            'N': 1_000_000,
            'I0': observed_cases[0],
            't_span': (0, 140)
        },
        fit_params={
            'beta': (0.1, 1.0),    # Search bounds
            'gamma': (0.05, 0.5)
        },
        loss='rmse'
    )

    result = calibrator.fit(
        t_observed=days,
        observed={'I': observed_cases}
    )

    print(f"Best fit: β={result.parameters['beta']:.3f}, γ={result.parameters['gamma']:.3f}")
    print(f"R₀={result.parameters['beta']/result.parameters['gamma']:.2f}")
    print(f"Loss: {result.loss:.2f}")

    # Run calibrated model
    cal_result, model_result = calibrator.fit_and_apply(days, {'I': observed_cases})
    model_result.plot().show()

Fitting multiple compartments (SEIRD)::

    # Fit to both cases and deaths
    calibrator = ModelCalibrator(
        model_class=SEIRDModel,
        param_class=SEIRDParameters,
        fixed_params={'N': 1e6, 'I0': 10, 'E0': 50, 't_span': (0, 200)},
        fit_params={
            'beta': (0.1, 1.0),
            'mu': (0.001, 0.1)    # Mortality rate
        }
    )

    result = calibrator.fit(
        t_observed=days,
        observed={
            'I': observed_cases,
            'D': observed_deaths
        }
    )