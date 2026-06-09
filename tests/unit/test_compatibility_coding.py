"""
Tests for episia.compatibility.coding - full coverage
"""

import warnings
import numpy as np
import pandas as pd
import pytest

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from episia.compatibility import CodingComparator, CodingRobustnessResult, MeasureDelta


# Fixtures

def _make_datasets(seed: int = 42, n: int = 500):
    """
    Two datasets representing the same cohort coded differently.
    V2 introduces ~25% missed cases among young unexposed patients.
    """
    rng = np.random.default_rng(seed)
    age = rng.integers(20, 80, n)
    exposure = rng.integers(0, 2, n)
    prob = 1 / (1 + np.exp(-(0.05 * age + 1.5 * exposure - 4)))
    disease_true = (rng.random(n) < prob).astype(int)
    follow_up = rng.uniform(100, 3650, n)  # person-days

    disease_v2 = disease_true.copy()
    for i in range(n):
        if disease_true[i] == 1 and age[i] < 50 and exposure[i] == 0:
            if rng.random() < 0.25:
                disease_v2[i] = 0

    df_v1 = pd.DataFrame({
        "age": age, "exposure": exposure,
        "disease": disease_true, "follow_up": follow_up,
    })
    df_v2 = pd.DataFrame({
        "age": age, "exposure": exposure,
        "disease": disease_v2, "follow_up": follow_up,
    })
    return df_v1, df_v2


@pytest.fixture
def datasets():
    return _make_datasets()


# CodingComparator - basic

class TestCodingComparatorBasic:

    def test_run_returns_result(self, datasets):
        df_v1, df_v2 = datasets
        comp = CodingComparator(
            dataset_v1=df_v1, dataset_v2=df_v2,
            outcome_col="disease", exposure_col="exposure",
            coding_system_v1="ICD-10", coding_system_v2="ICD-11",
        )
        assert isinstance(comp.run(), CodingRobustnessResult)

    def test_prevalence_always_computed(self, datasets):
        df_v1, df_v2 = datasets
        result = CodingComparator(
            dataset_v1=df_v1, dataset_v2=df_v2,
            outcome_col="disease",
        ).run()
        assert any(d.measure == "prevalence" for d in result.deltas)

    def test_no_exposure_no_rr_or(self, datasets):
        df_v1, df_v2 = datasets
        result = CodingComparator(
            dataset_v1=df_v1, dataset_v2=df_v2,
            outcome_col="disease",
        ).run()
        measures = {d.measure for d in result.deltas}
        assert "risk_ratio" not in measures
        assert "odds_ratio" not in measures

    def test_identical_datasets_full_robustness(self, datasets):
        df_v1, _ = datasets
        result = CodingComparator(
            dataset_v1=df_v1, dataset_v2=df_v1,
            outcome_col="disease", exposure_col="exposure",
        ).run()
        assert result.robustness_score == 1.0
        assert result.unstable_measures == []

    def test_robustness_score_in_range(self, datasets):
        df_v1, df_v2 = datasets
        result = CodingComparator(
            dataset_v1=df_v1, dataset_v2=df_v2,
            outcome_col="disease", exposure_col="exposure",
        ).run()
        assert 0.0 <= result.robustness_score <= 1.0

    def test_n_v2_lte_n_v1_with_coding_miss(self, datasets):
        df_v1, df_v2 = datasets
        result = CodingComparator(
            dataset_v1=df_v1, dataset_v2=df_v2,
            outcome_col="disease",
        ).run()
        assert result.n_v2 <= result.n_v1



# CodingComparator - all measures

class TestCodingComparatorMeasures:

    def test_exposure_measures_present(self, datasets):
        df_v1, df_v2 = datasets
        result = CodingComparator(
            dataset_v1=df_v1, dataset_v2=df_v2,
            outcome_col="disease", exposure_col="exposure",
        ).run()
        measures = {d.measure for d in result.deltas}
        assert {"risk_ratio", "odds_ratio", "attributable_risk",
                "pop_attributable_frac"}.issubset(measures)

    def test_incidence_rate_computed_with_person_time(self, datasets):
        df_v1, df_v2 = datasets
        result = CodingComparator(
            dataset_v1=df_v1, dataset_v2=df_v2,
            outcome_col="disease", person_time_col="follow_up",
        ).run()
        assert any(d.measure == "incidence_rate" for d in result.deltas)

    def test_incidence_rate_not_computed_without_person_time(self, datasets):
        df_v1, df_v2 = datasets
        result = CodingComparator(
            dataset_v1=df_v1, dataset_v2=df_v2,
            outcome_col="disease",
        ).run()
        assert not any(d.measure == "incidence_rate" for d in result.deltas)

    def test_all_measures_with_all_columns(self, datasets):
        df_v1, df_v2 = datasets
        result = CodingComparator(
            dataset_v1=df_v1, dataset_v2=df_v2,
            outcome_col="disease", exposure_col="exposure",
            person_time_col="follow_up",
        ).run()
        measures = {d.measure for d in result.deltas}
        expected = {
            "prevalence", "incidence_rate", "risk_ratio",
            "odds_ratio", "attributable_risk", "pop_attributable_frac",
        }
        assert expected == measures



# CodingComparator - validation errors

