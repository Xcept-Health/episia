"""
tests/unit/test_data_viz_unified.py
Unit tests for:
    data/dataset.py        — Dataset construction, clean, filter,
                             aggregate_by_date, create_2x2_table,
                             calculate_incidence, copy, I/O
    data/io.py             — read_csv, from_pandas, from_dict,
                             from_records, detect_format, export_dataset
    data/surveillance.py   — SurveillanceDataset properties, filtering,
                             aggregate, attack_rate, endemic_channel,
                             to_timeseries_result, summary, __repr__
    data/surveillance.py   — AlertEngine, Alert, alert_summary
    viz/themes/registry.py — set_theme, get_theme, get_available_themes,
                             get_palette, get_plotly_layout, register_theme
    viz/curves.py          — plot_epicurve (raw arrays + proxy result)
    viz/roc.py             — plot_roc
    api/unified.py         — EpisiaAPI (epi singleton) all methods
"""
from __future__ import annotations

import io as _io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

#  data ─
from episia.data.dataset import Dataset
from episia.data.io import (
    read_csv, from_pandas, from_dict, from_records,
    detect_format, export_dataset,
)
from episia.data.surveillance import (
    SurveillanceDataset, Alert, AlertEngine,
)

#  viz ─
from episia.viz.themes.registry import (
    set_theme, get_theme, get_available_themes,
    get_palette, get_plotly_layout, register_theme,
    AVAILABLE_THEMES,
)
from episia.viz.curves import plot_epicurve
from episia.viz.roc import plot_roc

#  api ─
from episia.api.unified import epi, EpisiaAPI



# Shared fixtures


@pytest.fixture
def simple_df():
    return pd.DataFrame({
        "age":      [25, 30, 35, 40, 45],
        "exposed":  [1,  1,  0,  0,  1],
        "outcome":  [1,  0,  1,  0,  1],
        "district": ["A","A","B","B","A"],
    })

@pytest.fixture
def simple_dataset(simple_df):
    return Dataset(simple_df, low_memory=False)

@pytest.fixture
def surveillance_data():
    dates = pd.date_range("2024-01-01", periods=52, freq="W")
    rng   = np.random.default_rng(0)
    return pd.DataFrame({
        "date":     dates,
        "cases":    rng.poisson(10, 52).astype(int),
        "deaths":   rng.poisson(1, 52).astype(int),
        "district": ["Centre"] * 26 + ["Nord"] * 26,
        "pop":      [500_000] * 52,
    })

@pytest.fixture
def surv(surveillance_data):
    return SurveillanceDataset.from_dataframe(
        surveillance_data,
        date_col="date", cases_col="cases",
        deaths_col="deaths", district_col="district",
        population_col="pop",
    )

@pytest.fixture
def roc_result():
    from episia.stats.diagnostic import roc_analysis
    y_true  = np.array([1,1,1,1,1,0,0,0,0,0])
    y_score = np.array([0.9,0.8,0.7,0.6,0.4,0.3,0.2,0.1,0.35,0.45])
    return roc_analysis(y_true, y_score)



# 1. Dataset — construction


class TestDatasetConstruction:
    def test_from_dataframe(self, simple_df):
        ds = Dataset(simple_df, low_memory=False)
        assert isinstance(ds, Dataset)

    def test_from_dict(self):
        ds = Dataset({"a": [1, 2, 3], "b": [4, 5, 6]}, low_memory=False)
        assert len(ds) == 3

    def test_from_csv(self, tmp_path, simple_df):
        p = tmp_path / "test.csv"
        simple_df.to_csv(p, index=False)
        ds = Dataset(str(p), low_memory=False)
        assert len(ds) == len(simple_df)

    def test_unsupported_type_raises(self):
        from episia.core.exceptions import DataError
        with pytest.raises(DataError):
            Dataset(42)

    def test_missing_file_raises(self):
        from episia.core.exceptions import DataError
        with pytest.raises(DataError):
            Dataset("/no/such/file.csv")

    def test_empty_df_raises(self):
        # validate_dataframe raises ValidationError (from validator module)
        # which is re-raised before DataError wrapping
        from episia.core.validator import ValidationError as ValidatorError
        with pytest.raises((Exception,)):
            Dataset(pd.DataFrame(), low_memory=False)

    def test_repr(self, simple_dataset):
        r = repr(simple_dataset)
        assert "Dataset" in r and "5" in r

    def test_len(self, simple_dataset):
        assert len(simple_dataset) == 5

    def test_history_has_init(self, simple_dataset):
        ops = [h["operation"] for h in simple_dataset.history]
        assert "init" in ops

    def test_metadata_source(self, simple_dataset):
        assert "source" in simple_dataset.metadata



