"""
episia.compatibility.coding - CodingComparator

Quantifies the impact of coding system differences (e.g. ICD-10 vs ICD-11)
on epidemiological measures: prevalence, incidence rate, risk ratio, odds ratio,
attributable risk, and population attributable fraction.

Two comparison modes
--------------------
SAME_COHORT (default)
    dataset_v1 and dataset_v2 represent the SAME patients coded differently.
    Row count must be identical. Paired analysis.

INDEPENDENT
    dataset_v1 and dataset_v2 are DISTINCT cohorts (e.g. before/after ICD
    transition, or two different registries). Row counts may differ.
    Unpaired analysis — RR, OR, AR are computed across cohorts.
    Use with caution: confounding is not controlled.

No duplication: all statistical computations delegate to episia.stats.
Validation delegates to episia.core.validator.

Typical usage
-------------
    from episia.compatibility.coding import CodingComparator, ComparisonMode

    # Same cohort, two codings
    comp = CodingComparator(
        dataset_v1=df_icd10,
        dataset_v2=df_icd11,
        outcome_col="disease",
        exposure_col="exposure",
        person_time_col="follow_up_days",
        coding_system_v1="ICD-10",
        coding_system_v2="ICD-11",
    )
    result = comp.run()

    # Two independent cohorts
    from episia.compatibility.coding import ComparisonMode
    comp = CodingComparator(
        dataset_v1=df_before,
        dataset_v2=df_after,
        outcome_col="death",
        exposure_col="treatment",
        mode=ComparisonMode.INDEPENDENT,
        coding_system_v1="Registry-2019",
        coding_system_v2="Registry-2023",
    )
    result = comp.run()
"""

from __future__ import annotations

import warnings
from enum import Enum
from typing import Optional

import pandas as pd

from episia.stats.contingency import from_dataframe as table_from_dataframe
from episia.stats.descriptive import prevalence as stats_prevalence
from episia.stats.descriptive import incidence_rate as stats_incidence_rate
from episia.core.validator import validate_binary_variable, validate_dataframe

from .results import CodingRobustnessResult, MeasureDelta

# Mode enum

class ComparisonMode(Enum):
    """
    SAME_COHORT : both datasets are the same patients coded differently.
                  Row counts must match.
    INDEPENDENT : two distinct cohorts compared across coding/time/system.
                  Row counts may differ.
    """
    SAME_COHORT = "same_cohort"
    INDEPENDENT = "independent"


# Internal helper

def _drop_nan(df: pd.DataFrame, cols: list[str], label: str) -> pd.DataFrame:
    before = len(df)
    df = df.dropna(subset=cols)
    lost = before - len(df)
    if lost:
        warnings.warn(
            f"{label}: {lost} row(s) dropped due to NaN in {cols}.",
            UserWarning,
            stacklevel=3,
        )
    return df

# CodingComparator

