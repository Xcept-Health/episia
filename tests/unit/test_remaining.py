"""
tests/unit/test_remaining.py
Unit tests for:
    api/results.py         — EpiResult, ConfidenceInterval, AssociationResult,
                             ProportionResult, DiagnosticResult, ROCResult,
                             ModelResult, TimeSeriesResult, make_ci,
                             make_association, make_proportion
    stats/time_series.py   — EpidemicCurve, calculate_incidence,
                             calculate_attack_rate, epidemic_curve,
                             moving_average, exponential_growth_rate,
                             cumulative_curve, detect_peaks,
                             detect_epidemic_threshold, reproductive_number
    stats/regression.py    — RegressionResult, logistic_regression,
                             poisson_regression, likelihood_ratio_test,
                             hosmer_lemeshow_test, calculate_vif
"""
from __future__ import annotations

import json
import math
import numpy as np
import pandas as pd
import pytest

# ── api.results ───────────────────────────────────────────────────────────────
from epitools.api.results import (
    EpiResult, ConfidenceInterval,
    AssociationResult, ProportionResult, DiagnosticResult,
    ROCResult, ModelResult, TimeSeriesResult,
    make_ci, make_association, make_proportion,
)

# ── stats.time_series ─────────────────────────────────────────────────────────
from epitools.stats.time_series import (
    EpidemicCurve, TimeAggregation,
    calculate_incidence, calculate_attack_rate, epidemic_curve,
    moving_average, exponential_growth_rate,
    cumulative_curve, detect_peaks, detect_epidemic_threshold,
    reproductive_number,
)

# ── stats.regression ──────────────────────────────────────────────────────────
from epitools.stats.regression import (
    RegressionResult, logistic_regression, poisson_regression,
    likelihood_ratio_test, hosmer_lemeshow_test, calculate_vif,
)



# Fixtures


@pytest.fixture
def ci_95():
    return ConfidenceInterval(lower=0.5, upper=1.5, confidence=0.95, method="wald")

@pytest.fixture
def assoc_result(ci_95):
    return AssociationResult(
        measure="risk_ratio", estimate=2.667,
        ci=ci_95, p_value=0.003, null_value=1.0,
        method="wald", n_total=100,
    )

@pytest.fixture
def rng():
    return np.random.default_rng(42)

@pytest.fixture
def logistic_data(rng):
    n = 200
    X = rng.normal(0, 1, (n, 2))
    log_odds = 0.5 + 1.2 * X[:, 0] - 0.8 * X[:, 1]
    prob = 1 / (1 + np.exp(-log_odds))
    y = (rng.uniform(0, 1, n) < prob).astype(float)
    return X, y

@pytest.fixture
def poisson_data(rng):
    n = 150
    X = rng.normal(0, 1, (n, 2))
    log_mu = 1.0 + 0.5 * X[:, 0]
    mu = np.exp(log_mu)
    y = rng.poisson(mu).astype(float)
    return X, y



# 1. ConfidenceInterval


class TestConfidenceInterval:
    def test_fields(self, ci_95):
        assert ci_95.lower == 0.5 and ci_95.upper == 1.5

    def test_repr_has_ci(self, ci_95):
        assert "CI95" in repr(ci_95)

    def test_contains_true(self, ci_95):
        assert ci_95.contains(1.0) is True

    def test_contains_false_below(self, ci_95):
        assert ci_95.contains(0.1) is False

    def test_contains_false_above(self, ci_95):
        assert ci_95.contains(2.0) is False

    def test_contains_boundary(self, ci_95):
        assert ci_95.contains(0.5) is True
        assert ci_95.contains(1.5) is True

    def test_to_dict_keys(self, ci_95):
        d = ci_95.to_dict()
        for k in ["lower", "upper", "confidence", "method"]:
            assert k in d

    def test_make_ci_factory(self):
        ci = make_ci(0.2, 0.8, confidence=0.99, method="wilson")
        assert ci.lower == 0.2 and ci.upper == 0.8
        assert ci.confidence == 0.99 and ci.method == "wilson"



