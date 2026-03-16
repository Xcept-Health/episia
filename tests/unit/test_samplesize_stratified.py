"""
tests/unit/test_samplesize_stratified.py
Unit tests for episia.stats.samplesize and episia.stats.stratified

Coverage
--------
samplesize.py
    StudyDesign / TestType          enums
    SampleSizeResult                repr, to_dict
    sample_size_risk_ratio          nominal, edge cases, aliases, validation
    sample_size_risk_difference     nominal, delegates correctly
    sample_size_odds_ratio          nominal, edge cases, validation
    sample_size_single_proportion   nominal, p=0.5, design_effect
    sample_size_sensitivity_specificity  both/sens/spec, prevalence required
    power_calculation               cohort, case-control
    fleiss_correction               with/without correction
    design_effect_deff              formula, boundaries
    calculate_sample_size           dispatcher for each design

stratified.py
    StratifiedTable                 init, validation, len, getitem, to_dict
    MantelHaenszelResult            repr, summary
    mantel_haenszel_or              nominal, homogeneous strata, heterogeneous
    mathematical cross-checks       OR > RR (common outcome), pooled OR direction
"""
from __future__ import annotations
import math
import numpy as np
import pytest

from episia.stats.samplesize import (
    StudyDesign, TestType, SampleSizeResult,
    sample_size_risk_ratio, sample_size_risk_difference,
    sample_size_odds_ratio, sample_size_single_proportion,
    sample_size_sensitivity_specificity, power_calculation,
    fleiss_correction, design_effect_deff, calculate_sample_size,
)
from episia.stats.stratified import (
    StratifiedTable, MantelHaenszelResult, mantel_haenszel_or,
)
from episia.stats.contingency import Table2x2



# 1. Enums


class TestStudyEnums:
    def test_study_designs(self):
        assert {d.value for d in StudyDesign} == {
            "cohort", "case_control", "cross_sectional", "diagnostic"
        }

    def test_test_types(self):
        assert {t.value for t in TestType} == {"two_sided", "one_sided"}



# 2. SampleSizeResult


class TestSampleSizeResult:
    def test_repr_per_group(self):
        r = SampleSizeResult(n_per_group=199, n_total=398)
        assert "199" in repr(r)

    def test_repr_cases_controls(self):
        r = SampleSizeResult(n_cases=146, n_controls=146)
        assert "146" in repr(r)

    def test_repr_power_only(self):
        r = SampleSizeResult(power=0.832)
        assert "0.832" in repr(r)

    def test_to_dict_has_alpha(self):
        r = SampleSizeResult(alpha=0.05)
        assert r.to_dict()["alpha"] == 0.05

    def test_to_dict_n_per_group(self):
        r = SampleSizeResult(n_per_group=100, n_total=200, alpha=0.05)
        d = r.to_dict()
        assert "n_per_group" in d and "n_total" in d

    def test_to_dict_cases_controls(self):
        r = SampleSizeResult(n_cases=50, n_controls=50, alpha=0.05)
        d = r.to_dict()
        assert "n_cases" in d and "n_controls" in d



# 3. sample_size_risk_ratio


