"""
data/surveillance.py - Epidemiological surveillance data utilities.

Tools for ingesting, cleaning, aggregating, and alerting on
routine surveillance data  designed for the Burkina Faso / francophone
African public health context (SNIS, DHIS2-compatible CSV exports).

Public classes
--------------
    SurveillanceDataset   structured weekly/daily case counts per site/disease
    AlertEngine           threshold-based and statistical alert detection

Public functions
----------------
    from_dhis2_csv()      load DHIS2 export CSV
    from_weekly_bulletin() parse standard weekly bulletin table
    aggregate_by()        temporal or spatial aggregation
    compute_attack_rate() attack rate per stratum
    endemic_channel()     historical percentile envelope (alert zones)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

# SurveillanceDataset

class SurveillanceDataset:
    """
    Structured surveillance case count dataset.

    Wraps a pandas DataFrame with columns:
        date / week / period   time axis
        district / site        spatial unit (optional)
        disease                disease or syndrome name
        cases                  integer case count
        deaths                 integer death count (optional)
        population             population at risk (optional)

    Built from CSV, DHIS2 exports, or a plain DataFrame.

    Example::

        from episia.data.surveillance import SurveillanceDataset

        ds = SurveillanceDataset.from_csv("meningite_2024.csv",
                                           date_col="semaine",
                                           cases_col="cas")
        print(ds.summary())
        ds.epicurve().plot().show()
        alerts = ds.alert_engine().run()
    """

    def __init__(self, df, *, date_col: str = "date",
                 cases_col: str = "cases", deaths_col: Optional[str] = None,
                 district_col: Optional[str] = None,
                 disease_col: Optional[str] = None,
                 population_col: Optional[str] = None):
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required. pip install pandas")

        self._df          = df.copy()
        self.date_col     = date_col
        self.cases_col    = cases_col
        self.deaths_col   = deaths_col
        self.district_col = district_col
        self.disease_col  = disease_col
        self.population_col = population_col

        # Ensure date column is datetime
        if date_col in self._df.columns:
            self._df[date_col] = pd.to_datetime(self._df[date_col],
                                                 errors="coerce")

    #  Constructors

    @classmethod
    def from_csv(
        cls,
        path: Union[str, Path],
        date_col: str = "date",
        cases_col: str = "cases",
        deaths_col: Optional[str] = None,
        district_col: Optional[str] = None,
        disease_col: Optional[str] = None,
        population_col: Optional[str] = None,
        **read_kwargs,
    ) -> "SurveillanceDataset":
        """
        Load from CSV file.

        Args:
            path:         Path to CSV file.
            date_col:     Column name for date / week.
            cases_col:    Column name for case counts.
            deaths_col:   Column name for deaths (optional).
            district_col: Column name for district / site (optional).
            disease_col:  Column name for disease / syndrome (optional).
            population_col: Column for population at risk (optional).
            **read_kwargs: Passed to pd.read_csv.

        Returns:
            SurveillanceDataset.
        """
        import pandas as pd
        df = pd.read_csv(path, **read_kwargs)
        return cls(df, date_col=date_col, cases_col=cases_col,
                   deaths_col=deaths_col, district_col=district_col,
                   disease_col=disease_col, population_col=population_col)

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, List],
        **kwargs,
    ) -> "SurveillanceDataset":
        """Create from a plain dict of lists."""
        import pandas as pd
        return cls(pd.DataFrame(data), **kwargs)

    @classmethod
    def from_dataframe(
        cls,
        df,
        **kwargs,
    ) -> "SurveillanceDataset":
        """Wrap an existing DataFrame."""
        return cls(df, **kwargs)

    #  Properties

    @property
    def df(self):
        return self._df

    @property
    def n_records(self) -> int:
        return len(self._df)

    @property
    def total_cases(self) -> int:
        return int(self._df[self.cases_col].sum())

    @property
    def total_deaths(self) -> Optional[int]:
        if self.deaths_col and self.deaths_col in self._df.columns:
            return int(self._df[self.deaths_col].sum())
        return None

    @property
    def cfr(self) -> Optional[float]:
        """Case fatality rate = total_deaths / total_cases."""
        d = self.total_deaths
        c = self.total_cases
        if d is not None and c > 0:
            return d / c
        return None

    @property
    def date_range(self) -> Tuple[Any, Any]:
        col = self._df[self.date_col]
        return col.min(), col.max()

    @property
    def districts(self) -> List[str]:
        if self.district_col and self.district_col in self._df.columns:
            return sorted(self._df[self.district_col].dropna().unique().tolist())
        return []

    @property
    def diseases(self) -> List[str]:
        if self.disease_col and self.disease_col in self._df.columns:
            return sorted(self._df[self.disease_col].dropna().unique().tolist())
        return []

    #  Filtering 

    def filter_district(self, district: str) -> "SurveillanceDataset":
        """Return a new dataset filtered to a single district."""
        if not self.district_col:
            raise ValueError("No district_col defined.")
        mask = self._df[self.district_col] == district
        return SurveillanceDataset(
            self._df[mask], date_col=self.date_col,
            cases_col=self.cases_col, deaths_col=self.deaths_col,
            district_col=self.district_col, disease_col=self.disease_col,
            population_col=self.population_col,
        )

    def filter_disease(self, disease: str) -> "SurveillanceDataset":
        """Return a new dataset filtered to a single disease."""
        if not self.disease_col:
            raise ValueError("No disease_col defined.")
        mask = self._df[self.disease_col] == disease
        return SurveillanceDataset(
            self._df[mask], date_col=self.date_col,
            cases_col=self.cases_col, deaths_col=self.deaths_col,
            district_col=self.district_col, disease_col=self.disease_col,
            population_col=self.population_col,
        )

    def filter_date(self, start: Any = None,
                    end: Any = None) -> "SurveillanceDataset":
        """Filter to a date range (inclusive)."""
        import pandas as pd
        df = self._df
        if start is not None:
            df = df[df[self.date_col] >= pd.to_datetime(start)]
        if end is not None:
            df = df[df[self.date_col] <= pd.to_datetime(end)]
        return SurveillanceDataset(
            df, date_col=self.date_col, cases_col=self.cases_col,
            deaths_col=self.deaths_col, district_col=self.district_col,
            disease_col=self.disease_col,
            population_col=self.population_col,
        )

    #  Aggregation 

    def aggregate(
        self,
        freq: str = "W",
        group_by: Optional[List[str]] = None,
    ):
        """
        Aggregate cases by time frequency and optional grouping columns.

        Args:
            freq:     Pandas offset alias ('D'=daily, 'W'=weekly, 'ME'=monthly).
            group_by: Additional columns to group by (district, disease…).

        Returns:
            pandas DataFrame with aggregated counts.
        """
        import pandas as pd

        df = self._df.copy()
        # Normalize freq alias for to_period compatibility
        _freq_map = {'ME': 'M', 'QE': 'Q', 'YE': 'Y', 'h': 'H'}
        _p_freq = _freq_map.get(freq, freq)
        df["_period"] = df[self.date_col].dt.to_period(_p_freq).dt.start_time

        agg_cols = {"_period": "first", self.cases_col: "sum"}
        if self.deaths_col and self.deaths_col in df.columns:
            agg_cols[self.deaths_col] = "sum"
        if self.population_col and self.population_col in df.columns:
            agg_cols[self.population_col] = "first"

        keys = ["_period"]
        if group_by:
            keys += [c for c in group_by if c in df.columns]

        result = (df.groupby(keys, as_index=False)
                    .agg({c: agg_cols[c] for c in agg_cols if c != "_period"}))
        result = result.rename(columns={"_period": "period"})
        return result.sort_values("period").reset_index(drop=True)

    #  Epidemiological metrics

    def attack_rate(
        self,
        population: Optional[int] = None,
        per: int = 100_000,
    ) -> float:
        """
        Compute overall attack rate.

        Args:
            population: Population denominator (uses population_col if None).
            per:        Rate denominator (default 100,000).

        Returns:
            Attack rate per `per` population.
        """
        if population is None:
            if self.population_col and self.population_col in self._df.columns:
                population = int(self._df[self.population_col].iloc[0])
            else:
                raise ValueError(
                    "population argument required when population_col is not set."
                )
        return self.total_cases / population * per

    def weekly_attack_rates(self, population: int, per: int = 100_000):
        """
        Compute weekly attack rates.

        Args:
            population: Population at risk.
            per:        Rate denominator.

        Returns:
            pandas DataFrame with columns: period, cases, attack_rate.
        """
        agg = self.aggregate(freq="W")
        agg["attack_rate"] = agg[self.cases_col] / population * per
        return agg

    def endemic_channel(
        self,
        historical_years: Optional[List[int]] = None,
        percentiles: Tuple[float, float, float] = (25, 50, 75),
    ) -> Dict[str, Any]:
        """
        Compute the endemic channel (historical percentile envelope).

        Groups by ISO week number across historical years.
        Returns the percentile bands used for alert zone classification.

        Args:
            historical_years: Years to include (all years if None).
            percentiles:      (low, median, high) percentiles.

        Returns:
            Dict with keys: 'weeks', 'p_low', 'p_mid', 'p_high'.
        """
        import pandas as pd

        df = self._df.copy()
        df["_year"] = df[self.date_col].dt.year
        df["_week"] = df[self.date_col].dt.isocalendar().week.astype(int)

        if historical_years:
            df = df[df["_year"].isin(historical_years)]

        grouped = df.groupby("_week")[self.cases_col]
        p_low   = grouped.quantile(percentiles[0] / 100)
        p_mid   = grouped.quantile(percentiles[1] / 100)
        p_high  = grouped.quantile(percentiles[2] / 100)

        return {
            "weeks":  p_low.index.tolist(),
            "p_low":  p_low.values,
            "p_mid":  p_mid.values,
            "p_high": p_high.values,
            "percentiles": percentiles,
        }

    #  Export to Episia viz 

    def to_timeseries_result(self):
        """
        Convert to api.results.TimeSeriesResult for viz integration.

        Returns:
            TimeSeriesResult ready for plot_epicurve().
        """
        from ..api.results import TimeSeriesResult

        agg = self.aggregate(freq="W")
        times  = agg["period"].dt.strftime("%Y-W%W").values
        values = agg[self.cases_col].values.astype(float)

        return TimeSeriesResult(times=times, values=values)

    #  Data quality

    def completeness(
        self,
        freq: str = "auto",
        period_col: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compute reporting completeness over the observed date range.

        Identifies expected periods (inferred from ``freq``) versus periods
        actually present in the dataset, and returns the missing ones.

        This is especially relevant when loading data from DHIS2 instances
        in sub-Saharan Africa where silent gaps are common: a district that
        did not submit its weekly report will simply be absent from the
        export, distorting endemic-channel baselines without any warning.

        Args:
            freq:       Expected reporting frequency.  One of:

                        * ``"auto"``    -- inferred from median gap between
                          dates (default).
                        * ``"W"``       -- weekly (ISO weeks).
                        * ``"ME"``      -- monthly (pandas >= 2.2).
                        * ``"QE"``      -- quarterly.
                        * ``"D"``       -- daily.

            period_col: Column that contains DHIS2 period strings such as
                        ``"2024W01"`` or ``"202401"`` (optional).  When
                        provided, completeness is calculated against these
                        string labels rather than inferred datetime periods,
                        and the ``period_range()`` helper is used internally
                        to build the expected sequence.

        Returns:
            dict with keys:

            * ``expected_periods``   (int)
            * ``reported_periods``   (int)
            * ``completeness_rate``  (float, 0.0 -- 1.0)
            * ``missing_periods``    (list[str])
            * ``freq``               (str, the frequency used)

        Raises:
            ValueError: if the dataset has fewer than 2 records.

        Example::

            ds = client.to_dataset(
                data_element="FTRrcoaog83",
                period="LAST_52_WEEKS",
                org_unit="ImspTQPwCqd",
            )
            result = ds.completeness()
            # {
            #   "expected_periods": 52,
            #   "reported_periods": 49,
            #   "completeness_rate": 0.942,
            #   "missing_periods": ["2024W15", "2024W16", "2024W31"],
            #   "freq": "W",
            # }
        """
        import pandas as pd

        if period_col and period_col in self._df.columns:
            return self._completeness_from_period_col(period_col)

        if self.n_records < 2:
            raise ValueError(
                "completeness() requires at least 2 records to infer "
                "the reporting frequency."
            )

        dates = pd.to_datetime(self._df[self.date_col].dropna()).sort_values()

        if freq == "auto":
            freq = self._infer_freq(dates)

        expected_index = pd.date_range(
            start=dates.min(),
            end=dates.max(),
            freq=freq,
        )

        # pd.date_range uses "ME"/"QE" (offset aliases, pandas >= 2.2) but
        # dt.to_period() needs the shorter "M"/"Q" period aliases.
        _period_freq = {
            "ME": "M", "MS": "M",
            "QE": "Q", "QS": "Q",
            "W-SUN": "W", "W-MON": "W",
        }.get(freq, freq)

        # Normalise to period strings for fair comparison.
        # We emit DHIS2-compatible labels (e.g. "2024W03", "202403") so the
        # output can be passed directly to period_range() or client queries.
        def _to_dhis2_label(period_obj, _freq: str) -> str:
            if _freq in ("W", "W-SUN", "W-MON"):
                iso = period_obj.to_timestamp().isocalendar()
                return f"{iso[0]}W{iso[1]:02d}"
            if _freq in ("ME", "M", "MS"):
                ts = period_obj.to_timestamp()
                return f"{ts.year}{ts.month:02d}"
            if _freq in ("QE", "Q", "QS"):
                ts = period_obj.to_timestamp()
                return f"{ts.year}Q{ts.quarter}"
            return str(period_obj)

        observed_periods = set(
            [_to_dhis2_label(p, freq)
             for p in dates.dt.to_period(_period_freq)]
        )
        expected_unique: List[str] = []
        seen: set = set()
        for d in expected_index:
            p = _to_dhis2_label(d.to_period(_period_freq), freq)
            if p not in seen:
                seen.add(p)
                expected_unique.append(p)

        missing = [p for p in expected_unique if p not in observed_periods]
        n_expected = len(expected_unique)
        n_reported = n_expected - len(missing)
        rate = round(n_reported / n_expected, 4) if n_expected else 0.0

        return {
            "expected_periods":  n_expected,
            "reported_periods":  n_reported,
            "completeness_rate": rate,
            "missing_periods":   missing,
            "freq":              freq,
        }

    @staticmethod
    def _infer_freq(dates) -> str:
        """Return the most likely pandas frequency alias from a sorted Series."""
        import pandas as pd
        gaps = dates.diff().dropna()
        median_gap = gaps.median()
        if median_gap <= pd.Timedelta(days=1):
            return "D"
        if median_gap <= pd.Timedelta(days=8):
            return "W"
        if median_gap <= pd.Timedelta(days=35):
            return "ME"
        return "QE"

    def _completeness_from_period_col(self, period_col: str) -> Dict[str, Any]:
        """Completeness when a DHIS2 period string column is available."""
        import re as _re

        observed = sorted(self._df[period_col].dropna().unique().tolist())
        if len(observed) < 2:
            raise ValueError(
                "completeness() needs at least 2 distinct period values."
            )

        first = observed[0]
        if _re.match(r"^\d{4}W\d{1,2}$", first):
            freq = "W"
        elif _re.match(r"^\d{4}Q[1-4]$", first):
            freq = "Q"
        elif _re.match(r"^\d{4}(0[1-9]|1[0-2])$", first):
            freq = "M"
        else:
            return {
                "expected_periods":  len(observed),
                "reported_periods":  len(observed),
                "completeness_rate": 1.0,
                "missing_periods":   [],
                "freq":              "unknown",
            }

        try:
            from ..dhis2.periods import period_range as _period_range
            full = _period_range(observed[0], observed[-1]).split(";")
        except Exception:
            full = observed

        obs_set = set(observed)
        missing = [p for p in full if p not in obs_set]
        n_expected = len(full)
        n_reported = n_expected - len(missing)
        rate = round(n_reported / n_expected, 4) if n_expected else 0.0

        return {
            "expected_periods":  n_expected,
            "reported_periods":  n_reported,
            "completeness_rate": rate,
            "missing_periods":   missing,
            "freq":              freq,
        }

    #  Summary

    def summary(self) -> Dict[str, Any]:
        """Return a summary statistics dict."""
        start, end = self.date_range
        s: Dict[str, Any] = {
            "n_records":   self.n_records,
            "total_cases": self.total_cases,
            "date_start":  str(start),
            "date_end":    str(end),
        }
        if self.total_deaths is not None:
            s["total_deaths"] = self.total_deaths
            s["cfr"]          = self.cfr
        if self.districts:
            s["n_districts"] = len(self.districts)
            s["districts"]   = self.districts[:10]
        if self.diseases:
            s["diseases"] = self.diseases
        return s

    def __repr__(self) -> str:
        start, end = self.date_range
        return (
            f"SurveillanceDataset("
            f"n={self.n_records}, "
            f"cases={self.total_cases:,}, "
            f"{start} → {end})"
        )

