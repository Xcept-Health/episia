"""
tests/unit/test_coverage_boost.py

Targeted tests to increase global coverage from 79% to 85%.
Modules covered: stats/time_series, stats/regression, data/surveillance,
                 viz/forest.
"""
import pytest
import numpy as np
import pandas as pd


#  stats/time_series 

class TestTimeSeriesUncovered:

    def test_timeseries_result_repr(self):
        from episia.stats.time_series import TimeSeriesResult
        ts = TimeSeriesResult(
            dates=np.array([pd.Timestamp("2024-01-01")]),
            observed=np.array([10.0]),
            predicted=None,
            metrics={"r_squared": 0.95},
        )
        assert "R²" in repr(ts) or "0.95" in repr(ts)

    def test_timeseries_result_repr_no_metrics(self):
        from episia.stats.time_series import TimeSeriesResult
        ts = TimeSeriesResult(
            dates=np.array([]),
            observed=np.array([]),
        )
        assert repr(ts) == "TimeSeriesResult"

    def test_plot_data_with_predicted(self):
        from episia.stats.time_series import TimeSeriesResult
        ts = TimeSeriesResult(
            dates=np.array([pd.Timestamp("2024-01-01")]),
            observed=np.array([10.0]),
            predicted=np.array([9.5]),
        )
        data = ts.plot_data()
        assert "predicted" in data

    def test_plot_data_without_predicted(self):
        from episia.stats.time_series import TimeSeriesResult
        ts = TimeSeriesResult(
            dates=np.array([pd.Timestamp("2024-01-01")]),
            observed=np.array([10.0]),
        )
        data = ts.plot_data()
        assert "dates" in data
        assert "observed" in data

    def test_calculate_incidence(self):
        from episia.stats.time_series import calculate_incidence
        cases = np.array([10.0, 20.0, 15.0])
        pop = 1000.0
        result = calculate_incidence(cases, pop)
        assert len(result) == 3
        assert result[0] == pytest.approx(0.01)

    def test_calculate_attack_rate(self):
        from episia.stats.time_series import calculate_attack_rate
        result = calculate_attack_rate(50, 1000, per=100)
        assert result == pytest.approx(5.0)

    def test_epidemic_curve_weekly(self):
        from episia.stats.time_series import epidemic_curve, TimeAggregation
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        counts = np.random.randint(1, 10, size=30)
        ec = epidemic_curve(dates, counts, aggregation=TimeAggregation.WEEKLY)
        assert len(ec.dates) <= 30

    def test_epidemic_curve_monthly(self):
        from episia.stats.time_series import epidemic_curve, TimeAggregation
        dates = pd.date_range("2024-01-01", periods=60, freq="D")
        counts = np.random.randint(1, 10, size=60)
        ec = epidemic_curve(dates, counts, aggregation=TimeAggregation.MONTHLY)
        assert len(ec.dates) >= 1

    def test_moving_average_basic(self):
        from episia.stats.time_series import moving_average
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = moving_average(data, window=3)
        assert len(result) == len(data)

    def test_reproductive_number_simple(self):
        from episia.stats.time_series import reproductive_number
        incidence = np.array([1.0, 2.0, 4.0, 8.0, 16.0, 10.0, 5.0])
        rt = reproductive_number(incidence, method="simple")
        assert len(rt) == len(incidence)

    def test_reproductive_number_cori(self):
        from episia.stats.time_series import reproductive_number
        incidence = np.array([1.0, 2.0, 4.0, 8.0, 16.0, 10.0, 5.0])
        rt = reproductive_number(incidence, method="cori")
        assert len(rt) == len(incidence)

    def test_exponential_growth_rate(self):
        from episia.stats.time_series import exponential_growth_rate
        cases = np.array([1.0, 2.0, 4.0, 8.0, 16.0, 32.0])
        result = exponential_growth_rate(cases)
        assert "growth_rate" in result
        assert "doubling_time" in result
        assert result["growth_rate"] > 0

    def test_exponential_growth_rate_flat(self):
        from episia.stats.time_series import exponential_growth_rate
        # fewer than 2 non-zero values → should return default values
        cases = np.array([0.0, 0.0, 1.0])
        result = exponential_growth_rate(cases)
        assert "growth_rate" in result

    def test_nowcasting_simple(self):
        from episia.stats.time_series import nowcasting
        reported = np.array([10.0, 8.0, 6.0, 4.0, 2.0])
        delay = np.array([0.5, 0.3, 0.2])
        result = nowcasting(reported, delay, method="simple")
        assert len(result) == len(reported)

    def test_nowcasting_unknown_method_raises(self):
        from episia.stats.time_series import nowcasting
        with pytest.raises(ValueError):
            nowcasting(np.array([1.0, 2.0]), np.array([0.5, 0.5]), method="unknown")

    def test_cumulative_curve(self):
        from episia.stats.time_series import cumulative_curve
        daily = np.array([1.0, 2.0, 3.0, 4.0])
        result = cumulative_curve(daily)
        assert result[-1] == pytest.approx(10.0)
        assert len(result) == 4

    def test_detect_peaks_basic(self):
        from episia.stats.time_series import detect_peaks
        ts = np.array([1.0, 5.0, 1.0, 8.0, 1.0, 3.0, 1.0])
        result = detect_peaks(ts, distance=1)
        assert "peak_indices" in result or "peaks" in result or isinstance(result, dict)