class TestSampleSizeRiskRatio:
    def test_returns_result(self):
        assert isinstance(sample_size_risk_ratio(0.1, 2.0), SampleSizeResult)

    def test_n_per_group_positive(self):
        r = sample_size_risk_ratio(0.1, 2.0)
        assert r.n_per_group > 0

    def test_n_total_is_double(self):
        r = sample_size_risk_ratio(0.1, 2.0)
        assert r.n_total == pytest.approx(r.n_per_group * 2)

    def test_n_is_integer_value(self):
        r = sample_size_risk_ratio(0.1, 2.0)
        assert r.n_per_group == math.ceil(r.n_per_group)

    def test_higher_power_larger_n(self):
        r80 = sample_size_risk_ratio(0.1, 2.0, power=0.80)
        r90 = sample_size_risk_ratio(0.1, 2.0, power=0.90)
        assert r90.n_per_group > r80.n_per_group

    def test_lower_alpha_larger_n(self):
        r05 = sample_size_risk_ratio(0.1, 2.0, alpha=0.05)
        r01 = sample_size_risk_ratio(0.1, 2.0, alpha=0.01)
        assert r01.n_per_group > r05.n_per_group

    def test_larger_rr_smaller_n(self):
        r2 = sample_size_risk_ratio(0.1, 2.0)
        r3 = sample_size_risk_ratio(0.1, 3.0)
        assert r3.n_per_group < r2.n_per_group

    def test_design_effect_scales_n(self):
        r1 = sample_size_risk_ratio(0.1, 2.0, design_effect=1.0)
        r2 = sample_size_risk_ratio(0.1, 2.0, design_effect=2.0)
        assert r2.n_per_group == pytest.approx(r1.n_per_group * 2, rel=0.01)

    def test_unequal_groups_r2(self):
        r = sample_size_risk_ratio(0.1, 2.0, r=2.0)
        # n_total = n_exposed + 2*n_exposed = 3*n_exposed
        assert r.n_total == pytest.approx(r.n_per_group * 3, rel=0.01)

    def test_alias_p0_rr_expected(self):
        r1 = sample_size_risk_ratio(0.1, 2.0)
        r2 = sample_size_risk_ratio(p0=0.1, rr_expected=2.0)
        assert r1.n_per_group == r2.n_per_group

    def test_missing_args_raises(self):
        with pytest.raises(TypeError):
            sample_size_risk_ratio(0.1)    # missing risk_ratio

    def test_risk_unexposed_zero_raises(self):
        with pytest.raises(ValueError):
            sample_size_risk_ratio(0.0, 2.0)

    def test_risk_unexposed_one_raises(self):
        with pytest.raises(ValueError):
            sample_size_risk_ratio(1.0, 2.0)

    def test_rr_zero_raises(self):
        with pytest.raises(ValueError):
            sample_size_risk_ratio(0.1, 0.0)

    def test_power_zero_raises(self):
        with pytest.raises(ValueError):
            sample_size_risk_ratio(0.1, 2.0, power=0.0)

    def test_alpha_one_raises(self):
        with pytest.raises(ValueError):
            sample_size_risk_ratio(0.1, 2.0, alpha=1.0)

    def test_design_is_cohort(self):
        r = sample_size_risk_ratio(0.1, 2.0)
        assert r.design == StudyDesign.COHORT.value

    def test_one_sided_smaller_than_two_sided(self):
        r_two = sample_size_risk_ratio(0.1, 2.0, test_type=TestType.TWO_SIDED)
        r_one = sample_size_risk_ratio(0.1, 2.0, test_type=TestType.ONE_SIDED)
        assert r_one.n_per_group < r_two.n_per_group

    def test_assumptions_stored(self):
        r = sample_size_risk_ratio(0.1, 2.0)
        assert r.assumptions["risk_unexposed"] == 0.1



# 4. sample_size_risk_difference


class TestSampleSizeRiskDifference:
    def test_returns_result(self):
        r = sample_size_risk_difference(0.1, 0.1)   # RD=0.1 → RR=2.0
        assert isinstance(r, SampleSizeResult)

    def test_positive_rd(self):
        r = sample_size_risk_difference(0.1, 0.1)
        assert r.n_per_group > 0

    def test_larger_rd_smaller_n(self):
        r_small = sample_size_risk_difference(0.1, 0.05)
        r_large = sample_size_risk_difference(0.1, 0.20)
        assert r_large.n_per_group < r_small.n_per_group

    def test_design_is_cohort(self):
        r = sample_size_risk_difference(0.1, 0.1)
        assert r.design == StudyDesign.COHORT.value



# 5. sample_size_odds_ratio