# 2. Dataset — operations


class TestDatasetOperations:
    def test_clean_drops_na(self):
        # validate_dataframe rejects NaN columns → use explicit NaN after init
        df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]})
        ds = Dataset(df, low_memory=False)
        # Inject NaN after construction to bypass validator
        ds.df.loc[0, "a"] = float("nan")
        ds.df.loc[2, "b"] = float("nan")
        cleaned = ds.clean(drop_na=True)
        assert len(cleaned) == 1  # only row 1 has no NaN

    def test_clean_drops_duplicates(self):
        df = pd.DataFrame({"a": [1, 1, 2], "b": [1, 1, 2]})
        ds = Dataset(df, low_memory=False)
        cleaned = ds.clean(drop_na=False)
        assert len(cleaned) == 2

    def test_clean_returns_new_by_default(self, simple_dataset):
        cleaned = simple_dataset.clean()
        assert cleaned is not simple_dataset

    def test_filter_string_query(self, simple_dataset):
        filtered = simple_dataset.filter("age > 30")
        assert len(filtered) < len(simple_dataset)
        assert all(filtered.df["age"] > 30)

    def test_filter_dict(self, simple_dataset):
        filtered = simple_dataset.filter({"district": "A"})
        assert all(filtered.df["district"] == "A")

    def test_filter_series(self, simple_dataset):
        mask = simple_dataset.df["exposed"] == 1
        filtered = simple_dataset.filter(mask)
        assert all(filtered.df["exposed"] == 1)

    def test_filter_invalid_raises(self, simple_dataset):
        from episia.core.exceptions import DataError
        with pytest.raises(DataError):
            simple_dataset.filter(42)

    def test_getitem_column(self, simple_dataset):
        col = simple_dataset["age"]
        assert isinstance(col, pd.Series)
        assert len(col) == 5

    def test_getitem_list(self, simple_dataset):
        df = simple_dataset[["age", "exposed"]]
        assert isinstance(df, pd.DataFrame)

    def test_setitem_column(self, simple_dataset):
        simple_dataset["new_col"] = 99
        assert "new_col" in simple_dataset.df.columns

    def test_copy_is_independent(self, simple_dataset):
        copy = simple_dataset.copy()
        copy.df["age"] = 0
        assert simple_dataset.df["age"].iloc[0] != 0

    def test_describe_epi_returns_df(self, simple_dataset):
        result = simple_dataset.describe_epidemiological()
        assert isinstance(result, pd.DataFrame)
        assert "column" in result.columns

    def test_calculate_incidence_scalar_pop(self, simple_dataset):
        # simple_dataset has column "age", use as proxy for cases
        result = simple_dataset.calculate_incidence(
            cases_col="age", population_value=1000.0
        )
        assert len(result) == 5

    def test_create_2x2_table(self, simple_dataset):
        result = simple_dataset.create_2x2_table("exposed", "outcome")
        assert "table" in result
        from episia.stats.contingency import Table2x2
        assert isinstance(result["table"], Table2x2)

    def test_aggregate_by_date(self, tmp_path):
        df = pd.DataFrame({
            "date":  pd.date_range("2024-01-01", periods=30, freq="D"),
            "cases": np.ones(30, dtype=int),
        })
        ds = Dataset(df, low_memory=False)
        agg = ds.aggregate_by_date(date_column="date", freq="W")
        assert len(agg) < 30

    def test_get_history_dataframe(self, simple_dataset):
        h = simple_dataset.get_history()
        assert isinstance(h, pd.DataFrame)