class TestCodingComparatorValidation:

    def test_missing_outcome_col_raises(self, datasets):
        df_v1, df_v2 = datasets
        with pytest.raises(ValueError, match="outcome_col"):
            CodingComparator(
                dataset_v1=df_v1, dataset_v2=df_v2,
                outcome_col="nonexistent",
            )

    def test_missing_exposure_col_raises(self, datasets):
        df_v1, df_v2 = datasets
        with pytest.raises(ValueError, match="exposure_col"):
            CodingComparator(
                dataset_v1=df_v1, dataset_v2=df_v2,
                outcome_col="disease", exposure_col="nonexistent",
            )

    def test_missing_person_time_col_raises(self, datasets):
        df_v1, df_v2 = datasets
        with pytest.raises(ValueError, match="person_time_col"):
            CodingComparator(
                dataset_v1=df_v1, dataset_v2=df_v2,
                outcome_col="disease", person_time_col="nonexistent",
            )

    def test_different_row_counts_raises(self, datasets):
        df_v1, df_v2 = datasets
        with pytest.raises(ValueError, match="same number of rows"):
            CodingComparator(
                dataset_v1=df_v1, dataset_v2=df_v2.iloc[:100],
                outcome_col="disease",
            )

    def test_non_binary_outcome_raises(self, datasets):
        df_v1, df_v2 = datasets
        df_bad = df_v1.copy()
        df_bad["disease"] = df_bad["disease"] * 3  # values 0 and 3
        with pytest.raises(ValueError, match="binary"):
            CodingComparator(
                dataset_v1=df_bad, dataset_v2=df_v2,
                outcome_col="disease",
            )

    def test_nan_rows_dropped_with_warning(self, datasets):
        df_v1, df_v2 = datasets
        df_v1_nan = df_v1.copy()
        df_v1_nan.loc[0, "disease"] = float("nan")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = CodingComparator(
                dataset_v1=df_v1_nan, dataset_v2=df_v2,
                outcome_col="disease",
            ).run()
        assert any("dropped" in str(warning.message).lower() for warning in w)
        assert result.metadata["n_rows_v1"] == len(df_v1) - 1

    def test_empty_dataset_returns_nan_measures(self):
        df_empty = pd.DataFrame({"disease": pd.Series([], dtype=int)})
        result = CodingComparator(
            dataset_v1=df_empty, dataset_v2=df_empty,
            outcome_col="disease",
        ).run()
        prev = next(d for d in result.deltas if d.measure == "prevalence")
        assert np.isnan(prev.value_v1)



# CodingRobustnessResult interface

class TestCodingRobustnessResult:

    @pytest.fixture
    def result(self, datasets):
        df_v1, df_v2 = datasets
        return CodingComparator(
            dataset_v1=df_v1, dataset_v2=df_v2,
            outcome_col="disease", exposure_col="exposure",
            person_time_col="follow_up",
            coding_system_v1="ICD-10", coding_system_v2="ICD-11",
        ).run()

    def test_summary_contains_system_labels(self, result):
        s = result.summary()
        assert "ICD-10" in s and "ICD-11" in s

    def test_summary_contains_robustness_score(self, result):
        assert "Robustness" in result.summary() or "robustness" in result.summary()

    def test_to_dataframe_columns(self, result):
        df = result.to_dataframe()
        assert "measure" in df.columns
        assert "absolute_delta" in df.columns
        assert "relative_delta_pct" in df.columns
        assert "conclusion_changed" in df.columns

    def test_to_dataframe_row_count(self, result):
        assert len(result.to_dataframe()) == len(result.deltas)

    def test_plot_plotly(self, result):
        fig = result.plot(backend="plotly")
        assert fig is not None

    def test_plot_matplotlib(self, result):
        import matplotlib
        matplotlib.use("Agg")
        fig = result.plot(backend="matplotlib")
        assert fig is not None

    def test_plot_invalid_backend(self, result):
        with pytest.raises(ValueError, match="backend"):
            result.plot(backend="seaborn")

    def test_repr(self, result):
        assert "CodingRobustnessResult" in repr(result)


# MeasureDelta

class TestMeasureDelta:

    def test_absolute_delta(self):
        d = MeasureDelta("prevalence", value_v1=0.20, value_v2=0.15)
        assert abs(d.absolute_delta - (-0.05)) < 1e-9

    def test_relative_delta(self):
        d = MeasureDelta("prevalence", value_v1=0.20, value_v2=0.15)
        assert abs(d.relative_delta - (-0.25)) < 1e-9

    def test_relative_delta_zero_denominator(self):
        d = MeasureDelta("prevalence", value_v1=0.0, value_v2=0.10)
        assert np.isnan(d.relative_delta)

    def test_conclusion_stable_overlapping_ci(self):
        d = MeasureDelta.from_values(
            "risk_ratio", value_v1=2.0, value_v2=1.9,
            ci_lower_v1=1.5, ci_upper_v1=2.5,
            ci_lower_v2=1.4, ci_upper_v2=2.4,
        )
        assert d.conclusion_changed is False

    def test_conclusion_changed_non_overlapping_ci(self):
        d = MeasureDelta.from_values(
            "risk_ratio", value_v1=3.0, value_v2=1.2,
            ci_lower_v1=2.5, ci_upper_v1=3.5,
            ci_lower_v2=1.0, ci_upper_v2=1.4,
        )
        assert d.conclusion_changed is True

    def test_fallback_threshold_stable(self):
        d = MeasureDelta("prevalence", value_v1=0.20, value_v2=0.21)
        assert d.conclusion_changed is False

    def test_fallback_threshold_unstable(self):
        d = MeasureDelta("prevalence", value_v1=0.20, value_v2=0.25)
        assert d.conclusion_changed is True

    def test_repr_contains_measure_name(self):
        d = MeasureDelta("odds_ratio", value_v1=1.5, value_v2=1.2)
        assert "odds_ratio" in repr(d)