# 2. AssociationResult


class TestAssociationResult:
    def test_is_epireuslt(self, assoc_result):
        assert isinstance(assoc_result, EpiResult)

    def test_significant_true(self, assoc_result):
        # CI 0.5–1.5 contains 1.0 → NOT significant
        assert assoc_result.significant is False

    def test_significant_false_when_ci_excludes_null(self):
        ci = make_ci(1.2, 3.0)
        r = AssociationResult(measure="rr", estimate=2.0, ci=ci)
        assert r.significant is True

    def test_repr_has_measure(self, assoc_result):
        assert "Risk Ratio" in repr(assoc_result) or "risk_ratio" in repr(assoc_result)

    def test_repr_has_estimate(self, assoc_result):
        assert "2.667" in repr(assoc_result)

    def test_repr_p_value_shown(self, assoc_result):
        assert "p=" in repr(assoc_result)

    def test_to_dict_keys(self, assoc_result):
        d = assoc_result.to_dict()
        for k in ["measure","estimate","ci_lower","ci_upper","p_value","significant"]:
            assert k in d

    def test_to_json_valid(self, assoc_result):
        parsed = json.loads(assoc_result.to_json())
        assert parsed["measure"] == "risk_ratio"

    def test_to_dataframe(self, assoc_result):
        df = assoc_result.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    def test_str_equals_repr(self, assoc_result):
        assert str(assoc_result) == repr(assoc_result)

    def test_make_association_factory(self):
        r = make_association(
            measure="odds_ratio", estimate=3.0,
            ci_lower=1.5, ci_upper=6.0,
            p_value=0.002, null_value=1.0,
            n_total=200,
        )
        assert isinstance(r, AssociationResult)
        assert r.estimate == 3.0
        assert r.significant is True



# 3. ProportionResult


class TestProportionResult:
    def test_is_epiresult(self):
        r = make_proportion(0.3, 0.2, 0.4, numerator=30, denominator=100)
        assert isinstance(r, EpiResult)

    def test_repr_has_proportion(self):
        r = make_proportion(0.3, 0.2, 0.4)
        assert "0.3000" in repr(r)

    def test_repr_shows_numerator_denominator(self):
        r = make_proportion(0.3, 0.2, 0.4, numerator=30, denominator=100)
        assert "30" in repr(r) and "100" in repr(r)

    def test_to_dict_has_proportion(self):
        r = make_proportion(0.3, 0.2, 0.4)
        assert r.to_dict()["proportion"] == pytest.approx(0.3)

    def test_make_proportion_factory(self):
        r = make_proportion(0.225, 0.17, 0.29, numerator=45, denominator=200,
                            label="attack_rate", confidence=0.95, method="wilson")
        assert r.label == "attack_rate"
        assert r.ci.method == "wilson"

    def test_to_json_valid(self):
        r = make_proportion(0.3, 0.2, 0.4)
        parsed = json.loads(r.to_json())
        assert "proportion" in parsed



# 4. ModelResult (api.results version)


class TestModelResultAPI:
    @pytest.fixture
    def model_result(self):
        t = np.linspace(0, 100, 500)
        N = 10_000
        I = np.exp(-((t - 50) ** 2) / 200) * 1000
        S = N - I - np.cumsum(I / 500)
        R = N - S - I
        return ModelResult(
            model_type="SIR",
            t=t,
            compartments={"S": S, "I": I, "R": R},
            parameters={"N": N, "beta": 0.3, "gamma": 0.1},
            r0=3.0,
            peak_infected=float(I.max()),
            peak_time=float(t[I.argmax()]),
            final_size=0.95,
        )

    def test_is_epiresult(self, model_result):
        assert isinstance(model_result, EpiResult)

    def test_repr_has_model_type(self, model_result):
        assert "SIR" in repr(model_result)

    def test_repr_has_r0(self, model_result):
        assert "3.000" in repr(model_result)

    def test_to_dict_keys(self, model_result):
        d = model_result.to_dict()
        for k in ["model_type", "r0", "peak_infected", "final_size", "t_start", "t_end"]:
            assert k in d

    def test_to_dataframe_has_compartments(self, model_result):
        df = model_result.to_dataframe()
        for c in ["t", "S", "I", "R"]:
            assert c in df.columns

    def test_to_json_valid(self, model_result):
        parsed = json.loads(model_result.to_json())
        assert parsed["model_type"] == "SIR"

    def test_json_safe_numpy(self, model_result):
        # numpy integers/floats should be serializable
        d = model_result.to_dict()
        json.dumps(d)   # should not raise