# 3. Dataset — I/O (save/load round-trip)


class TestDatasetIO:
    def test_to_csv_and_reload(self, simple_dataset, tmp_path):
        p = tmp_path / "out.csv"
        simple_dataset.to_csv(p, index=False)
        ds2 = Dataset(str(p), low_memory=False)
        assert len(ds2) == len(simple_dataset)

    def test_to_parquet_and_reload(self, simple_dataset, tmp_path):
        pytest.importorskip("pyarrow", reason="pyarrow not installed")
        p = tmp_path / "out.parquet"
        simple_dataset.to_parquet(p)
        ds2 = Dataset(str(p), low_memory=False)
        assert len(ds2) == len(simple_dataset)



# 4. io.py convenience functions


class TestIOFunctions:
    def test_read_csv(self, simple_df, tmp_path):
        p = tmp_path / "data.csv"
        simple_df.to_csv(p, index=False)
        ds = read_csv(str(p), low_memory=False)
        assert isinstance(ds, Dataset)
        assert len(ds) == len(simple_df)

    def test_from_pandas(self, simple_df):
        ds = from_pandas(simple_df, low_memory=False)
        assert isinstance(ds, Dataset)
        assert len(ds) == len(simple_df)

    def test_from_dict(self):
        ds = from_dict({"x": [1, 2, 3]}, low_memory=False)
        assert len(ds) == 3

    def test_from_records(self):
        records = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        ds = from_records(records, low_memory=False)
        assert len(ds) == 2

    def test_detect_format_csv(self):
        assert detect_format("/some/file.csv") == "csv"

    def test_detect_format_excel(self):
        assert detect_format("/some/file.xlsx") == "excel"

    def test_detect_format_parquet(self):
        assert detect_format("/some/file.parquet") == "parquet"

    def test_detect_format_unknown(self):
        assert detect_format("/some/file.abc") == "unknown"

    def test_export_csv(self, simple_dataset, tmp_path):
        p = tmp_path / "export.csv"
        export_dataset(simple_dataset, p, format="csv", index=False)
        assert p.exists()

    def test_export_auto_detects(self, simple_dataset, tmp_path):
        p = tmp_path / "export.csv"
        export_dataset(simple_dataset, p, format="auto", index=False)
        assert p.exists()

    def test_export_unsupported_raises(self, simple_dataset, tmp_path):
        from episia.core.exceptions import FileError
        p = tmp_path / "export.abc"
        with pytest.raises(FileError):
            export_dataset(simple_dataset, p, format="abc")



# 5. SurveillanceDataset — construction & properties


class TestSurveillanceDatasetProperties:
    def test_from_dataframe(self, surv):
        assert isinstance(surv, SurveillanceDataset)

    def test_from_dict_constructor(self):
        ds = SurveillanceDataset.from_dict({
            "date":  ["2024-01-01", "2024-01-08"],
            "cases": [5, 10],
        })
        assert ds.n_records == 2

    def test_from_csv(self, surveillance_data, tmp_path):
        p = tmp_path / "surv.csv"
        surveillance_data.to_csv(p, index=False)
        ds = SurveillanceDataset.from_csv(str(p), date_col="date",
                                           cases_col="cases",
                                           deaths_col="deaths")
        assert ds.n_records == len(surveillance_data)

    def test_n_records(self, surv, surveillance_data):
        assert surv.n_records == len(surveillance_data)

    def test_total_cases_positive(self, surv):
        assert surv.total_cases > 0

    def test_total_deaths_positive(self, surv):
        assert surv.total_deaths is not None and surv.total_deaths > 0

    def test_cfr_between_0_and_1(self, surv):
        assert 0 <= surv.cfr <= 1

    def test_cfr_none_without_deaths_col(self):
        df = pd.DataFrame({"date": ["2024-01-01"], "cases": [5]})
        ds = SurveillanceDataset.from_dataframe(df)
        assert ds.cfr is None

    def test_date_range(self, surv):
        start, end = surv.date_range
        assert start < end

    def test_districts(self, surv):
        assert "Centre" in surv.districts and "Nord" in surv.districts

    def test_districts_empty_without_col(self):
        df = pd.DataFrame({"date": ["2024-01-01"], "cases": [5]})
        ds = SurveillanceDataset.from_dataframe(df)
        assert ds.districts == []

    def test_repr(self, surv):
        r = repr(surv)
        assert "SurveillanceDataset" in r

    def test_df_property(self, surv):
        assert isinstance(surv.df, pd.DataFrame)