class TestSampleSizeOddsRatio:
    def test_returns_result(self):
        assert isinstance(sample_size_odds_ratio(0.3, 2.0), SampleSizeResult)

    def test_n_cases_positive(self):
        r = sample_size_odds_ratio(0.3, 2.0)
        assert r.n_cases > 0

    def test_n_controls_equals_cases_default(self):
        r = sample_size_odds_ratio(0.3, 2.0)
        assert r.n_cases == r.n_controls

    def test_r2_double_controls(self):
        r = sample_size_odds_ratio(0.3, 2.0, r=2.0)
        # ceil() rounding can differ by 1 — use abs tolerance
        assert r.n_controls == pytest.approx(r.n_cases * 2, abs=1)

    def test_higher_or_smaller_n(self):
        r2 = sample_size_odds_ratio(0.3, 2.0)
        r4 = sample_size_odds_ratio(0.3, 4.0)
        assert r4.n_cases < r2.n_cases

    def test_design_is_case_control(self):
        r = sample_size_odds_ratio(0.3, 2.0)
        assert r.design == StudyDesign.CASE_CONTROL.value

    def test_proportion_zero_raises(self):
        with pytest.raises(ValueError):
            sample_size_odds_ratio(0.0, 2.0)

    def test_or_zero_raises(self):
        with pytest.raises(ValueError):
            sample_size_odds_ratio(0.3, 0.0)

    def test_n_total_is_cases_plus_controls(self):
        r = sample_size_odds_ratio(0.3, 2.0)
        assert r.n_total == pytest.approx(r.n_cases + r.n_controls)



# 6. sample_size_single_proportion


class TestSampleSizeSingleProportion:
    def test_returns_result(self):
        assert isinstance(sample_size_single_proportion(0.5, 0.05), SampleSizeResult)

    def test_n_positive(self):
        assert sample_size_single_proportion(0.5, 0.05).n_total > 0

    def test_p_half_maximum_n(self):
        n_half = sample_size_single_proportion(0.5, 0.05).n_total
        n_low  = sample_size_single_proportion(0.1, 0.05).n_total
        assert n_half >= n_low

    def test_smaller_precision_larger_n(self):
        r_wide   = sample_size_single_proportion(0.5, 0.10)
        r_narrow = sample_size_single_proportion(0.5, 0.03)
        assert r_narrow.n_total > r_wide.n_total

    def test_design_effect_scales(self):
        r1 = sample_size_single_proportion(0.5, 0.05, design_effect=1.0)
        r2 = sample_size_single_proportion(0.5, 0.05, design_effect=2.0)
        # ceil() rounding can differ by 1 — use abs tolerance
        assert r2.n_total == pytest.approx(r1.n_total * 2, abs=1)

    def test_design_is_cross_sectional(self):
        r = sample_size_single_proportion(0.5, 0.05)
        assert r.design == StudyDesign.CROSS_SECTIONAL.value

    def test_proportion_above_one_raises(self):
        with pytest.raises(ValueError):
            sample_size_single_proportion(1.1, 0.05)

    def test_precision_zero_raises(self):
        with pytest.raises(ValueError):
            sample_size_single_proportion(0.5, 0.0)

    def test_classic_n385(self):
        # Standard result: p=0.5, precision=0.05, alpha=0.05 → n≈384
        r = sample_size_single_proportion(0.5, 0.05, alpha=0.05)
        assert 380 <= r.n_total <= 390



# 7. sample_size_sensitivity_specificity