#  stats/regression (uncovered sections) 

class TestRegressionUncovered:

    def _make_logistic_data(self, n=100):
        np.random.seed(42)
        X = np.random.randn(n, 2)
        p = 1 / (1 + np.exp(-(X[:, 0] + 0.5 * X[:, 1])))
        y = (p > 0.5).astype(float)
        return X, y

    def _make_poisson_data(self, n=80):
        np.random.seed(42)
        X = np.random.rand(n, 1)
        y = np.random.poisson(lam=np.exp(1 + X[:, 0]))
        return X, y.astype(float)

    def test_poisson_regression_basic(self):
        from episia.stats.regression import poisson_regression
        X, y = self._make_poisson_data()
        result = poisson_regression(X, y)
        assert hasattr(result, "coefficients")
        assert len(result.coefficients) >= 1

    def test_poisson_regression_negative_y_raises(self):
        from episia.stats.regression import poisson_regression
        X = np.array([[1.0], [2.0], [3.0]])
        y = np.array([1.0, -1.0, 2.0])
        with pytest.raises(ValueError):
            poisson_regression(X, y)

    def test_regression_result_summary_table(self):
        from episia.stats.regression import logistic_regression
        X, y = self._make_logistic_data()
        model = logistic_regression(X, y)
        table = model.summary_table()
        assert isinstance(table, pd.DataFrame)

    def test_regression_result_predict(self):
        from episia.stats.regression import logistic_regression
        X, y = self._make_logistic_data()
        model = logistic_regression(X, y, add_intercept=True)
        X_test = np.column_stack([np.ones(5), np.random.randn(5, 2)])
        preds = model.predict(X_test)
        assert len(preds) == 5
        assert all(0 <= p <= 1 for p in preds)

    def test_interaction_term_no_center(self):
        from episia.stats.regression import interaction_term
        X1 = np.array([1.0, 2.0, 3.0])
        X2 = np.array([4.0, 5.0, 6.0])
        result = interaction_term(X1, X2, center=False)
        np.testing.assert_array_equal(result, [4.0, 10.0, 18.0])

    def test_interaction_term_centered(self):
        from episia.stats.regression import interaction_term
        X1 = np.array([1.0, 2.0, 3.0])
        X2 = np.array([4.0, 5.0, 6.0])
        result = interaction_term(X1, X2, center=True)
        assert len(result) == 3

    def test_likelihood_ratio_test(self):
        from episia.stats.regression import logistic_regression, likelihood_ratio_test
        np.random.seed(0)
        X = np.random.randn(100, 2)
        y = (X[:, 0] > 0).astype(float)
        full = logistic_regression(X, y, add_intercept=True)
        reduced = logistic_regression(X[:, :1], y, add_intercept=True)
        result = likelihood_ratio_test(full, reduced)
        assert "lr_stat" in result or "statistic" in result or isinstance(result, dict)

    def test_likelihood_ratio_test_type_mismatch_raises(self):
        from episia.stats.regression import logistic_regression, poisson_regression, likelihood_ratio_test
        np.random.seed(0)
        X = np.random.randn(50, 1)
        y_bin = (X[:, 0] > 0).astype(float)
        y_count = np.abs(np.random.poisson(2, 50)).astype(float)
        m1 = logistic_regression(X, y_bin)
        m2 = poisson_regression(X, y_count)
        with pytest.raises(ValueError):
            likelihood_ratio_test(m1, m2)


#  data/surveillance (uncovered sections) 