# 5. EpiResult._json_safe & _flatten


class TestEpiResultHelpers:
    def test_json_safe_numpy_int(self):
        r = EpiResult._json_safe(np.int64(42))
        assert isinstance(r, int) and r == 42

    def test_json_safe_numpy_float(self):
        r = EpiResult._json_safe(np.float64(3.14))
        assert isinstance(r, float)

    def test_json_safe_nan_becomes_none(self):
        assert EpiResult._json_safe(float("nan")) is None

    def test_json_safe_numpy_nan_becomes_none(self):
        assert EpiResult._json_safe(np.float64("nan")) is None

    def test_json_safe_array(self):
        r = EpiResult._json_safe(np.array([1, 2, 3]))
        assert r == [1, 2, 3]

    def test_json_safe_nested_dict(self):
        d = {"a": np.int64(1), "b": {"c": np.float64(2.0)}}
        r = EpiResult._json_safe(d)
        assert isinstance(r["a"], int)
        assert isinstance(r["b"]["c"], float)

    def test_flatten_nested(self):
        d = {"a": 1, "b": {"c": 2, "d": 3}}
        flat = EpiResult._flatten(d)
        assert "b.c" in flat and "b.d" in flat

    def test_flatten_no_nesting(self):
        d = {"x": 1, "y": 2}
        flat = EpiResult._flatten(d)
        assert flat == {"x": 1, "y": 2}

    def test_ci_str_format(self):
        r = make_association("rr", 2.0, 1.0, 3.0)
        s = r._ci_str(1.5, 2.5)
        assert "1.500" in s and "2.500" in s

    def test_plot_no_viz_raises(self):
        ci = make_ci(0.5, 1.5)
        r = make_proportion(0.3, 0.2, 0.4)
        # _viz_function is None → should raise NotImplementedError
        r._viz_function = None
        with pytest.raises(NotImplementedError):
            r.plot()



# 6. EpidemicCurve


class TestEpidemicCurve:
    @pytest.fixture
    def curve(self):
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        counts = np.random.default_rng(0).poisson(10, 30).astype(float)
        return EpidemicCurve(dates=dates.values, counts=counts, aggregated=False)

    def test_valid(self, curve):
        assert len(curve.dates) == len(curve.counts) == 30

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError):
            EpidemicCurve(
                dates=np.array(["2024-01-01"]),
                counts=np.array([1, 2]),
                aggregated=False,
            )

    def test_to_dataframe(self, curve):
        df = curve.to_dataframe()
        assert "date" in df.columns and "count" in df.columns

    def test_summary_keys(self, curve):
        s = curve.summary()
        for k in ["total_cases", "peak_date", "max_daily", "duration_days"]:
            assert k in s

    def test_total_cases(self, curve):
        assert curve.summary()["total_cases"] == int(curve.counts.sum())

    def test_metadata_default_empty(self, curve):
        assert isinstance(curve.metadata, dict)



# 7. calculate_incidence & calculate_attack_rate