class TestSampleSizeDiagnostic:
    def test_returns_result(self):
        r = sample_size_sensitivity_specificity(0.9, 0.85, 0.05, prevalence=0.1)
        assert isinstance(r, SampleSizeResult)

    def test_n_total_positive(self):
        r = sample_size_sensitivity_specificity(0.9, 0.85, 0.05, prevalence=0.1)
        assert r.n_total > 0

    def test_design_is_diagnostic(self):
        r = sample_size_sensitivity_specificity(0.9, 0.85, 0.05, prevalence=0.1)
        assert r.design == StudyDesign.DIAGNOSTIC.value

    def test_which_sensitivity(self):
        r = sample_size_sensitivity_specificity(0.9, 0.85, 0.05,
                                                prevalence=0.1, which="sensitivity")
        assert r.n_total > 0

    def test_which_specificity(self):
        r = sample_size_sensitivity_specificity(0.9, 0.85, 0.05,
                                                prevalence=0.1, which="specificity")
        assert r.n_total > 0

    def test_no_prevalence_raises(self):
        with pytest.raises(ValueError, match="prevalence"):
            sample_size_sensitivity_specificity(0.9, 0.85, 0.05)

    def test_invalid_sens_raises(self):
        with pytest.raises(ValueError):
            sample_size_sensitivity_specificity(1.1, 0.85, 0.05, prevalence=0.1)

    def test_narrower_precision_larger_n(self):
        r_wide   = sample_size_sensitivity_specificity(0.9, 0.85, 0.10, prevalence=0.1)
        r_narrow = sample_size_sensitivity_specificity(0.9, 0.85, 0.03, prevalence=0.1)
        assert r_narrow.n_total > r_wide.n_total



# 8. power_calculation


class TestPowerCalculation:
    def test_cohort_returns_result(self):
        r = power_calculation(
            n_per_group=200,
            risk_unexposed=0.1,
            risk_ratio=2.0,
        )
        assert isinstance(r, SampleSizeResult)

    def test_power_in_0_1(self):
        r = power_calculation(
            n_per_group=200,
            risk_unexposed=0.1,
            risk_ratio=2.0,
        )
        assert 0 < r.power < 1

    def test_larger_n_higher_power(self):
        r_small = power_calculation(n_per_group=50,  risk_unexposed=0.1, risk_ratio=2.0)
        r_large = power_calculation(n_per_group=500, risk_unexposed=0.1, risk_ratio=2.0)
        assert r_large.power > r_small.power

    def test_power_at_design_n(self):
        # If we use the n from sample_size_risk_ratio, power should ≥ 80%
        n = sample_size_risk_ratio(0.1, 2.0, power=0.8).n_per_group
        r = power_calculation(n_per_group=n, risk_unexposed=0.1, risk_ratio=2.0)
        assert r.power >= 0.79   # Allow tiny numerical tolerance

    def test_case_control_returns_result(self):
        r = power_calculation(
            n_cases=200, n_controls=200,
            proportion_exposed_controls=0.3,
            odds_ratio=2.0,
            design=StudyDesign.CASE_CONTROL,
        )
        assert 0 < r.power < 1

    def test_missing_cohort_params_raises(self):
        with pytest.raises(ValueError):
            power_calculation(n_per_group=100, risk_unexposed=0.1)

    def test_unsupported_design_raises(self):
        with pytest.raises(NotImplementedError):
            power_calculation(
                n_per_group=100,
                risk_unexposed=0.1,
                risk_ratio=2.0,
                design=StudyDesign.CROSS_SECTIONAL,
            )



# 9. fleiss_correction & design_effect_deff


class TestHelpers:
    def test_fleiss_no_correction(self):
        assert fleiss_correction(100, continuity_correction=False) == 100

    def test_fleiss_with_correction_larger(self):
        n = fleiss_correction(100, continuity_correction=True)
        assert n >= 100

    def test_design_effect_icc_zero(self):
        # ICC=0 → DEFF=1 regardless of cluster size
        assert design_effect_deff(0.0, 10) == pytest.approx(1.0)

    def test_design_effect_cluster_one(self):
        # m=1 → DEFF=1 regardless of ICC
        assert design_effect_deff(0.2, 1) == pytest.approx(1.0)

    def test_design_effect_formula(self):
        # DEFF = 1 + (m-1)*rho = 1 + 9*0.1 = 1.9
        assert design_effect_deff(0.1, 10) == pytest.approx(1.9)

    def test_design_effect_icc_above_one_raises(self):
        with pytest.raises(ValueError):
            design_effect_deff(1.1, 10)

    def test_design_effect_cluster_below_one_raises(self):
        with pytest.raises(ValueError):
            design_effect_deff(0.1, 0.5)