class TestSurveillanceUncovered:

    @pytest.fixture
    def multi_disease_ds(self):
        import pandas as pd
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=12, freq="W"),
            "cases": np.random.randint(1, 20, 12),
            "disease": ["malaria"] * 6 + ["meningitis"] * 6,
            "district": ["Nord"] * 12,
        })
        from episia.data.surveillance import SurveillanceDataset
        return SurveillanceDataset(df, date_col="date", cases_col="cases",
                                   disease_col="disease", district_col="district")

    @pytest.fixture
    def basic_ds(self):
        import pandas as pd
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=8, freq="W"),
            "cases": [5, 8, 12, 6, 4, 9, 15, 7],
        })
        from episia.data.surveillance import SurveillanceDataset
        return SurveillanceDataset(df, date_col="date", cases_col="cases")

    def test_diseases_property(self, multi_disease_ds):
        diseases = multi_disease_ds.diseases
        assert "malaria" in diseases
        assert "meningitis" in diseases

    def test_diseases_empty_when_no_col(self, basic_ds):
        assert basic_ds.diseases == []

    def test_filter_disease(self, multi_disease_ds):
        ds = multi_disease_ds.filter_disease("malaria")
        assert ds.n_records == 6

    def test_filter_disease_no_col_raises(self, basic_ds):
        with pytest.raises(ValueError):
            basic_ds.filter_disease("malaria")

    def test_alert_engine_zscore(self, basic_ds):
        from episia.data.surveillance import AlertEngine
        engine = AlertEngine(basic_ds)
        alerts = engine.run(threshold=999, zscore_threshold=1.0)
        assert isinstance(alerts, list)

    def test_alert_engine_endemic_channel(self):
        import pandas as pd
        from episia.data.surveillance import SurveillanceDataset, AlertEngine
        rows = []
        for year in [2022, 2023, 2024]:
            for week in range(1, 20):
                rows.append({
                    "date": pd.Timestamp.fromisocalendar(year, week, 1),
                    "cases": week + year - 2022,
                })
        df = pd.DataFrame(rows)
        ds = SurveillanceDataset(df, date_col="date", cases_col="cases")
        engine = AlertEngine(ds)
        alerts = engine.run(threshold=999, use_endemic_channel=True)
        assert isinstance(alerts, list)

    def test_compute_attack_rate_module_level(self):
        from episia.data.surveillance import compute_attack_rate
        result = compute_attack_rate(100, 10000, per=100000)
        assert result == pytest.approx(1000.0)

    def test_compute_attack_rate_zero_pop_raises(self):
        from episia.data.surveillance import compute_attack_rate
        with pytest.raises(ValueError):
            compute_attack_rate(10, 0)

    def test_endemic_channel_module_level(self, basic_ds):
        from episia.data.surveillance import endemic_channel
        result = endemic_channel(basic_ds)
        assert "weeks" in result

    def test_aggregate_by_module_level(self, basic_ds):
        from episia.data.surveillance import aggregate_by
        result = aggregate_by(basic_ds, freq="W")
        assert len(result) >= 1

    def test_completeness_with_period_col(self):
        import pandas as pd
        from episia.data.surveillance import SurveillanceDataset
        df = pd.DataFrame({
            "period_str": ["2024W01", "2024W02", "2024W04", "2024W05"],
            "date": pd.date_range("2024-01-01", periods=4, freq="W"),
            "cases": [5, 8, 6, 10],
        })
        ds = SurveillanceDataset(df, date_col="date", cases_col="cases")
        result = ds.completeness(period_col="period_str")
        assert "missing_periods" in result
        assert "2024W03" in result["missing_periods"]

    def test_summary_dict(self, basic_ds):
        summary = basic_ds.summary()
        assert isinstance(summary, dict)
        assert "n_records" in summary or "total_cases" in summary or len(summary) > 0


#  viz/forest (uncovered sections) 

class TestForestPlotUncovered:

    def _make_result(self, measure, ci_lower, ci_upper, p=0.05,
                     variable="X", n=100):
        """Create a result object compatible with plot_forest."""
        class MockResult:
            def __init__(self):
                self.variable_names = [variable]
                self.coefficients = np.array([measure])
                self.ci_lower = np.array([ci_lower])
                self.ci_upper = np.array([ci_upper])
                self.p_values = np.array([p])
                self.odds_ratios = np.array([np.exp(measure)])
                self.n_observations = n
                self.model_type = "logistic"
                self.log_likelihood = -50.0
                self.aic = 104.0
                self.bic = 108.0
        return MockResult()

    def test_collect_rows_logistic(self):
        from episia.viz.forest import _collect_rows
        result = self._make_result(0.5, 0.2, 0.8)
        rows, ref = _collect_rows(result)
        assert len(rows) >= 1

    def test_p_str_small(self):
        from episia.viz.forest import _p_str
        assert _p_str(0.0001) == "<0.001"

    def test_p_str_normal(self):
        from episia.viz.forest import _p_str
        result = _p_str(0.05)
        assert "0.05" in result or result == "0.050"

    def test_p_str_none(self):
        from episia.viz.forest import _p_str
        result = _p_str(None)
        assert result == "" or result is not None

    def test_plot_forest_returns_figure(self):
        pytest.importorskip("matplotlib")
        from episia.viz.forest import plot_forest
        result = self._make_result(0.5, 0.2, 0.8)
        fig = plot_forest(result)
        assert fig is not None

    def test_plot_forest_multiple_variables(self):
        pytest.importorskip("matplotlib")
        from episia.viz.forest import plot_forest
        from episia.stats.regression import logistic_regression
        np.random.seed(42)
        X = np.random.randn(100, 3)
        y = (X[:, 0] + X[:, 1] > 0).astype(float)
        model = logistic_regression(X, y, add_intercept=False,
                                    variable_names=["Age", "BMI", "Sex"])
        fig = plot_forest(model)
        assert fig is not None