# 6. SurveillanceDataset — filtering & aggregation


class TestSurveillanceFiltering:
    def test_filter_district(self, surv):
        sub = surv.filter_district("Centre")
        assert all(sub.df["district"] == "Centre")
        assert sub.n_records == 26

    def test_filter_district_no_col_raises(self):
        df = pd.DataFrame({"date": ["2024-01-01"], "cases": [5]})
        ds = SurveillanceDataset.from_dataframe(df)
        with pytest.raises(ValueError):
            ds.filter_district("X")

    def test_filter_disease(self):
        df = pd.DataFrame({
            "date":    ["2024-01-01", "2024-01-08"],
            "cases":   [10, 5],
            "disease": ["malaria", "cholera"],
        })
        ds = SurveillanceDataset.from_dataframe(
            df, disease_col="disease"
        )
        sub = ds.filter_disease("malaria")
        assert sub.n_records == 1

    def test_filter_date_start(self, surv):
        sub = surv.filter_date(start="2024-07-01")
        assert sub.n_records < surv.n_records

    def test_filter_date_end(self, surv):
        sub = surv.filter_date(end="2024-06-30")
        assert sub.n_records < surv.n_records

    def test_aggregate_weekly_returns_df(self, surv):
        agg = surv.aggregate(freq="W")
        assert isinstance(agg, pd.DataFrame)
        assert "period" in agg.columns
        assert "cases" in agg.columns

    def test_aggregate_monthly_fewer_rows(self, surv):
        weekly  = surv.aggregate(freq="W")
        monthly = surv.aggregate(freq="ME")
        assert len(monthly) < len(weekly)

    def test_aggregate_preserves_total(self, surv):
        agg = surv.aggregate(freq="W")
        assert agg["cases"].sum() == surv.total_cases



# 7. SurveillanceDataset — metrics


class TestSurveillanceMetrics:
    def test_attack_rate_scalar(self, surv):
        ar = surv.attack_rate(population=500_000)
        assert ar > 0

    def test_attack_rate_per_100k(self, surv):
        ar = surv.attack_rate(population=500_000, per=100_000)
        assert ar > 0

    def test_attack_rate_uses_population_col(self, surv):
        ar = surv.attack_rate()   # uses pop column
        assert ar > 0

    def test_attack_rate_no_pop_raises(self):
        df = pd.DataFrame({"date": ["2024-01-01"], "cases": [5]})
        ds = SurveillanceDataset.from_dataframe(df)
        with pytest.raises(ValueError):
            ds.attack_rate()

    def test_weekly_attack_rates_returns_df(self, surv):
        df = surv.weekly_attack_rates(population=500_000)
        assert "attack_rate" in df.columns

    def test_endemic_channel_keys(self, surv):
        ch = surv.endemic_channel()
        for k in ["weeks", "p_low", "p_mid", "p_high"]:
            assert k in ch

    def test_endemic_channel_lengths_match(self, surv):
        ch = surv.endemic_channel()
        assert len(ch["weeks"]) == len(ch["p_low"]) == len(ch["p_high"])

    def test_endemic_channel_ordered(self, surv):
        ch = surv.endemic_channel()
        assert ch["p_low"][0] <= ch["p_mid"][0] <= ch["p_high"][0]

    def test_to_timeseries_result(self, surv):
        from episia.api.results import TimeSeriesResult
        ts = surv.to_timeseries_result()
        assert isinstance(ts, TimeSeriesResult)
        assert len(ts.times) > 0

    def test_summary_keys(self, surv):
        s = surv.summary()
        for k in ["n_records", "total_cases", "date_start", "date_end"]:
            assert k in s