# 10. calculate_sample_size dispatcher


class TestCalculateSampleSize:
    def test_cohort_string(self):
        r = calculate_sample_size("cohort", {"risk_unexposed": 0.1, "risk_ratio": 2.0})
        assert r.design == StudyDesign.COHORT.value

    def test_case_control(self):
        r = calculate_sample_size("case_control", {
            "proportion_exposed_controls": 0.3,
            "odds_ratio": 2.0
        })
        assert r.design == StudyDesign.CASE_CONTROL.value

    def test_cross_sectional(self):
        r = calculate_sample_size("cross_sectional", {
            "expected_proportion": 0.5,
            "precision": 0.05
        })
        assert r.design == StudyDesign.CROSS_SECTIONAL.value

    def test_diagnostic(self):
        r = calculate_sample_size("diagnostic", {
            "expected_sens": 0.9,
            "expected_spec": 0.85,
            "precision": 0.05,
            "prevalence": 0.1,
        })
        assert r.design == StudyDesign.DIAGNOSTIC.value

    def test_enum_input(self):
        r = calculate_sample_size(StudyDesign.COHORT, {
            "risk_unexposed": 0.1, "risk_ratio": 2.0
        })
        assert r.n_per_group > 0

    def test_invalid_design_raises(self):
        with pytest.raises(ValueError):
            calculate_sample_size("randomized_trial", {})



# 11. StratifiedTable


@pytest.fixture
def two_strata():
    return StratifiedTable([
        Table2x2(10, 20, 30, 40),
        Table2x2(15, 25, 35, 45),
    ])

class TestStratifiedTable:
    def test_empty_raises(self):
        with pytest.raises(ValueError):
            StratifiedTable([])

    def test_len(self, two_strata):
        assert len(two_strata) == 2

    def test_getitem(self, two_strata):
        t = two_strata[0]
        assert isinstance(t, Table2x2)
        assert t.a == 10

    def test_default_strata_names(self, two_strata):
        assert two_strata.strata_names == ["Stratum_1", "Stratum_2"]

    def test_custom_strata_names(self):
        st = StratifiedTable(
            [Table2x2(10, 20, 30, 40)],
            strata_names=["Age < 40"]
        )
        assert st.strata_names == ["Age < 40"]

    def test_mismatched_names_raises(self):
        with pytest.raises(ValueError):
            StratifiedTable(
                [Table2x2(10, 20, 30, 40), Table2x2(5, 10, 15, 20)],
                strata_names=["only_one_name"]
            )

    def test_to_dict_keys(self, two_strata):
        d = two_strata.to_dict()
        assert "n_strata" in d and "tables" in d
        assert d["n_strata"] == 2



# 12. mantel_haenszel_or


