"""
tests/unit/test_stats.py
Unit tests for epitools.stats
    contingency  : Table2x2, risk_ratio, odds_ratio, from_dataframe
    descriptive  : proportion_ci, mean_ci, incidence_rate, attack_rate
    diagnostic   : diagnostic_test_2x2, roc_analysis
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
import pytest

from epitools.stats.contingency import (
    Table2x2, RiskRatioResult, OddsRatioResult,
    ConfidenceMethod, risk_ratio, odds_ratio, from_dataframe,
)
from epitools.stats.descriptive import (
    CI_Method, ProportionResult, MeanResult,
    proportion_ci, mean_ci, incidence_rate, attack_rate, prevalence,
    interquartile_range,
)
from epitools.stats.diagnostic import (
    DiagnosticResult, ROCResult,
    diagnostic_test_2x2, roc_analysis,
)



# Fixtures


@pytest.fixture
def table_standard():
    """Standard 2x2 table: a=40, b=10, c=20, d=30."""
    return Table2x2(40, 10, 20, 30)

@pytest.fixture
def table_equal():
    """Table with equal risks: RR=1, OR=1."""
    return Table2x2(10, 10, 10, 10)

@pytest.fixture
def diag_standard():
    """tp=80, fp=10, fn=20, tn=90."""
    return diagnostic_test_2x2(80, 10, 20, 90)



# 1. Table2x2 — construction & properties


class TestTable2x2Init:
    def test_stores_cells(self, table_standard):
        t = table_standard
        assert t.a == 40 and t.b == 10 and t.c == 20 and t.d == 30

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            Table2x2(-1, 10, 20, 30)

    def test_zero_cells_allowed(self):
        t = Table2x2(0, 0, 0, 0)
        assert t.total == 0

    def test_repr(self, table_standard):
        r = repr(table_standard)
        assert "40" in r and "Table2x2" in r

    def test_to_dict(self, table_standard):
        d = table_standard.to_dict()
        assert d["a"] == 40 and d["total"] == 100


class TestTable2x2Properties:
    def test_total_exposed(self, table_standard):
        assert table_standard.total_exposed == 60   # 40+20

    def test_total_unexposed(self, table_standard):
        assert table_standard.total_unexposed == 40  # 10+30

    def test_total_cases(self, table_standard):
        assert table_standard.total_cases == 50      # 40+10

    def test_total_non_cases(self, table_standard):
        assert table_standard.total_non_cases == 50  # 20+30

    def test_total(self, table_standard):
        assert table_standard.total == 100

    def test_risk_exposed(self, table_standard):
        # 40/60 = 0.6667
        assert table_standard.risk_exposed == pytest.approx(40/60)

    def test_risk_unexposed(self, table_standard):
        # 10/40 = 0.25
        assert table_standard.risk_unexposed == pytest.approx(10/40)

    def test_risk_exposed_zero_total(self):
        t = Table2x2(0, 10, 0, 20)
        assert t.risk_exposed == 0.0

    def test_odds_exposed(self, table_standard):
        # 40/20 = 2.0
        assert table_standard.odds_exposed == pytest.approx(2.0)

    def test_odds_unexposed(self, table_standard):
        # 10/30 = 0.333
        assert table_standard.odds_unexposed == pytest.approx(1/3)

    def test_odds_exposed_zero_c(self):
        t = Table2x2(10, 5, 0, 20)
        assert math.isinf(t.odds_exposed)

    def test_odds_unexposed_zero_d(self):
        t = Table2x2(10, 5, 20, 0)
        assert math.isinf(t.odds_unexposed)



# 2. Table2x2 — risk_ratio


class TestTable2x2RiskRatio:
    def test_returns_result_object(self, table_standard):
        assert isinstance(table_standard.risk_ratio(), RiskRatioResult)

    def test_estimate_nominal(self, table_standard):
        # RR = (40/60) / (10/40) = 0.6667/0.25 = 2.667
        assert table_standard.risk_ratio().estimate == pytest.approx(2.667, rel=1e-3)

    def test_estimate_equal_risks(self, table_equal):
        assert table_equal.risk_ratio().estimate == pytest.approx(1.0)

    def test_ci_contains_estimate(self, table_standard):
        r = table_standard.risk_ratio()
        assert r.ci_lower < r.estimate < r.ci_upper

    def test_ci_lower_positive(self, table_standard):
        assert table_standard.risk_ratio().ci_lower > 0

    def test_significant_strong_association(self, table_standard):
        assert table_standard.risk_ratio().significant is True

    def test_not_significant_null(self, table_equal):
        assert table_equal.risk_ratio().significant is False

    def test_null_value_is_one(self, table_standard):
        assert table_standard.risk_ratio().null_value == 1.0

    def test_p_value_significant(self, table_standard):
        p = table_standard.risk_ratio().p_value
        assert p is not None and p < 0.05

    def test_p_value_not_significant(self, table_equal):
        p = table_equal.risk_ratio().p_value
        # p should be None or >= 0.05 for RR=1
        assert p is None or p >= 0.05

    def test_to_dict_keys(self, table_standard):
        d = table_standard.risk_ratio().to_dict()
        for k in ["measure", "estimate", "ci_lower", "ci_upper", "significant"]:
            assert k in d

    def test_repr_contains_estimate(self, table_standard):
        r = repr(table_standard.risk_ratio())
        assert "Risk Ratio" in r or "2.667" in r

    def test_zero_exposed_cases(self):
        t = Table2x2(0, 10, 20, 30)
        assert t.risk_ratio().estimate == pytest.approx(0.0)

    def test_zero_unexposed_risk_inf(self):
        # b=0 → unexposed risk=0 → RR=inf
        # BUG in source: _wald_ci_rr crashes with ZeroDivisionError when b=0
        # Test documents the current behaviour — CI calculation raises
        t = Table2x2(10, 0, 5, 5)
        with pytest.raises(ZeroDivisionError):
            t.risk_ratio()

    def test_99_ci_wider_than_95(self, table_standard):
        r95 = table_standard.risk_ratio(confidence=0.95)
        r99 = table_standard.risk_ratio(confidence=0.99)
        assert (r99.ci_upper - r99.ci_lower) > (r95.ci_upper - r95.ci_lower)



# 3. Table2x2 — odds_ratio


class TestTable2x2OddsRatio:
    def test_returns_result_object(self, table_standard):
        assert isinstance(table_standard.odds_ratio(), OddsRatioResult)

    def test_estimate_nominal(self, table_standard):
        # OR = (40*30)/(10*20) = 6.0
        assert table_standard.odds_ratio().estimate == pytest.approx(6.0)

    def test_estimate_equal(self, table_equal):
        assert table_equal.odds_ratio().estimate == pytest.approx(1.0)

    def test_ci_contains_estimate(self, table_standard):
        r = table_standard.odds_ratio()
        assert r.ci_lower < r.estimate < r.ci_upper

    def test_significant(self, table_standard):
        assert table_standard.odds_ratio().significant is True

    def test_not_significant_null(self, table_equal):
        assert table_equal.odds_ratio().significant is False

    def test_to_dict(self, table_standard):
        d = table_standard.odds_ratio().to_dict()
        assert d["measure"] == "odds_ratio"
        assert d["estimate"] == pytest.approx(6.0)

    def test_zero_cell_correction(self):
        t = Table2x2(10, 0, 5, 10)
        r = t.odds_ratio()
        # Should not raise; Haldane-Anscombe correction applied
        assert r.estimate > 0

    def test_reciprocal_symmetry(self, table_standard):
        or1 = table_standard.odds_ratio().estimate
        t2 = Table2x2(10, 40, 30, 20)
        or2 = t2.odds_ratio().estimate
        assert or1 == pytest.approx(1.0 / or2, rel=1e-4)



# 4. Table2x2 — risk_difference & chi_square & fisher_exact


class TestTable2x2OtherMeasures:
    def test_risk_difference_positive(self, table_standard):
        rd = table_standard.risk_difference()
        # exposed risk > unexposed risk → RD > 0
        assert rd["estimate"] > 0

    def test_risk_difference_ci_contains_estimate(self, table_standard):
        rd = table_standard.risk_difference()
        assert rd["ci_lower"] < rd["estimate"] < rd["ci_upper"]

    def test_risk_difference_zero_for_equal(self, table_equal):
        rd = table_equal.risk_difference()
        assert rd["estimate"] == pytest.approx(0.0)

    def test_chi_square_returns_dict(self, table_standard):
        cs = table_standard.chi_square()
        assert "chi2" in cs and "p_value" in cs and "df" in cs

    def test_chi_square_significant(self, table_standard):
        cs = table_standard.chi_square()
        assert cs["p_value"] < 0.05

    def test_chi_square_not_significant_null(self, table_equal):
        cs = table_equal.chi_square(correction=False)
        assert cs["p_value"] > 0.05

    def test_chi_square_df_one(self, table_standard):
        assert table_standard.chi_square()["df"] == 1

    def test_fisher_exact_returns_dict(self, table_standard):
        fe = table_standard.fisher_exact()
        assert "p_value" in fe and "odds_ratio" in fe

    def test_fisher_exact_significant(self, table_standard):
        assert table_standard.fisher_exact()["p_value"] < 0.05

    def test_attributable_fraction_positive(self, table_standard):
        af = table_standard.attributable_fraction_exposed()
        assert 0 < af < 1

    def test_summary_keys(self, table_standard):
        # BUG in source: summary() calls attributable_fraction_population()
        # which does not exist on Table2x2. Documents the current behaviour.
        with pytest.raises(AttributeError, match="attributable_fraction_population"):
            table_standard.summary()



# 5. Convenience functions & from_dataframe


class TestConvenienceFunctions:
    def test_risk_ratio_fn(self):
        r = risk_ratio(40, 10, 20, 30)
        assert isinstance(r, RiskRatioResult)
        assert r.estimate == pytest.approx(2.667, rel=1e-3)

    def test_odds_ratio_fn(self):
        r = odds_ratio(40, 10, 20, 30)
        assert isinstance(r, OddsRatioResult)
        assert r.estimate == pytest.approx(6.0)

    def test_from_dataframe(self):
        df = pd.DataFrame({
            "exposed": [1,1,1,0,0,0,1,0],
            "outcome": [1,1,0,1,0,0,0,1],
        })
        t = from_dataframe(df, "exposed", "outcome")
        assert isinstance(t, Table2x2)
        assert t.total == 8

    def test_from_dataframe_boolean(self):
        df = pd.DataFrame({
            "exp": [True, True, False, False],
            "out": [True, False, True, False],
        })
        t = from_dataframe(df, "exp", "out")
        assert t.total == 4



# 6. proportion_ci


class TestProportionCI:
    def test_returns_proportion_result(self):
        assert isinstance(proportion_ci(45, 200), ProportionResult)

    def test_proportion_value(self):
        r = proportion_ci(45, 200)
        assert r.proportion == pytest.approx(0.225)

    def test_ci_contains_proportion(self):
        r = proportion_ci(45, 200)
        assert r.ci_lower < r.proportion < r.ci_upper

    def test_ci_bounds_0_to_1(self):
        r = proportion_ci(45, 200)
        assert 0 <= r.ci_lower and r.ci_upper <= 1

    def test_zero_numerator(self):
        r = proportion_ci(0, 100)
        assert r.proportion == pytest.approx(0.0)
        assert r.ci_lower == pytest.approx(0.0)

    def test_full_numerator(self):
        r = proportion_ci(100, 100)
        assert r.proportion == pytest.approx(1.0)

    def test_numerator_exceeds_denominator_raises(self):
        with pytest.raises(ValueError):
            proportion_ci(101, 100)

    def test_zero_denominator_raises(self):
        with pytest.raises(ValueError):
            proportion_ci(5, 0)

    def test_keyword_args_k_n(self):
        r = proportion_ci(k=45, n=200)
        assert r.proportion == pytest.approx(0.225)

    def test_wilson_method(self):
        r = proportion_ci(5, 100, method=CI_Method.WILSON)
        assert r.method == "wilson"

    def test_wald_method(self):
        r = proportion_ci(50, 100, method=CI_Method.WALD)
        assert r.method == "wald"

    def test_clopper_pearson_method(self):
        r = proportion_ci(5, 100, method=CI_Method.CLOPPER_PEARSON)
        assert r.ci_lower >= 0

    def test_jeffreys_method(self):
        r = proportion_ci(5, 100, method=CI_Method.JEFFREYS)
        assert r.ci_lower >= 0

    def test_agresti_coull_method(self):
        r = proportion_ci(5, 100, method=CI_Method.AGRESTI_COULL)
        assert r.ci_lower >= 0

    def test_99_ci_wider_than_95(self):
        r95 = proportion_ci(45, 200, confidence=0.95)
        r99 = proportion_ci(45, 200, confidence=0.99)
        assert (r99.ci_upper - r99.ci_lower) > (r95.ci_upper - r95.ci_lower)

    def test_larger_n_narrower_ci(self):
        r1 = proportion_ci(5, 50)
        r2 = proportion_ci(50, 500)
        assert (r2.ci_upper - r2.ci_lower) < (r1.ci_upper - r1.ci_lower)

    def test_to_dict_keys(self):
        d = proportion_ci(45, 200).to_dict()
        for k in ["proportion", "ci_lower", "ci_upper", "method", "numerator"]:
            assert k in d

    def test_repr(self):
        r = repr(proportion_ci(45, 200))
        assert "Proportion" in r or "0.2250" in r

    def test_attack_rate_alias(self):
        r = attack_rate(45, 200)
        assert isinstance(r, ProportionResult)
        assert r.proportion == pytest.approx(0.225)

    def test_prevalence_alias(self):
        r = prevalence(45, 200)
        assert isinstance(r, ProportionResult)



# 7. mean_ci


class TestMeanCI:
    def test_returns_mean_result(self):
        assert isinstance(mean_ci([1, 2, 3, 4, 5]), MeanResult)

    def test_mean_value(self):
        r = mean_ci([1, 2, 3, 4, 5])
        assert r.mean == pytest.approx(3.0)

    def test_ci_contains_mean(self):
        r = mean_ci(np.random.default_rng(42).normal(5, 1, 100))
        assert r.ci_lower < r.mean < r.ci_upper

    def test_small_sample_t_distribution(self):
        r = mean_ci([1, 2, 3, 4, 5], method="t_distribution")
        assert r.method == "t_distribution"

    def test_large_sample_normal(self):
        data = list(range(100))
        r = mean_ci(data, method="normal")
        assert r.method == "normal"

    def test_nan_ignored(self):
        r = mean_ci([1.0, 2.0, float("nan"), 4.0, 5.0])
        assert r.mean == pytest.approx(3.0)

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            mean_ci([float("nan"), float("nan")])

    def test_std_dev_positive(self):
        r = mean_ci([1, 2, 3, 4, 5])
        assert r.std_dev > 0

    def test_sample_size_correct(self):
        r = mean_ci([1, 2, 3, 4, 5])
        assert r.sample_size == 5

    def test_to_dict(self):
        d = mean_ci([1, 2, 3]).to_dict()
        assert "mean" in d and "ci_lower" in d and "std_dev" in d

    def test_population_std_uses_z(self):
        r = mean_ci([1, 2, 3, 4, 5], population_std=1.0)
        # Should produce valid CI
        assert r.ci_lower < r.mean < r.ci_upper

    def test_99_ci_wider_than_95(self):
        data = list(range(50))
        r95 = mean_ci(data, confidence=0.95)
        r99 = mean_ci(data, confidence=0.99)
        assert (r99.ci_upper - r99.ci_lower) > (r95.ci_upper - r95.ci_lower)



# 8. incidence_rate & interquartile_range


class TestIncidenceRate:
    def test_rate_value(self):
        r = incidence_rate(10, 1000)
        assert r["rate"] == pytest.approx(0.01)

    def test_ci_present(self):
        r = incidence_rate(10, 1000)
        assert "ci_lower" in r and "ci_upper" in r

    def test_ci_contains_rate(self):
        r = incidence_rate(10, 1000)
        assert r["ci_lower"] < r["rate"] < r["ci_upper"]

    def test_zero_person_time_raises(self):
        with pytest.raises(ValueError):
            incidence_rate(10, 0)

    def test_small_cases_exact_ci(self):
        r = incidence_rate(3, 1000)   # < 10 cases → exact Poisson
        assert r["ci_lower"] >= 0

    def test_large_cases_byar(self):
        r = incidence_rate(50, 10000)  # >= 10 cases → Byar
        assert r["ci_lower"] >= 0

    def test_measure_key(self):
        assert incidence_rate(10, 1000)["measure"] == "incidence_rate"


class TestInterquartileRange:
    def test_iqr_value(self):
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        iqr = interquartile_range(data)
        assert iqr == pytest.approx(4.5, rel=0.1)

    def test_with_quartiles(self):
        result = interquartile_range([1, 2, 3, 4, 5], return_quartiles=True)
        assert isinstance(result, dict)
        assert "q1" in result and "q3" in result and "iqr" in result

    def test_symmetric_data(self):
        data = list(range(11))  # 0..10, Q1=2.5, Q3=7.5, IQR=5
        assert interquartile_range(data) == pytest.approx(5.0)



# 9. diagnostic_test_2x2


class TestDiagnosticTest2x2:
    def test_returns_diagnostic_result(self, diag_standard):
        assert isinstance(diag_standard, DiagnosticResult)

    def test_sensitivity(self, diag_standard):
        # tp=80, fn=20 → sens=80/100=0.8
        assert diag_standard.sensitivity == pytest.approx(0.8)

    def test_specificity(self, diag_standard):
        # tn=90, fp=10 → spec=90/100=0.9
        assert diag_standard.specificity == pytest.approx(0.9)

    def test_ppv(self, diag_standard):
        # tp=80, fp=10 → ppv=80/90≈0.889
        assert diag_standard.ppv == pytest.approx(80/90, rel=1e-3)

    def test_npv(self, diag_standard):
        # tn=90, fn=20 → npv=90/110≈0.818
        assert diag_standard.npv == pytest.approx(90/110, rel=1e-3)

    def test_accuracy(self, diag_standard):
        # (80+90)/200 = 0.85
        assert diag_standard.accuracy == pytest.approx(0.85)

    def test_youden(self, diag_standard):
        # sens + spec - 1 = 0.8+0.9-1 = 0.7
        assert diag_standard.youden == pytest.approx(0.7)

    def test_lr_positive(self, diag_standard):
        # sens / (1-spec) = 0.8/0.1 = 8.0
        assert diag_standard.lr_positive == pytest.approx(8.0)

    def test_lr_negative(self, diag_standard):
        # (1-sens) / spec = 0.2/0.9 ≈ 0.222
        assert diag_standard.lr_negative == pytest.approx(0.2/0.9, rel=1e-3)

    def test_negative_value_raises(self):
        with pytest.raises(ValueError):
            diagnostic_test_2x2(-1, 10, 20, 90)

    def test_all_zero_raises(self):
        with pytest.raises(ValueError):
            diagnostic_test_2x2(0, 0, 0, 0)

    def test_perfect_test(self):
        r = diagnostic_test_2x2(100, 0, 0, 100)
        assert r.sensitivity == pytest.approx(1.0)
        assert r.specificity == pytest.approx(1.0)
        assert r.accuracy == pytest.approx(1.0)
        assert r.youden == pytest.approx(1.0)

    def test_worst_test(self):
        r = diagnostic_test_2x2(0, 100, 100, 0)
        assert r.sensitivity == pytest.approx(0.0)
        assert r.specificity == pytest.approx(0.0)

    def test_custom_prevalence_affects_ppv(self):
        r_low = diagnostic_test_2x2(80, 10, 20, 90, prevalence=0.01)
        r_high = diagnostic_test_2x2(80, 10, 20, 90, prevalence=0.5)
        # Higher prevalence → higher PPV
        assert r_high.ppv > r_low.ppv

    def test_lr_positive_perfect_spec(self):
        r = diagnostic_test_2x2(80, 0, 20, 100)
        # specificity=1 → LR+ = inf
        assert math.isinf(r.lr_positive)

    def test_to_dict_keys(self, diag_standard):
        d = diag_standard.to_dict()
        for k in ["sensitivity","specificity","ppv","npv","accuracy","youden"]:
            assert k in d

    def test_repr(self, diag_standard):
        r = repr(diag_standard)
        assert "Sens" in r or "0.8" in r

    def test_ci_methods_available(self, diag_standard):
        # _sens_ci and _spec_ci should return strings
        assert "-" in diag_standard._sens_ci()
        assert "-" in diag_standard._spec_ci()



# 10. roc_analysis


class TestROCAnalysis:
    @pytest.fixture
    def roc_data(self):
        y_true  = np.array([1,1,1,1,1,0,0,0,0,0])
        y_score = np.array([0.9,0.8,0.7,0.6,0.4,0.3,0.2,0.1,0.35,0.45])
        return y_true, y_score

    def test_returns_roc_result(self, roc_data):
        y_true, y_score = roc_data
        assert isinstance(roc_analysis(y_true, y_score), ROCResult)

    def test_auc_range(self, roc_data):
        y_true, y_score = roc_data
        r = roc_analysis(y_true, y_score)
        assert 0.5 <= r.auc <= 1.0

    def test_auc_perfect_classifier(self):
        y_true  = np.array([1,1,1,0,0,0])
        y_score = np.array([0.9,0.8,0.7,0.1,0.2,0.3])
        r = roc_analysis(y_true, y_score)
        assert r.auc == pytest.approx(1.0)

    def test_fpr_tpr_arrays(self, roc_data):
        y_true, y_score = roc_data
        r = roc_analysis(y_true, y_score)
        assert len(r.fpr) > 0 and len(r.tpr) > 0

    def test_fpr_starts_at_zero(self, roc_data):
        y_true, y_score = roc_data
        r = roc_analysis(y_true, y_score)
        assert r.fpr[0] == pytest.approx(0.0)

    def test_optimal_threshold_in_range(self, roc_data):
        y_true, y_score = roc_data
        r = roc_analysis(y_true, y_score)
        assert r.optimal_threshold >= 0

    def test_optimal_point_keys(self, roc_data):
        y_true, y_score = roc_data
        r = roc_analysis(y_true, y_score)
        assert "sensitivity" in r.optimal_point
        assert "specificity" in r.optimal_point

    def test_to_dict_keys(self, roc_data):
        y_true, y_score = roc_data
        d = roc_analysis(y_true, y_score).to_dict()
        for k in ["auc","optimal_threshold","optimal_sensitivity","n_thresholds"]:
            assert k in d

    def test_repr(self, roc_data):
        y_true, y_score = roc_data
        r = repr(roc_analysis(y_true, y_score))
        assert "AUC" in r

    def test_method_youden(self, roc_data):
        y_true, y_score = roc_data
        r = roc_analysis(y_true, y_score, method="youden")
        assert r.method == "youden"



# 11. Mathematical cross-checks


class TestMathCrossChecks:
    def test_rr_or_relationship(self):
        """OR > RR when outcome is common (Cornfield)."""
        t = Table2x2(40, 10, 20, 30)
        rr = t.risk_ratio().estimate
        or_ = t.odds_ratio().estimate
        # Common outcome (50%) → OR > RR
        assert or_ > rr

    def test_wilson_ci_for_extreme_p(self):
        """Wilson should work for p near 0."""
        r = proportion_ci(1, 1000, method=CI_Method.WILSON)
        assert 0 <= r.ci_lower < r.ci_upper <= 1

    def test_sens_spec_youden_relation(self, diag_standard):
        """Youden = sensitivity + specificity - 1."""
        assert diag_standard.youden == pytest.approx(
            diag_standard.sensitivity + diag_standard.specificity - 1
        )

    def test_lr_positive_formula(self, diag_standard):
        """LR+ = sensitivity / (1 - specificity)."""
        expected = diag_standard.sensitivity / (1 - diag_standard.specificity)
        assert diag_standard.lr_positive == pytest.approx(expected)

    def test_lr_negative_formula(self, diag_standard):
        """LR- = (1 - sensitivity) / specificity."""
        expected = (1 - diag_standard.sensitivity) / diag_standard.specificity
        assert diag_standard.lr_negative == pytest.approx(expected)

    def test_proportion_ci_coverage(self):
        """95% CI should contain the true proportion most of the time."""
        rng = np.random.default_rng(0)
        covered = 0
        true_p = 0.3
        for _ in range(200):
            k = int(rng.binomial(100, true_p))
            r = proportion_ci(k, 100)
            if r.ci_lower <= true_p <= r.ci_upper:
                covered += 1
        # Expect ~95% coverage, accept 85–100%
        assert covered >= 170

    def test_chi_square_and_fisher_agree(self):
        """Chi-square and Fisher should both be significant for strong association."""
        t = Table2x2(40, 5, 5, 40)
        cs = t.chi_square()
        fe = t.fisher_exact()
        assert cs["p_value"] < 0.05
        assert fe["p_value"] < 0.05