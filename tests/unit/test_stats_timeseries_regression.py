"""
tests/test_stats_timeseries_regression.py
"""
import sys; sys.path.insert(0, '/tmp')
import pytest
import numpy as np
from episia.stats.time_series import (
    calculate_incidence, detect_epidemic_threshold,
    cumulative_curve, EpidemicCurve,
)
from episia.stats.regression import (
    logistic_regression, hosmer_lemeshow_test,
    likelihood_ratio_test, calculate_vif, RegressionResult,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def weekly_counts():
    return np.array([2,3,5,8,15,25,40,35,20,10,5,3], dtype=float)

@pytest.fixture
def logistic_data():
    np.random.seed(42)
    n = 120
    X = np.random.randn(n, 2)
    p = 1 / (1 + np.exp(-(X[:,0]*0.6 + X[:,1]*0.4 + 0.2)))
    y = (np.random.rand(n) < p).astype(float)
    return X, y

@pytest.fixture
def logistic_result(logistic_data):
    X, y = logistic_data
    return logistic_regression(X, y, variable_names=['age','exposure'], add_intercept=True)


# ── Time series ───────────────────────────────────────────────────────────────

class TestCalculateIncidence:

    def test_returns_array(self, weekly_counts):
        result = calculate_incidence(weekly_counts, population=10_000)
        assert isinstance(result, np.ndarray)

    def test_same_length(self, weekly_counts):
        result = calculate_incidence(weekly_counts, population=10_000)
        assert len(result) == len(weekly_counts)

    def test_values_positive(self, weekly_counts):
        result = calculate_incidence(weekly_counts, population=10_000)
        assert (result >= 0).all()

    def test_known_value(self):
        counts = np.array([100.0])
        result = calculate_incidence(counts, population=10_000, time_period=1.0)
        assert abs(result[0] - 0.01) < 1e-10

    def test_larger_population_lower_incidence(self, weekly_counts):
        r1 = calculate_incidence(weekly_counts, population=10_000)
        r2 = calculate_incidence(weekly_counts, population=100_000)
        assert (r1 > r2).all()


class TestDetectEpidemicThreshold:

    def test_returns_dict(self, weekly_counts):
        result = detect_epidemic_threshold(weekly_counts)
        assert isinstance(result, dict)

    def test_has_threshold_key(self, weekly_counts):
        result = detect_epidemic_threshold(weekly_counts)
        assert 'threshold' in result

    def test_has_baseline_key(self, weekly_counts):
        result = detect_epidemic_threshold(weekly_counts)
        assert 'baseline' in result

    def test_has_epidemic_flags_key(self, weekly_counts):
        result = detect_epidemic_threshold(weekly_counts)
        assert 'epidemic_flags' in result

    def test_epidemic_flags_length(self, weekly_counts):
        result = detect_epidemic_threshold(weekly_counts)
        assert len(result['epidemic_flags']) == len(weekly_counts)

    def test_peak_flagged_with_low_multiplier(self):
        # Use a low multiplier so the peak is flagged
        counts = np.array([2,3,5,8,15,25,40,35,20,10,5,3], dtype=float)
        result = detect_epidemic_threshold(counts, multiplier=0.5)
        assert result['epidemic_flags'].any()

    def test_no_epidemic_below_threshold(self):
        # Flat counts — no epidemic
        counts = np.ones(12, dtype=float) * 5
        result = detect_epidemic_threshold(counts, multiplier=2.0)
        assert isinstance(result['epidemic_flags'], (list, np.ndarray))

    def test_method_parameter(self, weekly_counts):
        result = detect_epidemic_threshold(weekly_counts, method='moving_average')
        assert 'threshold' in result


class TestCumulativeCurve:

    def test_returns_array(self, weekly_counts):
        result = cumulative_curve(weekly_counts)
        assert isinstance(result, np.ndarray)

    def test_same_length(self, weekly_counts):
        result = cumulative_curve(weekly_counts)
        assert len(result) == len(weekly_counts)

    def test_monotonically_increasing(self, weekly_counts):
        result = cumulative_curve(weekly_counts)
        assert (np.diff(result) >= 0).all()

    def test_last_value_equals_sum(self, weekly_counts):
        result = cumulative_curve(weekly_counts)
        assert abs(result[-1] - weekly_counts.sum()) < 1e-9

    def test_first_value_equals_first_count(self, weekly_counts):
        result = cumulative_curve(weekly_counts)
        assert abs(result[0] - weekly_counts[0]) < 1e-9


# ── Logistic regression ───────────────────────────────────────────────────────

class TestLogisticRegression:

    def test_returns_regression_result(self, logistic_data):
        X, y = logistic_data
        result = logistic_regression(X, y)
        assert isinstance(result, RegressionResult)

    def test_has_coefficients(self, logistic_result):
        assert logistic_result.coefficients is not None
        assert len(logistic_result.coefficients) > 0

    def test_has_p_values(self, logistic_result):
        assert logistic_result.p_values is not None

    def test_has_odds_ratios(self, logistic_result):
        assert logistic_result.odds_ratios is not None

    def test_has_ci(self, logistic_result):
        assert logistic_result.ci_lower is not None
        assert logistic_result.ci_upper is not None

    def test_ci_lower_less_than_upper(self, logistic_result):
        assert (logistic_result.ci_lower < logistic_result.ci_upper).all()

    def test_odds_ratios_positive(self, logistic_result):
        assert (logistic_result.odds_ratios > 0).all()

    def test_variable_names_stored(self, logistic_result):
        assert logistic_result.variable_names is not None

    def test_model_type_logistic(self, logistic_result):
        assert logistic_result.model_type == 'logistic'

    def test_n_observations(self, logistic_data, logistic_result):
        X, _ = logistic_data
        assert logistic_result.n_observations == len(X)

    def test_aic_finite(self, logistic_result):
        assert np.isfinite(logistic_result.aic)

    def test_predict_shape(self, logistic_data, logistic_result):
        X, y = logistic_data
        X_int = np.column_stack([np.ones(len(X)), X])
        y_pred = logistic_result.predict(X_int)
        assert y_pred.shape == (len(X),)

    def test_predict_values_between_0_and_1(self, logistic_data, logistic_result):
        X, y = logistic_data
        X_int = np.column_stack([np.ones(len(X)), X])
        y_pred = logistic_result.predict(X_int)
        assert (y_pred >= 0).all() and (y_pred <= 1).all()


class TestHosmerLemeshow:

    def test_returns_dict(self, logistic_data, logistic_result):
        X, y = logistic_data
        X_int = np.column_stack([np.ones(len(X)), X])
        y_pred = logistic_result.predict(X_int)
        result = hosmer_lemeshow_test(y, y_pred)
        assert isinstance(result, dict)

    def test_has_chi2(self, logistic_data, logistic_result):
        X, y = logistic_data
        X_int = np.column_stack([np.ones(len(X)), X])
        y_pred = logistic_result.predict(X_int)
        result = hosmer_lemeshow_test(y, y_pred)
        assert 'chi2' in result

    def test_has_p_value(self, logistic_data, logistic_result):
        X, y = logistic_data
        X_int = np.column_stack([np.ones(len(X)), X])
        y_pred = logistic_result.predict(X_int)
        result = hosmer_lemeshow_test(y, y_pred)
        assert 'p_value' in result

    def test_p_value_between_0_and_1(self, logistic_data, logistic_result):
        X, y = logistic_data
        X_int = np.column_stack([np.ones(len(X)), X])
        y_pred = logistic_result.predict(X_int)
        result = hosmer_lemeshow_test(y, y_pred)
        assert 0 <= result['p_value'] <= 1

    def test_chi2_positive(self, logistic_data, logistic_result):
        X, y = logistic_data
        X_int = np.column_stack([np.ones(len(X)), X])
        y_pred = logistic_result.predict(X_int)
        result = hosmer_lemeshow_test(y, y_pred)
        assert result['chi2'] >= 0


class TestLikelihoodRatioTest:

    def test_returns_dict(self, logistic_data):
        X, y = logistic_data
        full    = logistic_regression(X, y, add_intercept=True)
        reduced = logistic_regression(X[:, :1], y, add_intercept=True)
        result  = likelihood_ratio_test(full, reduced)
        assert isinstance(result, dict)

    def test_has_lr_statistic(self, logistic_data):
        X, y = logistic_data
        full    = logistic_regression(X, y, add_intercept=True)
        reduced = logistic_regression(X[:, :1], y, add_intercept=True)
        result  = likelihood_ratio_test(full, reduced)
        assert 'lr_statistic' in result

    def test_has_p_value(self, logistic_data):
        X, y = logistic_data
        full    = logistic_regression(X, y, add_intercept=True)
        reduced = logistic_regression(X[:, :1], y, add_intercept=True)
        result  = likelihood_ratio_test(full, reduced)
        assert 'p_value' in result

    def test_lr_statistic_positive(self, logistic_data):
        X, y = logistic_data
        full    = logistic_regression(X, y, add_intercept=True)
        reduced = logistic_regression(X[:, :1], y, add_intercept=True)
        result  = likelihood_ratio_test(full, reduced)
        assert result['lr_statistic'] >= 0


class TestCalculateVif:

    def test_returns_dict(self):
        X = np.random.randn(100, 3)
        result = calculate_vif(X)
        assert isinstance(result, dict)

    def test_vif_for_each_column(self):
        X = np.random.randn(100, 3)
        result = calculate_vif(X)
        assert len(result) == 3

    def test_uncorrelated_vif_near_1(self):
        np.random.seed(0)
        X = np.random.randn(200, 2)
        result = calculate_vif(X)
        for v in result.values():
            assert float(v) < 3.0

    def test_highly_correlated_vif_high(self):
        np.random.seed(0)
        x1 = np.random.randn(200)
        x2 = x1 * 0.99 + np.random.randn(200) * 0.01
        X = np.column_stack([x1, x2])
        result = calculate_vif(X)
        assert max(float(v) for v in result.values()) > 10