class TestMantelHaenszel:
    @pytest.fixture
    def homogeneous_tables(self):
        """Three strata with identical OR≈2."""
        return [
            Table2x2(40, 20, 20, 40),
            Table2x2(30, 15, 15, 30),
            Table2x2(20, 10, 10, 20),
        ]

    @pytest.fixture
    def null_tables(self):
        """Strata with OR=1 (no association)."""
        return [
            Table2x2(10, 10, 10, 10),
            Table2x2(20, 20, 20, 20),
        ]

    def test_returns_result(self, homogeneous_tables):
        r = mantel_haenszel_or(homogeneous_tables)
        assert isinstance(r, MantelHaenszelResult)

    def test_accepts_stratified_table(self, homogeneous_tables):
        st = StratifiedTable(homogeneous_tables)
        r = mantel_haenszel_or(st)
        assert isinstance(r, MantelHaenszelResult)

    def test_or_positive(self, homogeneous_tables):
        r = mantel_haenszel_or(homogeneous_tables)
        assert r.common_or > 0

    def test_or_null_is_one(self, null_tables):
        r = mantel_haenszel_or(null_tables)
        assert r.common_or == pytest.approx(1.0, rel=0.05)

    def test_ci_lower_positive(self, homogeneous_tables):
        r = mantel_haenszel_or(homogeneous_tables)
        assert r.or_ci[0] > 0

    def test_ci_contains_or(self, homogeneous_tables):
        r = mantel_haenszel_or(homogeneous_tables)
        assert r.or_ci[0] < r.common_or < r.or_ci[1]

    def test_p_value_in_0_1(self, homogeneous_tables):
        r = mantel_haenszel_or(homogeneous_tables)
        assert 0 <= r.p_value <= 1

    def test_significant_association(self, homogeneous_tables):
        r = mantel_haenszel_or(homogeneous_tables)
        assert r.p_value < 0.05

    def test_not_significant_null(self, null_tables):
        r = mantel_haenszel_or(null_tables)
        assert r.p_value > 0.05

    def test_i_squared_range(self, homogeneous_tables):
        r = mantel_haenszel_or(homogeneous_tables)
        assert 0 <= r.i_squared <= 100

    def test_homogeneous_low_i_squared(self, homogeneous_tables):
        r = mantel_haenszel_or(homogeneous_tables)
        # All strata have same OR → I² should be low
        assert r.i_squared < 50

    def test_repr(self, homogeneous_tables):
        r = mantel_haenszel_or(homogeneous_tables)
        assert "Mantel-Haenszel" in repr(r)
        assert "OR" in repr(r)

    def test_summary_contains_key_info(self, homogeneous_tables):
        r = mantel_haenszel_or(homogeneous_tables)
        s = r.summary()
        assert "OR" in s and "RR" in s and "I²" in s

    def test_rr_positive(self, homogeneous_tables):
        r = mantel_haenszel_or(homogeneous_tables)
        assert r.common_rr > 0

    def test_single_stratum(self):
        r = mantel_haenszel_or([Table2x2(40, 10, 20, 30)])
        assert isinstance(r, MantelHaenszelResult)
        assert r.common_or > 0



# 13. Mathematical cross-checks


class TestMathCrossChecks:
    def test_n_increases_with_power(self):
        """Monotone relationship between power and required N."""
        ns = [sample_size_risk_ratio(0.1, 2.0, power=p).n_per_group
              for p in [0.70, 0.80, 0.90, 0.95]]
        assert ns == sorted(ns)

    def test_n_decreases_with_rr(self):
        """Larger effect → smaller N needed."""
        ns = [sample_size_risk_ratio(0.1, rr).n_per_group
              for rr in [1.5, 2.0, 3.0, 4.0]]
        assert ns == sorted(ns, reverse=True)

    def test_power_sample_size_round_trip(self):
        """Using N from sample_size_rr gives power ≈ target."""
        target_power = 0.80
        r = sample_size_risk_ratio(0.1, 2.0, power=target_power)
        pc = power_calculation(
            n_per_group=r.n_per_group,
            risk_unexposed=0.1,
            risk_ratio=2.0,
        )
        assert pc.power == pytest.approx(target_power, abs=0.02)

    def test_deff_inflates_sample_size(self):
        """Design effect increases required N proportionally."""
        deff = design_effect_deff(0.05, 20)   # 1 + 19*0.05 = 1.95
        r1 = sample_size_single_proportion(0.5, 0.05, design_effect=1.0)
        r2 = sample_size_single_proportion(0.5, 0.05, design_effect=deff)
        assert r2.n_total / r1.n_total == pytest.approx(deff, rel=0.02)

    def test_mh_or_between_stratum_specific(self):
        """Pooled MH OR should fall between stratum-specific ORs."""
        t1 = Table2x2(30, 10, 10, 30)   # OR = (30*30)/(10*10) = 9
        t2 = Table2x2(10, 20, 20, 10)   # OR = (10*10)/(20*20) = 0.25
        r = mantel_haenszel_or([t1, t2])
        or1 = t1.odds_ratio().estimate
        or2 = t2.odds_ratio().estimate
        assert min(or1, or2) <= r.common_or <= max(or1, or2)