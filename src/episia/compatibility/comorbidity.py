"""
episia.compatibility.comorbidity - Charlson and Elixhauser comorbidity indices

Computes the Charlson Comorbidity Index (CCI) and the Elixhauser Comorbidity
Score (ECS) from ICD-10 or ICD-11 diagnosis codes, and quantifies how the
transition between classification systems affects these indices at the
patient and cohort level.

Typical usage
-------------
    from episia.compatibility.comorbidity import ComorbidityScorer, ComorbidityComparator

    # Score a single dataset
    scorer = ComorbidityScorer(coding_system="ICD-10")
    df_scored = scorer.score(df, icd_col="diagnosis_code")

    # Compare the same cohort under two coding systems
    comp = ComorbidityComparator(
        dataset_v1=df_icd10,
        dataset_v2=df_icd11,
        icd_col_v1="diag_icd10",
        icd_col_v2="diag_icd11",
        coding_system_v1="ICD-10",
        coding_system_v2="ICD-11",
    )
    result = comp.run()
    print(result.summary())

Notes
-----
- ICD-10 mappings follow Quan et al. (2005) for Charlson and Elixhauser.
- ICD-11 mappings follow WHO ICD-11 MMS (2022) chapter structure, cross-walked
  from ICD-10 using the WHO official mapping tables.
- Codes are matched by prefix (first 3 characters = category level).
  Full-code matching (4–5 characters) is supported when available.
- Multiple diagnosis codes per patient: pass a list-valued column or a
  pre-aggregated binary indicator matrix (one column per condition).

References
----------
Quan H et al. Coding Algorithms for Defining Comorbidities in ICD-9-CM and
    ICD-10 Administrative Data. Med Care. 2005;43(11):1130-1139.
Elixhauser A et al. Comorbidity Measures for Use with Administrative Data.
    Med Care. 1998;36(1):8-27.
WHO. ICD-11 for Mortality and Morbidity Statistics. Geneva: WHO; 2022.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Union

import numpy as np
import pandas as pd

from episia.api.results import ConfidenceInterval, EpiResult
from episia.core.validator import validate_dataframe



# ICD-10 code mappings (Quan 2005)
# Keys = condition name, Values = list of ICD-10 3-char prefixes

from typing import Dict, List

# ICD mappings loaded from JSON data files 
# Edit  src/episia/compatibility/data/charlson.json
#       src/episia/compatibility/data/elixhauser.json
# to update codes or weights — do NOT hardcode values here.

import importlib.resources
import json
from pathlib import Path

def _load_index(name: str) -> dict:
    """Load a comorbidity index definition from the bundled JSON data file."""
    data_dir = Path(__file__).parent / "data"
    path = data_dir / f"{name}.json"
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)

_CHARLSON_DATA    = _load_index("charlson")["conditions"]
_ELIXHAUSER_DATA  = _load_index("elixhauser")["conditions"]

# Derived lookup helpers (same interface as before)
_CHARLSON_ICD10  = {c: v["icd10"] for c, v in _CHARLSON_DATA.items()}
_CHARLSON_ICD11  = {c: v["icd11"] for c, v in _CHARLSON_DATA.items()}
_CHARLSON_WEIGHTS = {c: v["weight"] for c, v in _CHARLSON_DATA.items()}

_ELIXHAUSER_ICD10  = {c: v["icd10"] for c, v in _ELIXHAUSER_DATA.items()}
_ELIXHAUSER_ICD11  = {c: v["icd11"] for c, v in _ELIXHAUSER_DATA.items()}
_ELIXHAUSER_WEIGHTS = {c: v["weight"] for c, v in _ELIXHAUSER_DATA.items()}

# Registry: coding_system -> (index_name -> condition_map)
_MAPS = {
    "ICD-10": {
        "charlson":   _CHARLSON_ICD10,
        "elixhauser": _ELIXHAUSER_ICD10,
    },
    "ICD-11": {
        "charlson":   _CHARLSON_ICD11,
        "elixhauser": _ELIXHAUSER_ICD11,
    },
}

_WEIGHTS = {
    "charlson":   _CHARLSON_WEIGHTS,
    "elixhauser": _ELIXHAUSER_WEIGHTS,
}

SUPPORTED_SYSTEMS = list(_MAPS.keys())
SUPPORTED_INDICES = ["charlson", "elixhauser"]



# Result objects


@dataclass
class ComorbidityScoreResult(EpiResult):
    """
    Per-patient comorbidity scores for a single dataset.

    Attributes
    ----------
    index : str
        "charlson" or "elixhauser".
    coding_system : str
        Coding system used (e.g. "ICD-10").
    scores : pd.Series
        Numeric score per patient (index-aligned with input DataFrame).
    conditions : pd.DataFrame
        Binary indicator matrix (1 patient per row, 1 condition per column).
    mean_score : float
    std_score : float
    median_score : float
    n_patients : int
    """
    index: str
    coding_system: str
    scores: pd.Series
    conditions: pd.DataFrame
    mean_score: float
    std_score: float
    median_score: float
    n_patients: int

    def __repr__(self) -> str:
        return (
            f"ComorbidityScoreResult({self.coding_system} / {self.index}  "
            f"n={self.n_patients}  "
            f"mean={self.mean_score:.2f}  median={self.median_score:.1f})"
        )

    def to_dict(self):
        return {
            "index": self.index,
            "coding_system": self.coding_system,
            "n_patients": self.n_patients,
            "mean_score": self.mean_score,
            "std_score": self.std_score,
            "median_score": self.median_score,
            "score_distribution": self.scores.value_counts().sort_index().to_dict(),
        }

    def to_dataframe(self) -> pd.DataFrame:
        """Return conditions matrix with score column appended."""
        df = self.conditions.copy()
        df[f"{self.index}_score"] = self.scores
        return df


@dataclass
class ComorbidityComparisonResult(EpiResult):
    """
    Comparison of comorbidity scores between two coding systems.

    Attributes
    ----------
    index : str
        "charlson" or "elixhauser".
    coding_system_v1, coding_system_v2 : str
    result_v1, result_v2 : ComorbidityScoreResult
    mean_delta : float
        mean(score_v2) - mean(score_v1).
    ci_mean_delta : ConfidenceInterval
        95% CI on mean_delta (paired t-test).
    agreement_pct : float
        Proportion of patients with identical scores in both versions.
    kappa : float
        Cohen's kappa on score categories (0-1, 2+).
    conditions_gained : dict
        Conditions present more often in v2 than v1.
    conditions_lost : dict
        Conditions present more often in v1 than v2.
    robustness_score : float
        1 - |mean_delta| / max(mean_v1, mean_v2, 1). Higher = more stable.
    """
    index: str
    coding_system_v1: str
    coding_system_v2: str
    result_v1: ComorbidityScoreResult
    result_v2: ComorbidityScoreResult
    mean_delta: float
    ci_mean_delta: ConfidenceInterval
    agreement_pct: float
    kappa: float
    conditions_gained: Dict[str, float]
    conditions_lost: Dict[str, float]
    robustness_score: float

    def __repr__(self) -> str:
        return (
            f"ComorbidityComparisonResult({self.index}  "
            f"{self.coding_system_v1} vs {self.coding_system_v2}  "
            f"Δmean={self.mean_delta:+.3f}  "
            f"agreement={self.agreement_pct:.1%}  "
            f"κ={self.kappa:.3f}  "
            f"robustness={self.robustness_score:.2f})"
        )

    def to_dict(self):
        return {
            "index": self.index,
            "coding_system_v1": self.coding_system_v1,
            "coding_system_v2": self.coding_system_v2,
            "mean_score_v1": self.result_v1.mean_score,
            "mean_score_v2": self.result_v2.mean_score,
            "mean_delta": self.mean_delta,
            "ci_delta_lower": self.ci_mean_delta.lower,
            "ci_delta_upper": self.ci_mean_delta.upper,
            "agreement_pct": self.agreement_pct,
            "kappa": self.kappa,
            "robustness_score": self.robustness_score,
            "conditions_gained": self.conditions_gained,
            "conditions_lost": self.conditions_lost,
        }

    def to_dataframe(self) -> pd.DataFrame:
        """Tidy DataFrame with one row per condition and prevalence delta."""
        conds_v1 = self.result_v1.conditions.mean()
        conds_v2 = self.result_v2.conditions.mean()
        all_conds = conds_v1.index.union(conds_v2.index)
        rows = []
        for c in all_conds:
            p1 = float(conds_v1.get(c, 0.0))
            p2 = float(conds_v2.get(c, 0.0))
            rows.append({
                "condition": c,
                f"prevalence_{self.coding_system_v1}": p1,
                f"prevalence_{self.coding_system_v2}": p2,
                "delta": p2 - p1,
            })
        return pd.DataFrame(rows).sort_values("delta", key=abs, ascending=False)

    def summary(self) -> str:
        lines = [
            f"Comorbidity Comparison — {self.index.title()} Index",
            "=" * 50,
            f"  Systems   : {self.coding_system_v1} vs {self.coding_system_v2}",
            f"  Patients  : {self.result_v1.n_patients}",
            f"  Mean score ({self.coding_system_v1}): "
            f"{self.result_v1.mean_score:.3f}  "
            f"(SD {self.result_v1.std_score:.3f})",
            f"  Mean score ({self.coding_system_v2}): "
            f"{self.result_v2.mean_score:.3f}  "
            f"(SD {self.result_v2.std_score:.3f})",
            f"  Mean delta : {self.mean_delta:+.3f}  "
            f"95%CI [{self.ci_mean_delta.lower:+.3f}, "
            f"{self.ci_mean_delta.upper:+.3f}]",
            f"  Agreement  : {self.agreement_pct:.1%}",
            f"  Kappa      : {self.kappa:.3f}",
            f"  Robustness : {self.robustness_score:.2f}",
        ]
        if self.conditions_gained:
            top = sorted(self.conditions_gained.items(),
                         key=lambda x: x[1], reverse=True)[:5]
            lines.append(f"  Gained (top 5): "
                         + ", ".join(f"{c} (+{v:.2%})" for c, v in top))
        if self.conditions_lost:
            top = sorted(self.conditions_lost.items(),
                         key=lambda x: x[1], reverse=True)[:5]
            lines.append(f"  Lost   (top 5): "
                         + ", ".join(f"{c} (-{v:.2%})" for c, v in top))
        return "\n".join(lines)

    def plot(self, backend: str = "plotly"):
        df = self.to_dataframe()
        v1_col = f"prevalence_{self.coding_system_v1}"
        v2_col = f"prevalence_{self.coding_system_v2}"
        if backend == "plotly":
            try:
                import plotly.graph_objects as go
            except ImportError as e:
                raise ImportError("plotly required for backend='plotly'.") from e
            fig = go.Figure()
            fig.add_trace(go.Bar(name=self.coding_system_v1,
                                 x=df["condition"], y=df[v1_col],
                                 marker_color="#4C8CBF"))
            fig.add_trace(go.Bar(name=self.coding_system_v2,
                                 x=df["condition"], y=df[v2_col],
                                 marker_color="#E07B54"))
            fig.update_layout(
                title=f"{self.index.title()} Conditions: "
                      f"{self.coding_system_v1} vs {self.coding_system_v2}",
                xaxis_title="Condition", yaxis_title="Prevalence",
                barmode="group", template="plotly_white",
                xaxis={"tickangle": -40},
            )
            return fig
        elif backend == "matplotlib":
            try:
                import matplotlib.pyplot as plt
                import numpy as np
            except ImportError as e:
                raise ImportError("matplotlib required.") from e
            x = np.arange(len(df))
            w = 0.35
            fig, ax = plt.subplots(figsize=(14, 5))
            ax.bar(x - w / 2, df[v1_col], w,
                   label=self.coding_system_v1, color="#4C8CBF")
            ax.bar(x + w / 2, df[v2_col], w,
                   label=self.coding_system_v2, color="#E07B54")
            ax.set_xticks(x)
            ax.set_xticklabels(df["condition"], rotation=45, ha="right")
            ax.set_ylabel("Prevalence")
            ax.set_title(f"{self.index.title()} Conditions: "
                         f"{self.coding_system_v1} vs {self.coding_system_v2}")
            ax.legend()
            fig.tight_layout()
            return fig
        else:
            raise ValueError(f"Unknown backend: {backend!r}.")


# Internal helpers

def _prefix_match(code: str, prefixes: List[str]) -> bool:
    """True if *code* starts with any prefix in *prefixes*."""
    code = str(code).strip().upper()
    return any(code.startswith(p.upper()) for p in prefixes)


def _build_condition_matrix(
    codes_series: pd.Series,
    condition_map: Dict[str, List[str]],
) -> pd.DataFrame:
    """
    Build a binary condition-indicator matrix from a Series of ICD codes.

    Parameters
    ----------
    codes_series : pd.Series
        Each element is either a single code (str) or a list of codes.
    condition_map : dict
        condition_name -> list of ICD prefix strings.

    Returns
    -------
    pd.DataFrame
        Shape (n_patients, n_conditions), values in {0, 1}.
    """
    def _has_condition(cell, prefixes: List[str]) -> int:
        if cell is None or (isinstance(cell, float) and np.isnan(cell)):
            return 0
        codes = cell if isinstance(cell, (list, tuple)) else [cell]
        return int(any(_prefix_match(c, prefixes) for c in codes))

    return pd.DataFrame(
        {cond: codes_series.apply(_has_condition, prefixes=pfx)
         for cond, pfx in condition_map.items()},
        index=codes_series.index,
    )


def _compute_score(
    condition_matrix: pd.DataFrame,
    weights: Dict[str, int],
) -> pd.Series:
    """Weighted sum of binary condition indicators."""
    shared = [c for c in condition_matrix.columns if c in weights]
    w = pd.Series({c: weights[c] for c in shared})
    return condition_matrix[shared].multiply(w).sum(axis=1)


def _kappa(s1: pd.Series, s2: pd.Series, bins: List[int]) -> float:
    """
    Cohen's kappa on binned scores.
    bins example: [0, 1, 2] → categories 0, 1, ≥2.
    """
    def _bin(s: pd.Series) -> pd.Series:
        cats = []
        for v in s:
            for b in sorted(bins):
                if v <= b:
                    cats.append(b)
                    break
            else:
                cats.append(bins[-1] + 1)
        return pd.Series(cats, index=s.index)

    b1, b2 = _bin(s1), _bin(s2)
    cats = sorted(set(b1) | set(b2))
    n = len(b1)
    if n == 0:
        return float("nan")

    # Observed agreement
    po = (b1 == b2).mean()

    # Expected agreement
    pe = sum(
        (b1 == c).mean() * (b2 == c).mean()
        for c in cats
    )
    if pe >= 1.0:
        return 1.0
    return (po - pe) / (1.0 - pe)


def _paired_t_ci(
    diff: pd.Series, confidence: float = 0.95
) -> ConfidenceInterval:
    """95% CI on mean of paired differences via t-distribution."""
    from scipy import stats as _stats
    n = len(diff)
    if n < 2:
        return ConfidenceInterval(lower=float("nan"), upper=float("nan"),
                                  method="paired_t")
    mean_d = float(diff.mean())
    se = float(diff.std(ddof=1) / np.sqrt(n))
    alpha = 1 - confidence
    t_crit = float(_stats.t.ppf(1 - alpha / 2, df=n - 1))
    return ConfidenceInterval(
        lower=mean_d - t_crit * se,
        upper=mean_d + t_crit * se,
        confidence=confidence,
        method="paired_t",
    )


# ComorbidityScorer — scores a single dataset

class ComorbidityScorer:
    """
    Compute Charlson or Elixhauser scores for a single dataset.

    Parameters
    ----------
    index : {"charlson", "elixhauser"}
        Comorbidity index to compute.
    coding_system : {"ICD-10", "ICD-11"}
        Coding system of the diagnosis codes in the dataset.
    """

    def __init__(
        self,
        index: str = "charlson",
        coding_system: str = "ICD-10",
    ) -> None:
        index = index.lower()
        if index not in SUPPORTED_INDICES:
            raise ValueError(
                f"index must be one of {SUPPORTED_INDICES}, got {index!r}."
            )
        if coding_system not in SUPPORTED_SYSTEMS:
            raise ValueError(
                f"coding_system must be one of {SUPPORTED_SYSTEMS}, "
                f"got {coding_system!r}."
            )
        self.index = index
        self.coding_system = coding_system
        self._condition_map = _MAPS[coding_system][index]
        self._weights = _WEIGHTS[index]

    def score(
        self,
        df: pd.DataFrame,
        icd_col: str,
    ) -> ComorbidityScoreResult:
        """
        Compute comorbidity scores for each patient in *df*.

        Parameters
        ----------
        df : pd.DataFrame
            One row per patient. Must contain *icd_col*.
        icd_col : str
            Column containing ICD codes. Each cell may be:
            - a single code string (e.g. "I50")
            - a list/tuple of code strings (e.g. ["I50", "E11"])
            - NaN (patient treated as having no relevant codes)

        Returns
        -------
        ComorbidityScoreResult
        """
        validate_dataframe(df, required_columns=[icd_col], allow_nan=True)
        conditions = _build_condition_matrix(df[icd_col], self._condition_map)
        scores = _compute_score(conditions, self._weights)
        return ComorbidityScoreResult(
            index=self.index,
            coding_system=self.coding_system,
            scores=scores,
            conditions=conditions,
            mean_score=float(scores.mean()),
            std_score=float(scores.std(ddof=1)) if len(scores) > 1 else 0.0,
            median_score=float(scores.median()),
            n_patients=len(df),
        )



# ComorbidityComparator — compares two coding versions of the same cohort

class ComorbidityComparator:
    """
    Compare Charlson or Elixhauser scores between two coding versions
    of the same cohort.

    Parameters
    ----------
    dataset_v1, dataset_v2 : pd.DataFrame
        Same cohort, coded under different systems. Must have the same
        number of rows (one row per patient).
    icd_col_v1, icd_col_v2 : str
        Column names containing ICD codes in each dataset.
    coding_system_v1, coding_system_v2 : str
        Coding systems (e.g. "ICD-10", "ICD-11").
    index : {"charlson", "elixhauser"}
        Comorbidity index to compute.
    """

    def __init__(
        self,
        dataset_v1: pd.DataFrame,
        dataset_v2: pd.DataFrame,
        icd_col_v1: str,
        icd_col_v2: str,
        coding_system_v1: str = "ICD-10",
        coding_system_v2: str = "ICD-11",
        index: str = "charlson",
    ) -> None:
        if len(dataset_v1) != len(dataset_v2):
            raise ValueError(
                f"dataset_v1 ({len(dataset_v1)} rows) and dataset_v2 "
                f"({len(dataset_v2)} rows) must have the same number of rows."
            )
        self._v1 = dataset_v1.copy().reset_index(drop=True)
        self._v2 = dataset_v2.copy().reset_index(drop=True)
        self.icd_col_v1 = icd_col_v1
        self.icd_col_v2 = icd_col_v2
        self.coding_system_v1 = coding_system_v1
        self.coding_system_v2 = coding_system_v2
        self.index = index.lower()

    def run(self) -> ComorbidityComparisonResult:
        """
        Run the full comorbidity comparison.

        Returns
        -------
        ComorbidityComparisonResult
        """
        scorer_v1 = ComorbidityScorer(self.index, self.coding_system_v1)
        scorer_v2 = ComorbidityScorer(self.index, self.coding_system_v2)

        res_v1 = scorer_v1.score(self._v1, self.icd_col_v1)
        res_v2 = scorer_v2.score(self._v2, self.icd_col_v2)

        diff = res_v2.scores - res_v1.scores
        mean_delta = float(diff.mean())
        ci_delta = _paired_t_ci(diff)

        agreement_pct = float((res_v1.scores == res_v2.scores).mean())
        kappa = _kappa(res_v1.scores, res_v2.scores, bins=[0, 1, 2])

        # Conditions gained / lost (prevalence delta)
        prev_v1 = res_v1.conditions.mean()
        prev_v2 = res_v2.conditions.mean()
        all_conds = prev_v1.index.union(prev_v2.index)
        gained, lost = {}, {}
        for c in all_conds:
            p1 = float(prev_v1.get(c, 0.0))
            p2 = float(prev_v2.get(c, 0.0))
            delta = p2 - p1
            if delta > 0:
                gained[c] = delta
            elif delta < 0:
                lost[c] = abs(delta)

        max_mean = max(abs(res_v1.mean_score), abs(res_v2.mean_score), 1.0)
        robustness = max(0.0, 1.0 - abs(mean_delta) / max_mean)

        return ComorbidityComparisonResult(
            index=self.index,
            coding_system_v1=self.coding_system_v1,
            coding_system_v2=self.coding_system_v2,
            result_v1=res_v1,
            result_v2=res_v2,
            mean_delta=mean_delta,
            ci_mean_delta=ci_delta,
            agreement_pct=agreement_pct,
            kappa=kappa,
            conditions_gained=gained,
            conditions_lost=lost,
            robustness_score=robustness,
        )