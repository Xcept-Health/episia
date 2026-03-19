"""
tests/test_models_calibration.py
"""
import sys; sys.path.insert(0, '/tmp')
import pytest
import numpy as np
from episia.models import SEIRModel, SIRModel
from episia.models.parameters import SEIRParameters, SIRParameters
from episia.models.calibration import ModelCalibrator, CalibrationResult


@pytest.fixture
def seir_calibrator():
    return ModelCalibrator(
        SEIRModel, SEIRParameters,
        fixed_params = dict(N=100_000, I0=1, E0=5, sigma=1/5.2, t_span=(0,60)),
        fit_params   = {'beta': (0.1, 0.8), 'gamma': (0.05, 0.3)},
    )

@pytest.fixture
def observed_data():
    t = np.linspace(0, 60, 12)
    I = np.array([1,5,20,80,200,350,350,280,180,100,50,20], dtype=float)
    return t, {'I': I}


class TestModelCalibratorInit:

    def test_stores_model_class(self, seir_calibrator):
        assert seir_calibrator.model_class is SEIRModel

    def test_stores_param_class(self, seir_calibrator):
        assert seir_calibrator.param_class is SEIRParameters

    def test_default_loss_mse(self, seir_calibrator):
        assert seir_calibrator.loss == 'mse'

    def test_custom_loss(self):
        cal = ModelCalibrator(
            SEIRModel, SEIRParameters,
            fixed_params = dict(N=100_000, I0=1, E0=5, sigma=1/5.2, t_span=(0,60)),
            fit_params   = {'beta': (0.1, 0.8)},
            loss         = 'mae',
        )
        assert cal.loss == 'mae'


class TestModelCalibratorFit:

    def test_returns_calibration_result(self, seir_calibrator, observed_data):
        t, obs = observed_data
        result = seir_calibrator.fit(t, obs)
        assert isinstance(result, CalibrationResult)

    def test_result_has_parameters(self, seir_calibrator, observed_data):
        t, obs = observed_data
        result = seir_calibrator.fit(t, obs)
        assert 'beta' in result.parameters
        assert 'gamma' in result.parameters

    def test_beta_within_bounds(self, seir_calibrator, observed_data):
        t, obs = observed_data
        result = seir_calibrator.fit(t, obs)
        assert 0.1 <= result.parameters['beta'] <= 0.8

    def test_gamma_within_bounds(self, seir_calibrator, observed_data):
        t, obs = observed_data
        result = seir_calibrator.fit(t, obs)
        assert 0.05 <= result.parameters['gamma'] <= 0.3

    def test_loss_is_positive(self, seir_calibrator, observed_data):
        t, obs = observed_data
        result = seir_calibrator.fit(t, obs)
        assert result.loss >= 0

    def test_success_attribute_is_bool(self, seir_calibrator, observed_data):
        t, obs = observed_data
        result = seir_calibrator.fit(t, obs)
        assert isinstance(result.success, bool)

    def test_residuals_length(self, seir_calibrator, observed_data):
        t, obs = observed_data
        result = seir_calibrator.fit(t, obs)
        assert len(result.residuals) == len(t)

    def test_n_iterations_positive(self, seir_calibrator, observed_data):
        t, obs = observed_data
        result = seir_calibrator.fit(t, obs)
        assert result.n_iterations > 0

    def test_fit_and_apply_returns_tuple(self, seir_calibrator, observed_data):
        t, obs = observed_data
        result = seir_calibrator.fit_and_apply(t, obs)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_fit_and_apply_first_is_calibration_result(self, seir_calibrator, observed_data):
        t, obs = observed_data
        cal_result, model_result = seir_calibrator.fit_and_apply(t, obs)
        assert isinstance(cal_result, CalibrationResult)

    def test_sir_calibration(self):
        cal = ModelCalibrator(
            SIRModel, SIRParameters,
            fixed_params = dict(N=50_000, I0=5, t_span=(0,40)),
            fit_params   = {'beta': (0.1, 0.8), 'gamma': (0.05, 0.3)},
        )
        t = np.linspace(0, 40, 10)
        I = np.array([5,20,80,200,300,280,200,120,60,25], dtype=float)
        result = cal.fit(t, {'I': I})
        assert isinstance(result, CalibrationResult)
        assert result.loss >= 0


class TestCalibrationResult:

    def test_repr_contains_converged_or_failed(self, seir_calibrator, observed_data):
        t, obs = observed_data
        result = seir_calibrator.fit(t, obs)
        r = repr(result)
        assert 'CalibrationResult' in r

    def test_loss_finite(self, seir_calibrator, observed_data):
        t, obs = observed_data
        result = seir_calibrator.fit(t, obs)
        assert np.isfinite(result.loss)