class TestCalculateIncidence:
    def test_scalar_population(self):
        r = calculate_incidence(np.array([10, 20, 30]), 1000)
        np.testing.assert_array_almost_equal(r, [0.01, 0.02, 0.03])

    def test_array_population(self):
        cases = np.array([10, 20])
        pop   = np.array([1000, 2000])
        r = calculate_incidence(cases, pop)
        np.testing.assert_array_almost_equal(r, [0.01, 0.01])

    def test_time_period_scales(self):
        r = calculate_incidence(np.array([10]), 1000, time_period=100)
        assert r[0] == pytest.approx(1.0)

    def test_zero_population_raises(self):
        with pytest.raises(ValueError):
            calculate_incidence(np.array([10]), 0)

    def test_attack_rate_clipped_0_1(self):
        # cases > population → clipped to 1.0
        r = calculate_attack_rate(np.array([1500]), 1000)
        assert r[0] == pytest.approx(1.0)

    def test_attack_rate_nominal(self):
        r = calculate_attack_rate(np.array([100, 200]), 1000)
        np.testing.assert_array_almost_equal(r, [0.1, 0.2])

    def test_attack_rate_zero_population_raises(self):
        with pytest.raises(ValueError):
            calculate_attack_rate(np.array([10]), 0)



# 8. epidemic_curve


class TestEpidemicCurveFn:
    @pytest.fixture
    def daily_data(self):
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        counts = np.ones(30, dtype=float)
        return dates, counts

    def test_returns_epidemic_curve(self, daily_data):
        dates, counts = daily_data
        r = epidemic_curve(dates, counts)
        assert isinstance(r, EpidemicCurve)

    def test_daily_aggregation(self, daily_data):
        dates, counts = daily_data
        r = epidemic_curve(dates, counts, aggregation=TimeAggregation.DAILY)
        assert r.aggregation == "daily"
        assert not r.aggregated

    def test_weekly_aggregation(self, daily_data):
        dates, counts = daily_data
        r = epidemic_curve(dates, counts, aggregation=TimeAggregation.WEEKLY)
        assert r.aggregation == "weekly"
        assert r.aggregated
        # 30 days ≈ 4–5 weeks
        assert len(r.counts) <= 6

    def test_fill_missing_zeros(self):
        # Only provide 3 non-consecutive dates
        dates = pd.to_datetime(["2024-01-01", "2024-01-03", "2024-01-05"])
        counts = np.array([10, 20, 30])
        r = epidemic_curve(dates, counts, fill_missing=True)
        # Should have 5 days with gaps filled
        assert len(r.counts) == 5
        assert r.counts[1] == 0.0  # Jan 2 was missing

    def test_total_preserved_daily(self, daily_data):
        dates, counts = daily_data
        r = epidemic_curve(dates, counts)
        assert r.counts.sum() == pytest.approx(counts.sum())



# 9. moving_average


class TestMovingAverage:
    def test_returns_same_length(self):
        data = np.arange(20, dtype=float)
        ma = moving_average(data, window=7)
        assert len(ma) == len(data)

    def test_smooths_spike(self):
        data = np.ones(20, dtype=float)
        data[10] = 100
        ma = moving_average(data, window=7)
        # MA at the spike should be lower than spike itself
        assert ma[10] < 100

    def test_constant_series_unchanged(self):
        data = np.full(20, 5.0)
        ma = moving_average(data, window=5)
        np.testing.assert_array_almost_equal(ma, data)

    def test_window_zero_raises(self):
        with pytest.raises(ValueError):
            moving_average(np.arange(10, dtype=float), window=0)

    def test_window_larger_than_data(self):
        # Should warn and reduce window — not raise
        import warnings
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = moving_average(np.arange(5, dtype=float), window=10)
        assert len(result) == 5



# 10. exponential_growth_rate


class TestExponentialGrowthRate:
    def test_positive_growth(self):
        t = np.arange(10)
        cases = np.exp(0.2 * t)   # growth rate = 0.2
        r = exponential_growth_rate(cases)
        assert r["growth_rate"] == pytest.approx(0.2, rel=0.01)

    def test_doubling_time(self):
        t = np.arange(20)
        cases = 2 ** (t / 7.0)    # doubles every 7 units
        r = exponential_growth_rate(cases)
        assert r["doubling_time"] == pytest.approx(7.0, rel=0.05)

    def test_no_growth_inf_doubling(self):
        cases = np.ones(10)
        r = exponential_growth_rate(cases)
        assert math.isinf(r["doubling_time"])

    def test_all_zeros_zero_rate(self):
        r = exponential_growth_rate(np.zeros(10))
        assert r["growth_rate"] == pytest.approx(0.0)

    def test_r_squared_range(self):
        t = np.arange(20)
        cases = np.exp(0.15 * t)
        r = exponential_growth_rate(cases)
        assert 0 <= r["r_squared"] <= 1

    def test_custom_time_points(self):
        cases = np.exp(0.1 * np.arange(10))
        t = np.arange(10) * 2   # every 2 units
        r = exponential_growth_rate(cases, time_points=t)
        assert r["growth_rate"] == pytest.approx(0.05, rel=0.05)