# 8. AlertEngine & Alert


class TestAlertEngine:
    @pytest.fixture
    def spike_surv(self):
        """Dataset with one large spike that should trigger alerts."""
        dates  = pd.date_range("2024-01-01", periods=20, freq="W")
        cases  = np.array([3]*10 + [80] + [3]*9, dtype=int)
        return SurveillanceDataset.from_dataframe(
            pd.DataFrame({"date": dates, "cases": cases}),
            date_col="date", cases_col="cases",
        )

    def test_returns_list(self, spike_surv):
        engine = AlertEngine(spike_surv)
        alerts = engine.run(threshold=50)
        assert isinstance(alerts, list)

    def test_threshold_triggers_alert(self, spike_surv):
        engine = AlertEngine(spike_surv)
        alerts = engine.run(threshold=50)
        assert len(alerts) >= 1

    def test_alert_fields(self, spike_surv):
        engine = AlertEngine(spike_surv)
        alerts = engine.run(threshold=50)
        a = alerts[0]
        assert hasattr(a, "period")
        assert hasattr(a, "value")
        assert hasattr(a, "severity")
        assert hasattr(a, "kind")
        assert hasattr(a, "message")

    def test_threshold_severity(self, spike_surv):
        engine = AlertEngine(spike_surv)
        alerts = engine.run(threshold=40)
        kinds = {a.kind for a in alerts}
        assert "threshold" in kinds

    def test_zscore_triggers(self, spike_surv):
        engine = AlertEngine(spike_surv)
        alerts = engine.run(zscore_threshold=2.0)
        zscore_alerts = [a for a in alerts if a.kind == "zscore"]
        assert len(zscore_alerts) >= 1

    def test_no_alerts_below_threshold(self, spike_surv):
        engine = AlertEngine(spike_surv)
        alerts = engine.run(threshold=1000)
        threshold_alerts = [a for a in alerts if a.kind == "threshold"]
        assert len(threshold_alerts) == 0

    def test_alert_summary_no_alerts(self, spike_surv):
        engine = AlertEngine(spike_surv)
        s = engine.alert_summary([])
        assert s["n_alerts"] == 0

    def test_alert_summary_with_alerts(self, spike_surv):
        engine = AlertEngine(spike_surv)
        alerts = engine.run(threshold=50)
        s = engine.alert_summary(alerts)
        assert s["n_alerts"] == len(alerts)
        assert "severity_counts" in s
        assert "first_alert" in s

    def test_epidemic_severity_double_threshold(self, spike_surv):
        # spike=80, threshold=30 → 80 >= 60 → epidemic
        engine = AlertEngine(spike_surv)
        alerts = engine.run(threshold=30)
        sev = {a.severity for a in alerts if a.kind == "threshold"}
        assert "epidemic" in sev



# 9. viz/themes/registry


