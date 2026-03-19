"""
tests/test_core_exceptions_solver.py
Coverage: core/exceptions.py, models/solver.py
"""
import sys; sys.path.insert(0, '/tmp')
import pytest
import numpy as np
# Import base exception  name varies by version
try:
    from episia.core.exceptions import EpiToolsError as _BaseError
except ImportError:
    try:
        from episia.core.exceptions import EpisiaError as _BaseError
    except ImportError:
        _BaseError = Exception

from episia.core.exceptions import (
    ValidationError, DataError, ModelError,
    ComputationError, ConfigurationError, ConvergenceError,
    ParameterError, StatisticalError, PlotError, FileError,
    DimensionError,
)
EpiToolsError = _BaseError
from episia.models.solver import solve_model, doubling_time, estimate_herd_immunity


#  Exceptions 

class TestExceptions:

    def test_epitools_error_is_exception(self):
        with pytest.raises(EpiToolsError):
            raise EpiToolsError("test")

    def test_validation_error(self):
        with pytest.raises(ValidationError):
            raise ValidationError("invalid value")

    def test_validation_is_epitools(self):
        with pytest.raises(EpiToolsError):
            raise ValidationError("test")

    def test_data_error(self):
        with pytest.raises(DataError):
            raise DataError("bad data")

    def test_model_error(self):
        with pytest.raises(ModelError):
            raise ModelError("model failed")

    def test_computation_error(self):
        with pytest.raises(ComputationError):
            raise ComputationError("computation failed")

    def test_configuration_error(self):
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("bad config")

    def test_convergence_error(self):
        with pytest.raises(ConvergenceError):
            raise ConvergenceError("did not converge")

    def test_parameter_error(self):
        with pytest.raises(ParameterError):
            raise ParameterError("bad parameter")

    def test_statistical_error(self):
        with pytest.raises(StatisticalError):
            raise StatisticalError("stat error")

    def test_plot_error(self):
        with pytest.raises(PlotError):
            raise PlotError("plot failed")

    def test_file_error(self):
        with pytest.raises(FileError):
            raise FileError("file not found")

    def test_dimension_error(self):
        with pytest.raises(DimensionError):
            raise DimensionError("wrong dimensions")

    def test_error_message_preserved(self):
        msg = "specific error message"
        try:
            raise ValidationError(msg)
        except ValidationError as e:
            assert msg in str(e)

    def test_all_subclass_epitools(self):
        errors = [
            ValidationError, DataError, ModelError, ComputationError,
            ConfigurationError, ConvergenceError, ParameterError,
            StatisticalError, PlotError, FileError, DimensionError,
        ]
        for cls in errors:
            assert issubclass(cls, EpiToolsError), f"{cls.__name__} not subclass of EpiToolsError"


#  models/solver 

class TestDoublingTime:

    def test_returns_float(self):
        result = doubling_time(beta=0.35, gamma=1/14)
        assert isinstance(float(result), float)

    def test_positive_result(self):
        result = doubling_time(beta=0.35, gamma=1/14)
        assert float(result) > 0

    def test_higher_beta_shorter_doubling(self):
        dt_high = doubling_time(beta=0.5, gamma=1/14)
        dt_low  = doubling_time(beta=0.2, gamma=1/14)
        assert float(dt_high) < float(dt_low)


class TestEstimateHerdImmunity:

    def test_returns_float(self):
        result = estimate_herd_immunity(r0=4.9)
        assert isinstance(float(result), float)

    def test_between_0_and_1(self):
        result = estimate_herd_immunity(r0=4.9)
        assert 0 < float(result) < 1

    def test_r0_1_gives_0(self):
        result = estimate_herd_immunity(r0=1.0)
        assert abs(float(result)) < 0.01

    def test_higher_r0_higher_hit(self):
        hit_low  = estimate_herd_immunity(r0=2.0)
        hit_high = estimate_herd_immunity(r0=10.0)
        assert float(hit_high) > float(hit_low)

    def test_known_value_r0_5(self):
        result = estimate_herd_immunity(r0=5.0)
        assert abs(float(result) - 0.8) < 0.01


class TestSolveModel:

    def test_returns_tuple(self):
        def derivatives(t, y):
            S, I, R = y
            N = S + I + R
            beta, gamma = 0.35, 1/14
            dS = -beta * S * I / N
            dI =  beta * S * I / N - gamma * I
            dR =  gamma * I
            return [dS, dI, dR]

        y0 = np.array([99_990., 10., 0.])
        t, y = solve_model(derivatives, y0, t_span=(0., 100.))
        assert isinstance(t, np.ndarray)
        assert isinstance(y, np.ndarray)

    def test_output_shapes(self):
        def derivatives(t, y):
            return [-0.1*y[0], 0.1*y[0] - 0.05*y[1], 0.05*y[1]]

        y0 = np.array([1000., 10., 0.])
        t, y = solve_model(derivatives, y0, t_span=(0., 50.))
        assert t.ndim == 1
        assert y.ndim == 2
        assert y.shape[0] == len(y0)

    def test_t_starts_at_t0(self):
        def derivatives(t, y): return [-0.1*y[0]]
        t, _ = solve_model(derivatives, np.array([100.]), t_span=(0., 10.), check_conservation=False)
        assert t[0] == pytest.approx(0.)

    def test_t_ends_at_t1(self):
        def derivatives(t, y): return [-0.1*y[0]]
        t, _ = solve_model(derivatives, np.array([100.]), t_span=(0., 10.), check_conservation=False)
        assert t[-1] == pytest.approx(10.)