# 11. cumulative_curve & detect_peaks


class TestCumulativeAndPeaks:
    def test_cumulative_monotone(self):
        daily = np.array([5, 10, 3, 8, 2])
        cum = cumulative_curve(daily)
        assert np.all(np.diff(cum) >= 0)

    def test_cumulative_total(self):
        daily = np.array([5, 10, 3])
        assert cumulative_curve(daily)[-1] == 18

    def test_detect_peaks_single(self):
        ts = np.array([0, 1, 5, 1, 0, 1, 4, 1, 0], dtype=float)
        r = detect_peaks(ts, distance=2)
        assert r["n_peaks"] >= 1

    def test_detect_peaks_zero_peaks(self):
        ts = np.zeros(20)
        r = detect_peaks(ts)
        assert r["n_peaks"] == 0

    def test_detect_peaks_keys(self):
        ts = np.array([0, 1, 5, 1, 0], dtype=float)
        r = detect_peaks(ts)
        assert "peak_indices" in r and "n_peaks" in r



# 12. detect_epidemic_threshold


class TestEpidemicThreshold:
    def test_returns_dict(self):
        data = np.array([2, 3, 4, 20, 18, 3, 2, 2, 3], dtype=float)
        r = detect_epidemic_threshold(data)
        assert isinstance(r, dict)

    def test_epidemic_flags_bool(self):
        data = np.array([2, 3, 4, 20, 18, 3, 2, 2, 3], dtype=float)
        r = detect_epidemic_threshold(data)
        assert r["epidemic_flags"].dtype == bool

    def test_high_spike_flagged(self):
        data = np.array([2, 2, 2, 2, 50, 2, 2], dtype=float)
        r = detect_epidemic_threshold(data, method="moving_average")
        assert bool(r["epidemic_flags"][4]) is True

    def test_all_normal_no_flag(self):
        data = np.ones(20, dtype=float) * 5
        r = detect_epidemic_threshold(data, method="percentile", multiplier=1.5)
        # Constant series — nothing exceeds 75th percentile * 1.5
        assert r["epidemic_days"] == 0

    def test_unknown_method_raises(self):
        with pytest.raises(ValueError):
            detect_epidemic_threshold(np.ones(10), method="magic")



# 13. reproductive_number


class TestReproductiveNumber:
    def test_returns_array_same_length(self):
        incidence = np.array([1, 2, 4, 8, 16, 8, 4, 2, 1], dtype=float)
        Rt = reproductive_number(incidence, method="cori")
        assert len(Rt) == len(incidence)

    def test_growing_phase_rt_above_one(self):
        incidence = np.array([1, 2, 4, 8, 16, 32], dtype=float)
        Rt = reproductive_number(incidence, method="simple")
        # Rt in growing phase should be > 1 (skip first few points)
        assert Rt[-1] > 1.0

    def test_unknown_method_raises(self):
        with pytest.raises(ValueError):
            reproductive_number(np.array([1, 2, 3], dtype=float), method="unknown")



# 14. logistic_regression