# AlertEngine
@dataclass
class Alert:
    """A single surveillance alert."""
    period:     Any
    value:      float
    threshold:  float
    kind:       str        # 'threshold', 'zscore', 'endemic_channel'
    severity:   str        # 'warning', 'alert', 'epidemic'
    district:   Optional[str] = None
    disease:    Optional[str] = None
    message:    str = ""

class AlertEngine:
    """
    Threshold-based and statistical alert detection for surveillance data.

    Example::

        engine = AlertEngine(dataset)
        alerts = engine.run(
            threshold=10,
            zscore_threshold=2.0,
            use_endemic_channel=True,
        )
        for a in alerts:
            print(a.period, a.severity, a.message)
    """

    def __init__(self, dataset: SurveillanceDataset):
        self.dataset = dataset

    def run(
        self,
        threshold:            Optional[float] = None,
        zscore_threshold:     float = 2.0,
        use_endemic_channel:  bool = False,
        historical_years:     Optional[List[int]] = None,
        freq:                 str = "W",
    ) -> List[Alert]:
        """
        Run all enabled alert detectors.

        Args:
            threshold:           Absolute case count threshold.
            zscore_threshold:    Z-score threshold for statistical alert.
            use_endemic_channel: Use endemic channel (requires ≥3 historical years).
            historical_years:    Years to use for endemic channel baseline.
            freq:                Aggregation frequency ('D', 'W', 'ME').

        Returns:
            List of Alert objects, sorted by period.
        """
        alerts: List[Alert] = []
        agg = self.dataset.aggregate(freq=freq)
        values = agg[self.dataset.cases_col].values.astype(float)
        periods = agg["period"].values

        # Absolute threshold
        if threshold is not None:
            for period, val in zip(periods, values):
                if val >= threshold:
                    severity = "epidemic" if val >= threshold * 2 else "alert"
                    alerts.append(Alert(
                        period=period, value=float(val),
                        threshold=float(threshold), kind="threshold",
                        severity=severity,
                        message=(
                            f"{val:.0f} cas ≥ seuil {threshold:.0f}"
                        ),
                    ))

        # Z-score
        if len(values) >= 4:
            mean = np.mean(values)
            std  = np.std(values)
            if std > 0:
                zscores = (values - mean) / std
                for period, val, z in zip(periods, values, zscores):
                    if z >= zscore_threshold:
                        severity = "epidemic" if z >= zscore_threshold * 1.5 else "warning"
                        alerts.append(Alert(
                            period=period, value=float(val),
                            threshold=float(mean + zscore_threshold * std),
                            kind="zscore", severity=severity,
                            message=f"Z-score={z:.2f} ≥ {zscore_threshold}",
                        ))

        # Endemic channel
        if use_endemic_channel:
            try:
                channel = self.dataset.endemic_channel(historical_years)
                week_map = dict(zip(channel["weeks"], channel["p_high"]))
                import pandas as pd
                for period, val in zip(periods, values):
                    p = pd.Timestamp(period)
                    week = p.isocalendar()[1]
                    if week in week_map and val > week_map[week]:
                        alerts.append(Alert(
                            period=period, value=float(val),
                            threshold=float(week_map[week]),
                            kind="endemic_channel", severity="alert",
                            message=(
                                f"Semaine {week}: {val:.0f} cas "
                                f"> P75 historique {week_map[week]:.0f}"
                            ),
                        ))
            except Exception:
                pass

        # Sort by period
        try:
            alerts.sort(key=lambda a: str(a.period))
        except Exception:
            pass

        return alerts

    def alert_summary(self, alerts: List[Alert]) -> Dict[str, Any]:
        """Summarise a list of alerts."""
        if not alerts:
            return {"n_alerts": 0, "severity_counts": {}}
        from collections import Counter
        sev = Counter(a.severity for a in alerts)
        return {
            "n_alerts":       len(alerts),
            "severity_counts": dict(sev),
            "first_alert":    str(alerts[0].period),
            "last_alert":     str(alerts[-1].period),
        }