class TestThemeRegistry:
    def setup_method(self):
        # Reset to default before each test
        set_theme("scientific")

    def test_available_themes(self):
        themes = get_available_themes()
        assert "scientific" in themes
        assert "dark" in themes
        assert "minimal" in themes
        assert "colorblind" in themes

    def test_set_theme_scientific(self):
        set_theme("scientific")
        assert get_theme() == "scientific"

    def test_set_theme_dark(self):
        set_theme("dark")
        assert get_theme() == "dark"

    def test_set_theme_minimal(self):
        set_theme("minimal")
        assert get_theme() == "minimal"

    def test_set_theme_colorblind(self):
        set_theme("colorblind")
        assert get_theme() == "colorblind"

    def test_set_unknown_theme_raises(self):
        with pytest.raises(ValueError, match="Unknown theme"):
            set_theme("neon_green")

    def test_get_palette_returns_list(self):
        palette = get_palette("scientific")
        assert isinstance(palette, list)
        assert len(palette) >= 4

    def test_get_palette_is_hex(self):
        for color in get_palette("scientific"):
            assert color.startswith("#")

    def test_get_palette_default_theme(self):
        set_theme("dark")
        p1 = get_palette()        # uses active theme
        p2 = get_palette("dark")  # explicit
        assert p1 == p2

    def test_get_plotly_layout_keys(self):
        layout = get_plotly_layout("scientific")
        assert "paper_bgcolor" in layout
        assert "plot_bgcolor" in layout
        assert "font" in layout
        assert "colorway" in layout

    def test_dark_has_dark_background(self):
        layout = get_plotly_layout("dark")
        bg = layout["paper_bgcolor"]
        # Dark theme background should not be white
        assert bg != "#ffffff"

    def test_register_theme(self):
        register_theme(
            "test_xcept",
            palette=["#0d6efd", "#dc3545", "#198754", "#ffc107"],
            bg_paper="#f8f9fa",
        )
        assert "test_xcept" in get_available_themes()
        set_theme("test_xcept")
        assert get_theme() == "test_xcept"

    def test_register_theme_too_few_colors_raises(self):
        with pytest.raises(ValueError, match="4 colours"):
            register_theme("bad", palette=["#000", "#fff"])

    def test_palette_returns_copy(self):
        p1 = get_palette("scientific")
        p2 = get_palette("scientific")
        p1.append("extra")
        assert len(p2) == len(get_palette("scientific"))



# 10. viz/curves — plot_epicurve


class TestPlotEpicurve:
    def test_from_raw_arrays(self):
        times  = np.arange(20)
        values = np.random.default_rng(0).poisson(10, 20).astype(float)
        fig = plot_epicurve(times=times, values=values)
        assert fig is not None

    def test_from_epidemic_curve_obj(self):
        from episia.stats.time_series import EpidemicCurve
        dates  = pd.date_range("2024-01-01", periods=10, freq="W").values
        counts = np.ones(10, dtype=float) * 5
        ec = EpidemicCurve(dates=dates, counts=counts, aggregated=False)
        fig = plot_epicurve(ec)
        assert fig is not None

    def test_no_data_raises(self):
        with pytest.raises(ValueError):
            plot_epicurve()

    def test_title_parameter(self):
        times  = np.arange(10)
        values = np.ones(10)
        # Should not raise
        fig = plot_epicurve(times=times, values=values, title="Test title")
        assert fig is not None

    def test_matplotlib_backend(self):
        import matplotlib
        matplotlib.use("Agg")
        times  = np.arange(10)
        values = np.ones(10)
        fig = plot_epicurve(times=times, values=values, backend="matplotlib")
        assert fig is not None
        import matplotlib.pyplot as plt
        plt.close("all")



# 11. viz/roc — plot_roc


class TestPlotROC:
    def test_returns_figure(self, roc_result):
        fig = plot_roc(roc_result)
        assert fig is not None

    def test_title_parameter(self, roc_result):
        fig = plot_roc(roc_result, title="Malaria RDT ROC")
        assert fig is not None

    def test_matplotlib_backend(self, roc_result):
        import matplotlib
        matplotlib.use("Agg")
        fig = plot_roc(roc_result, backend="matplotlib")
        assert fig is not None
        import matplotlib.pyplot as plt
        plt.close("all")



# 12. api/unified — EpisiaAPI (epi singleton)