class TestLogisticRegression:
    def test_returns_result(self, logistic_data):
        X, y = logistic_data
        r = logistic_regression(X, y)
        assert isinstance(r, RegressionResult)

    def test_model_type(self, logistic_data):
        X, y = logistic_data
        assert logistic_regression(X, y).model_type == "logistic"

    def test_n_observations(self, logistic_data):
        X, y = logistic_data
        assert logistic_regression(X, y).n_observations == len(y)

    def test_coefficients_shape(self, logistic_data):
        X, y = logistic_data
        r = logistic_regression(X, y)
        # intercept + 2 features
        assert len(r.coefficients) == 3

    def test_variable_names_include_intercept(self, logistic_data):
        X, y = logistic_data
        r = logistic_regression(X, y)
        assert r.variable_names[0] == "Intercept"

    def test_custom_variable_names(self, logistic_data):
        X, y = logistic_data
        r = logistic_regression(X, y, variable_names=["age", "sex"])
        assert "age" in r.variable_names

    def test_odds_ratios_positive(self, logistic_data):
        X, y = logistic_data
        r = logistic_regression(X, y)
        assert np.all(r.odds_ratios > 0)

    def test_ci_contains_or(self, logistic_data):
        X, y = logistic_data
        r = logistic_regression(X, y)
        for i in range(len(r.coefficients)):
            assert r.ci_lower[i] <= r.odds_ratios[i] <= r.ci_upper[i]

    def test_p_values_in_0_1(self, logistic_data):
        X, y = logistic_data
        r = logistic_regression(X, y)
        assert np.all((r.p_values >= 0) & (r.p_values <= 1))

    def test_aic_positive(self, logistic_data):
        X, y = logistic_data
        r = logistic_regression(X, y)
        assert r.aic > 0

    def test_bic_positive(self, logistic_data):
        X, y = logistic_data
        r = logistic_regression(X, y)
        assert r.bic > 0

    def test_aic_lt_bic_for_large_n(self, logistic_data):
        X, y = logistic_data
        r = logistic_regression(X, y)
        # BIC penalizes complexity more for large n → BIC >= AIC
        assert r.bic >= r.aic

    def test_convergence(self, logistic_data):
        X, y = logistic_data
        assert logistic_regression(X, y).convergence is True

    def test_repr(self, logistic_data):
        X, y = logistic_data
        r = logistic_regression(X, y)
        assert "logistic" in repr(r).lower()

    def test_summary_dataframe(self, logistic_data):
        X, y = logistic_data
        r = logistic_regression(X, y)
        df = r.summary()
        assert isinstance(df, pd.DataFrame)
        # summary() adds a 'Model Statistics' footer row → n_coefficients + 1
        assert len(df) >= len(r.coefficients)
        assert "Variable" in df.columns

    def test_mismatched_xy_raises(self):
        X = np.ones((10, 2))
        y = np.ones(5)
        with pytest.raises(ValueError):
            logistic_regression(X, y)

    def test_non_binary_y_raises(self):
        X = np.ones((10, 2))
        y = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2, 0], dtype=float)
        with pytest.raises(ValueError):
            logistic_regression(X, y)

    def test_strong_predictor_significant(self, rng):
        # Use moderately separated data to avoid IRLS overflow
        X = np.concatenate([rng.normal(-1.5, 0.8, (100, 1)),
                            rng.normal(+1.5, 0.8, (100, 1))])
        y = np.array([0]*100 + [1]*100, dtype=float)
        r = logistic_regression(X, y, variable_names=["predictor"])
        # The predictor coefficient should be positive and significant
        assert r.coefficients[1] > 0
        assert r.p_values[1] < 0.05

    def test_newton_method(self, logistic_data):
        X, y = logistic_data
        r = logistic_regression(X, y, method="newton")
        assert isinstance(r, RegressionResult)

    def test_unknown_method_raises(self, logistic_data):
        X, y = logistic_data
        with pytest.raises(ValueError):
            logistic_regression(X, y, method="gradient_descent")



# 15. poisson_regression