# Module-level convenience functions

def from_dhis2_csv(
    path: Union[str, Path],
    date_col: str = "periodName",
    cases_col: str = "value",
    district_col: str = "orgUnitName",
    **kwargs,
) -> SurveillanceDataset:
    """
    Load a DHIS2 standard CSV export.

    DHIS2 exports typically have columns:
        periodName, orgUnitName, dataElementName, value, …

    Args:
        path:         Path to DHIS2 CSV export.
        date_col:     Column with period label.
        cases_col:    Column with case count value.
        district_col: Column with organisation unit name.
        **kwargs:     Passed to pd.read_csv.

    Returns:
        SurveillanceDataset.
    """
    return SurveillanceDataset.from_csv(
        path, date_col=date_col, cases_col=cases_col,
        district_col=district_col, **kwargs,
    )


def compute_attack_rate(
    cases: int,
    population: int,
    per: int = 100_000,
) -> float:
    """
    Compute attack rate.

    Args:
        cases:      Number of cases.
        population: Population at risk.
        per:        Rate denominator (default 100,000).

    Returns:
        Attack rate per `per` population.
    """
    if population <= 0:
        raise ValueError(f"population must be > 0, got {population}.")
    return cases / population * per


def endemic_channel(
    dataset: SurveillanceDataset,
    historical_years: Optional[List[int]] = None,
    percentiles: Tuple[float, float, float] = (25, 50, 75),
) -> Dict[str, Any]:
    """Module-level alias for dataset.endemic_channel()."""
    return dataset.endemic_channel(historical_years, percentiles)


def aggregate_by(
    dataset: SurveillanceDataset,
    freq: str = "W",
    group_by: Optional[List[str]] = None,
):
    """Module-level alias for dataset.aggregate()."""
    return dataset.aggregate(freq=freq, group_by=group_by)


__all__ = [
    "SurveillanceDataset",
    "AlertEngine",
    "Alert",
    "from_dhis2_csv",
    "compute_attack_rate",
    "endemic_channel",
    "aggregate_by",
]