class TestEpiSingleton:
    def test_is_instance(self):
        assert isinstance(epi, EpisiaAPI)

    def test_repr(self):
        r = repr(epi)
        assert "Episia" in r

    #  Stats 
    def test_risk_ratio(self):
        from episia.stats.contingency import RiskRatioResult
        r = epi.risk_ratio(40, 10, 20, 30)
        assert isinstance(r, RiskRatioResult)

    def test_odds_ratio(self):
        from episia.stats.contingency import OddsRatioResult
        r = epi.odds_ratio(40, 10, 20, 30)
        assert isinstance(r, OddsRatioResult)

    def test_proportion_ci(self):
        from episia.stats.descriptive import ProportionResult
        r = epi.proportion_ci(45, 200)
        assert isinstance(r, ProportionResult)

    def test_proportion_ci_kwargs(self):
        r = epi.proportion_ci(k=45, n=200)
        assert r.proportion == pytest.approx(0.225)

    def test_mean_ci(self):
        from episia.stats.descriptive import MeanResult
        r = epi.mean_ci([1, 2, 3, 4, 5])
        assert isinstance(r, MeanResult)

    def test_diagnostic(self):
        from episia.stats.diagnostic import DiagnosticResult
        r = epi.diagnostic(tp=80, fp=10, fn=20, tn=90)
        assert isinstance(r, DiagnosticResult)

    #  Models 
    def test_sir_returns_model(self):
        from episia.models import SIRModel
        m = epi.sir(N=10_000, I0=10, beta=0.3, gamma=0.1)
        assert isinstance(m, SIRModel)

    def test_seir_returns_model(self):
        from episia.models import SEIRModel
        m = epi.seir(N=10_000, I0=1, E0=5, beta=0.35, sigma=0.2, gamma=0.1)
        assert isinstance(m, SEIRModel)

    def test_seird_returns_model(self):
        from episia.models import SEIRDModel
        m = epi.seird(N=10_000, I0=1, E0=5,
                      beta=0.35, sigma=0.2, gamma=0.09, mu=0.01)
        assert isinstance(m, SEIRDModel)

    def test_sir_run(self):
        from episia.api.results import ModelResult
        result = epi.sir(N=10_000, I0=10, beta=0.3, gamma=0.1).run()
        assert isinstance(result, ModelResult)

    def test_seir_run(self):
        from episia.api.results import ModelResult
        result = epi.seir(N=10_000, I0=1, E0=5,
                          beta=0.35, sigma=0.2, gamma=0.1).run()
        assert isinstance(result, ModelResult)

    #  Data 
    def test_read_csv(self, tmp_path):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        p  = tmp_path / "data.csv"
        df.to_csv(p, index=False)
        ds = epi.read_csv(str(p), low_memory=False)
        assert isinstance(ds, Dataset)

    def test_surveillance_from_csv(self, tmp_path, surveillance_data):
        p = tmp_path / "surv.csv"
        surveillance_data.to_csv(p, index=False)
        ds = epi.surveillance_from_csv(str(p), date_col="date",
                                        cases_col="cases")
        assert isinstance(ds, SurveillanceDataset)

    #  Reporting 
    def test_report_from_model_result(self):
        from episia.api.reporting import EpiReport
        result = epi.sir(N=10_000, I0=10, beta=0.3, gamma=0.1).run()
        report = epi.report(result, title="Test Report")
        assert isinstance(report, EpiReport)

    def test_report_from_association_result(self):
        from episia.api.reporting import EpiReport
        result = epi.risk_ratio(40, 10, 20, 30)
        report = epi.report(result, title="RR Report")
        assert isinstance(report, EpiReport)

    #  Viz / Theme 
    def test_set_theme(self):
        epi.set_theme("dark")
        assert get_theme() == "dark"
        epi.set_theme("scientific")  # reset

    def test_get_available_themes(self):
        themes = epi.get_available_themes()
        assert isinstance(themes, list)
        assert "scientific" in themes

    def test_plot_epicurve(self):
        times  = np.arange(10)
        values = np.ones(10)
        fig = epi.plot_epicurve(times=times, values=values)
        assert fig is not None

    #  Sample size 
    def test_sample_size(self):
        from episia.stats.samplesize import SampleSizeResult
        r = epi.sample_size(
            "cohort",
            {"risk_unexposed": 0.1, "risk_ratio": 2.0}
        )
        assert isinstance(r, SampleSizeResult)
        assert r.n_per_group > 0