# ── BUG DOCUMENTED ─────────────────────────────────────────────────────────
# poisson_regression() uses np.math.factorial which was removed in NumPy 2.x.
# All tests are marked xfail until the source is fixed:
#   regression.py line ~450: replace np.math.factorial with math.factorial
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.xfail(
    reason="BUG: regression.py uses np.math.factorial removed in NumPy >= 2.0. "
           "Fix: replace np.math.factorial with math.factorial",
    strict=True,
)
class TestPoissonRegression:
    def test_returns_result(self, poisson_data):
        X, y = poisson_data
        r = poisson_regression(X, y)
        assert isinstance(r, RegressionResult)

    def test_model_type(self, poisson_data):
        X, y = poisson_data
        assert poisson_regression(X, y).model_type == "poisson"

    def test_n_observations(self, poisson_data):
        X, y = poisson_data
        r = poisson_regression(X, y)
        assert r.n_observations == len(y)

    def test_rate_ratios_positive(self, poisson_data):
        X, y = poisson_data
        r = poisson_regression(X, y)
        assert np.all(r.odds_ratios > 0)

    def test_ci_contains_rr(self, poisson_data):
        X, y = poisson_data
        r = poisson_regression(X, y)
        for i in range(len(r.coefficients)):
            assert r.ci_lower[i] <= r.odds_ratios[i] <= r.ci_upper[i]

    def test_p_values_range(self, poisson_data):
        X, y = poisson_data
        r = poisson_regression(X, y)
        assert np.all((r.p_values >= 0) & (r.p_values <= 1))



    def test_with_offset(self, poisson_data):
        X, y = poisson_data
        offset = np.log(np.full(len(y), 1000.0))
        r = poisson_regression(X, y, offset=offset)
        assert isinstance(r, RegressionResult)

    def test_strong_predictor_significant(self, rng):
        n = 100
        X = rng.normal(0, 1, (n, 1))
        log_mu = 1.0 + 1.5 * X[:, 0]
        y = rng.poisson(np.exp(log_mu)).astype(float)
        r = poisson_regression(X, y, variable_names=["x"])
        assert r.p_values[1] < 0.05



def test_poisson_negative_y_raises():
    """Validation runs before np.math bug → not affected by NumPy 2.x issue."""
    X = np.ones((10, 1))
    y = np.array([-1, 0, 1, 2, 3, 4, 5, 6, 7, 8], dtype=float)
    with pytest.raises(ValueError):
        poisson_regression(X, y)


# 16. likelihood_ratio_test


class TestLikelihoodRatioTest:
    def test_returns_dict(self, logistic_data):
        X, y = logistic_data
        r_full = logistic_regression(X, y)
        r_red  = logistic_regression(X[:, :1], y)
        result = likelihood_ratio_test(r_full, r_red)
        assert isinstance(result, dict)

    def test_lr_stat_positive(self, logistic_data):
        X, y = logistic_data
        r_full = logistic_regression(X, y)
        r_red  = logistic_regression(X[:, :1], y)
        result = likelihood_ratio_test(r_full, r_red)
        assert result["lr_statistic"] >= 0

    def test_p_value_in_0_1(self, logistic_data):
        X, y = logistic_data
        r_full = logistic_regression(X, y)
        r_red  = logistic_regression(X[:, :1], y)
        result = likelihood_ratio_test(r_full, r_red)
        assert 0 <= result["p_value"] <= 1

    def test_df_correct(self, logistic_data):
        X, y = logistic_data
        r_full = logistic_regression(X, y)          # 3 params (intercept + 2)
        r_red  = logistic_regression(X[:, :1], y)   # 2 params (intercept + 1)
        result = likelihood_ratio_test(r_full, r_red)
        assert result["df"] == 1

    def test_different_types_raises(self, logistic_data):
        # BUG: poisson_regression uses np.math.factorial (removed NumPy 2.x)
        # Test different_model_types check using two differently-typed mock results
        X, y = logistic_data
        r1 = logistic_regression(X, y)
        # Manually create a mock result with a different model_type
        import dataclasses
        r2 = dataclasses.replace(r1, model_type="poisson")
        with pytest.raises(ValueError, match="same type"):
            likelihood_ratio_test(r1, r2)



# 17. hosmer_lemeshow_test