class CodingComparator:
    """
    Compare two datasets under different classification systems and quantify
    the impact on epidemiological measures.

    Delegates all statistical computations to episia.stats:
        prevalence        → episia.stats.descriptive.prevalence (Wilson CI)
        incidence_rate    → episia.stats.descriptive.incidence_rate (Byar / Poisson)
        risk_ratio        → episia.stats.contingency.Table2x2.risk_ratio (Wald CI)
        odds_ratio        → episia.stats.contingency.Table2x2.odds_ratio (Wald CI)
        attributable_risk → episia.stats.contingency.Table2x2.risk_difference
        pop_attr_frac     → episia.stats.contingency.Table2x2.attributable_fraction_population

    Measures computed
    -----------------
    Always:
        prevalence
    With exposure_col:
        risk_ratio, odds_ratio, attributable_risk, pop_attributable_frac
    With person_time_col:
        incidence_rate

    Parameters
    ----------
    dataset_v1 : pd.DataFrame
        First dataset. In SAME_COHORT mode: same patients as v2, coded
        differently. In INDEPENDENT mode: a distinct cohort.
    dataset_v2 : pd.DataFrame
        Second dataset.
    outcome_col : str
        Binary column (0/1) for disease/outcome. Must exist in both datasets.
    exposure_col : str, optional
        Binary column (0/1) for exposure. Enables RR, OR, AR, PAF.
    person_time_col : str, optional
        Numeric column for person-time (e.g. follow-up days).
        Enables incidence rate computation.
    coding_system_v1, coding_system_v2 : str
        Labels for the two systems (default "V1", "V2").
    mode : ComparisonMode
        SAME_COHORT (default) or INDEPENDENT. In SAME_COHORT mode the row
        counts of v1 and v2 must be equal.
    """

    def __init__(
        self,
        dataset_v1: pd.DataFrame,
        dataset_v2: pd.DataFrame,
        outcome_col: str,
        exposure_col: Optional[str] = None,
        person_time_col: Optional[str] = None,
        coding_system_v1: str = "V1",
        coding_system_v2: str = "V2",
        mode: ComparisonMode = ComparisonMode.SAME_COHORT,
    ) -> None:
        self._v1 = dataset_v1.copy()
        self._v2 = dataset_v2.copy()
        self.outcome_col = outcome_col
        self.exposure_col = exposure_col
        self.person_time_col = person_time_col
        self.coding_system_v1 = coding_system_v1
        self.coding_system_v2 = coding_system_v2
        self.mode = mode
        self._validate()

    
    # Validation

    def _validate(self) -> None:
        # Row count constraint only in SAME_COHORT mode
        if (self.mode == ComparisonMode.SAME_COHORT
                and len(self._v1) != len(self._v2)):
            raise ValueError(
                f"SAME_COHORT mode requires the same number of rows. "
                f"Got dataset_v1={len(self._v1)} rows, "
                f"dataset_v2={len(self._v2)} rows. "
                "Use ComparisonMode.INDEPENDENT for cohorts of different sizes."
            )

        for df, name in [(self._v1, "dataset_v1"), (self._v2, "dataset_v2")]:
            # Validate outcome_col presence
            if self.outcome_col not in df.columns:
                raise ValueError(
                    f"outcome_col '{self.outcome_col}' not found in {name}."
                )
            # Validate exposure_col presence
            if self.exposure_col and self.exposure_col not in df.columns:
                raise ValueError(
                    f"exposure_col '{self.exposure_col}' not found in {name}."
                )

        required = [self.outcome_col]
        if self.exposure_col:
            required.append(self.exposure_col)

        for df, name in [(self._v1, "dataset_v1"), (self._v2, "dataset_v2")]:
            validate_dataframe(df, required_columns=required, allow_nan=True,
                               min_rows=0)
            validate_binary_variable(df[self.outcome_col],
                                     f"{name}[{self.outcome_col}]")
            if self.exposure_col:
                validate_binary_variable(df[self.exposure_col],
                                         f"{name}[{self.exposure_col}]")

        if self.person_time_col:
            for df, name in [(self._v1, "dataset_v1"), (self._v2, "dataset_v2")]:
                if self.person_time_col not in df.columns:
                    raise ValueError(
                        f"person_time_col '{self.person_time_col}' "
                        f"not found in {name}."
                    )

    
    # Main entry point
    
    def run(self) -> CodingRobustnessResult:
        """
        Run the full robustness analysis.

        Returns
        -------
        CodingRobustnessResult
            Rich result object with .summary(), .plot(), .to_dataframe(),
            .to_dict(), .to_json() (via EpiResult base class).
        """
        base_cols = [self.outcome_col]
        if self.exposure_col:
            base_cols.append(self.exposure_col)
        if self.person_time_col:
            base_cols.append(self.person_time_col)

        v1 = _drop_nan(self._v1, base_cols, self.coding_system_v1)
        v2 = _drop_nan(self._v2, base_cols, self.coding_system_v2)

        k1 = int((v1[self.outcome_col] == 1).sum())
        k2 = int((v2[self.outcome_col] == 1).sum())

        # Empty dataset guard: return all-NaN result
        if len(v1) == 0 or len(v2) == 0:
            measures = ["prevalence"]
            if self.person_time_col:
                measures.append("incidence_rate")
            if self.exposure_col:
                measures += ["risk_ratio", "odds_ratio",
                              "attributable_risk", "pop_attributable_frac"]
            nan_deltas = [
                MeasureDelta.from_values(m, float("nan"), float("nan"))
                for m in measures
            ]
            return CodingRobustnessResult(
                coding_system_v1=self.coding_system_v1,
                coding_system_v2=self.coding_system_v2,
                n_v1=k1, n_v2=k2,
                deltas=nan_deltas,
                robustness_score=1.0,
                unstable_measures=[],
                metadata={
                    "n_rows_v1": 0, "n_rows_v2": 0,
                    "outcome_col": self.outcome_col,
                    "exposure_col": self.exposure_col,
                    "person_time_col": self.person_time_col,
                    "mode": self.mode.value,
                    "warning": "Empty dataset - all measures are NaN.",
                },
            )

        deltas: list[MeasureDelta] = []

        # Prevalence
        pr1 = stats_prevalence(k1, len(v1))
        pr2 = stats_prevalence(k2, len(v2))
        deltas.append(MeasureDelta.from_values(
            "prevalence",
            pr1.proportion, pr2.proportion,
            pr1.ci_lower, pr1.ci_upper,
            pr2.ci_lower, pr2.ci_upper,
            method=pr1.method,
        ))

        # Incidence rate
        if self.person_time_col:
            pt1 = float(v1[self.person_time_col].sum())
            pt2 = float(v2[self.person_time_col].sum())
            ir1 = stats_incidence_rate(k1, pt1)
            ir2 = stats_incidence_rate(k2, pt2)
            deltas.append(MeasureDelta.from_values(
                "incidence_rate",
                ir1.rate, ir2.rate,
                ir1.ci_lower, ir1.ci_upper,
                ir2.ci_lower, ir2.ci_upper,
                method=ir1.method,
            ))

        # Exposure-based measures
        if self.exposure_col:
            if self.mode == ComparisonMode.INDEPENDENT:
                # For independent cohorts: pool the two datasets with a
                # cohort indicator as "exposure", then build separate tables
                # per cohort — compare the measure values across cohorts.
                warnings.warn(
                    "INDEPENDENT mode: RR, OR, AR and PAF are computed "
                    "independently per cohort and compared as cross-cohort "
                    "deltas. These are NOT causal estimates.",
                    UserWarning,
                    stacklevel=2,
                )

            t1 = table_from_dataframe(v1, self.exposure_col, self.outcome_col)
            t2 = table_from_dataframe(v2, self.exposure_col, self.outcome_col)

            rr1 = t1.risk_ratio()
            rr2 = t2.risk_ratio()
            deltas.append(MeasureDelta.from_values(
                "risk_ratio",
                rr1.estimate, rr2.estimate,
                rr1.ci_lower, rr1.ci_upper,
                rr2.ci_lower, rr2.ci_upper,
                method=rr1.method,
            ))

            or1 = t1.odds_ratio()
            or2 = t2.odds_ratio()
            deltas.append(MeasureDelta.from_values(
                "odds_ratio",
                or1.estimate, or2.estimate,
                or1.ci_lower, or1.ci_upper,
                or2.ci_lower, or2.ci_upper,
                method=or1.method,
            ))

            rd1 = t1.risk_difference()
            rd2 = t2.risk_difference()
            deltas.append(MeasureDelta.from_values(
                "attributable_risk",
                rd1["estimate"], rd2["estimate"],
                rd1["ci_lower"], rd1["ci_upper"],
                rd2["ci_lower"], rd2["ci_upper"],
                method="wald",
            ))

            paf1 = t1.attributable_fraction_population()
            paf2 = t2.attributable_fraction_population()
            deltas.append(MeasureDelta.from_values(
                "pop_attributable_frac", paf1, paf2
            ))

        unstable = [d.measure for d in deltas if d.conclusion_changed]
        score = 1.0 - (len(unstable) / len(deltas)) if deltas else 1.0

        return CodingRobustnessResult(
            coding_system_v1=self.coding_system_v1,
            coding_system_v2=self.coding_system_v2,
            n_v1=k1,
            n_v2=k2,
            deltas=deltas,
            robustness_score=score,
            unstable_measures=unstable,
            metadata={
                "n_rows_v1": len(v1),
                "n_rows_v2": len(v2),
                "outcome_col": self.outcome_col,
                "exposure_col": self.exposure_col,
                "person_time_col": self.person_time_col,
                "mode": self.mode.value,
            },
        )