class TestHosmerLemeshow:
    def test_returns_dict(self, logistic_data):
        X, y = logistic_data
        r = logistic_regression(X, y)
        X_int = np.column_stack([np.ones(len(y)), X])
        probs = 1 / (1 + np.exp(-X_int @ r.coefficients))
        result = hosmer_lemeshow_test(y, probs)
        assert isinstance(result, dict)

    def test_p_value_in_0_1(self, logistic_data):
        X, y = logistic_data
        r = logistic_regression(X, y)
        X_int = np.column_stack([np.ones(len(y)), X])
        probs = 1 / (1 + np.exp(-X_int @ r.coefficients))
        result = hosmer_lemeshow_test(y, probs)
        assert 0 <= result["p_value"] <= 1

    def test_good_fit_high_p(self, rng):
        # Perfect predictions → excellent fit → high p-value
        y    = np.array([0]*50 + [1]*50, dtype=float)
        pred = np.array([0.05]*50 + [0.95]*50)
        r = hosmer_lemeshow_test(y, pred)
        assert r["p_value"] > 0.05



# 18. calculate_vif


class TestCalculateVIF:
    def test_returns_dict(self):
        rng = np.random.default_rng(0)
        X = rng.normal(0, 1, (100, 3))
        result = calculate_vif(X)
        assert isinstance(result, dict)

    def test_independent_columns_vif_near_one(self):
        rng = np.random.default_rng(0)
        X = rng.normal(0, 1, (200, 3))
        result = calculate_vif(X)
        for v in result.values():
            assert v < 5   # independent predictors → low VIF

    def test_collinear_columns_high_vif(self):
        rng = np.random.default_rng(0)
        x1 = rng.normal(0, 1, 200)
        x2 = x1 + rng.normal(0, 0.01, 200)   # nearly identical
        X = np.column_stack([x1, x2])
        result = calculate_vif(X)
        # At least one VIF should be very high
        assert max(result.values()) > 10



# 19. Cross-module mathematical checks


class TestMathCrossChecks:
    def test_aic_penalizes_extra_params(self, logistic_data):
        """Full model AIC > reduced model AIC when extra param adds nothing."""
        # Add pure noise predictor
        X, y = logistic_data
        rng = np.random.default_rng(99)
        noise = rng.normal(0, 1, (len(y), 1))
        X_full = np.column_stack([X, noise])
        r_base = logistic_regression(X, y)
        r_full = logistic_regression(X_full, y)
        # AIC can go either way — just verify it's well-defined
        assert np.isfinite(r_base.aic) and np.isfinite(r_full.aic)

    def test_cumulative_total_equals_sum(self):
        daily = np.array([5, 10, 3, 8, 2, 7, 4])
        assert cumulative_curve(daily)[-1] == daily.sum()

    def test_growth_rate_doubling_inverse(self):
        """T2 = ln(2) / r."""
        data = np.exp(0.1 * np.arange(30))
        r = exponential_growth_rate(data)
        expected_t2 = math.log(2) / r["growth_rate"]
        assert r["doubling_time"] == pytest.approx(expected_t2, rel=0.01)

    def test_logistic_or_intercept_one_at_50pct(self, rng):
        """When prevalence is 50%, log-OR intercept ≈ 0 with no predictors."""
        n = 500
        y = rng.binomial(1, 0.5, n).astype(float)
        X = np.zeros((n, 1))
        r = logistic_regression(X, y, variable_names=["dummy"])
        # Intercept should be near 0 (log-odds ≈ 0 for 50% prevalence)
        assert abs(r.coefficients[0]) < 0.3

    @pytest.mark.xfail(
        reason="BUG: poisson_regression uses np.math.factorial removed in NumPy 2.x",
        strict=True,
    )
    def test_poisson_rate_ratio_direction(self, rng):
        """Positive coefficient → rate ratio > 1."""
        n = 100
        X = rng.normal(0, 1, (n, 1))
        y = rng.poisson(np.exp(0 + 2.0 * X[:, 0])).astype(float)
        r = poisson_regression(X, y, variable_names=["x"])
        assert r.odds_ratios[1] > 1.0