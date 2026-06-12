"""
tests/test_dhis2.py

Unit tests for episia.dhis2 module.
All tests use mock data — no live DHIS2 connection required.
"""

import sys
sys.path.insert(0, '/tmp')

import pytest
from episia.dhis2 import DHIS2Adapter
from episia.dhis2.constants import ENDPOINTS, PERIOD_TYPES, WHO_AFRO_ELEMENTS
from episia.data.surveillance import SurveillanceDataset, AlertEngine


#  Fixtures 

@pytest.fixture
def adapter():
    return DHIS2Adapter()

@pytest.fixture
def mock_simple():
    return {
        "headers": [{"name":"dx"},{"name":"pe"},{"name":"ou"},{"name":"value"}],
        "rows": [
            ["dx1","2024W01","OU1","5"],
            ["dx1","2024W02","OU1","10"],
            ["dx1","2024W03","OU1","15"],
            ["dx1","2024W04","OU1","20"],
        ]
    }

@pytest.fixture
def mock_with_deaths():
    return {
        "headers": [{"name":"dx"},{"name":"pe"},{"name":"ou"},{"name":"value"}],
        "rows": [
            ["elem_cases",  "2024W01","District_A","12"],
            ["elem_cases",  "2024W02","District_A","18"],
            ["elem_cases",  "2024W03","District_A","25"],
            ["elem_cases",  "2024W04","District_A","8"],
            ["elem_cases",  "2024W05","District_A","31"],
            ["elem_deaths", "2024W01","District_A","1"],
            ["elem_deaths", "2024W02","District_A","2"],
            ["elem_deaths", "2024W03","District_A","3"],
        ]
    }

@pytest.fixture
def mock_dvs():
    return {
        "dataValues": [
            {"period":"2024W01","orgUnit":"OU1","dataElement":"dx1","value":"5"},
            {"period":"2024W02","orgUnit":"OU1","dataElement":"dx1","value":"10"},
            {"period":"2024W03","orgUnit":"OU1","dataElement":"dx2","value":"2"},
        ]
    }


#  Constants 

class TestConstants:

    def test_all_endpoints_present(self):
        for key in ("analytics","data_values","org_units","data_elements","me"):
            assert key in ENDPOINTS

    def test_endpoints_start_with_slash(self):
        for k, v in ENDPOINTS.items():
            assert v.startswith("/"), f"{k} must start with '/'"

    def test_period_types_present(self):
        for key in ("weekly","monthly","quarterly","yearly"):
            assert key in PERIOD_TYPES

    def test_who_afro_uids_are_11_chars(self):
        for k, uid in WHO_AFRO_ELEMENTS.items():
            assert len(uid) == 11, f"{k}: DHIS2 UIDs must be 11 chars"


#  DHIS2Adapter: from_analytics_response 

class TestAdapterAnalytics:

    def test_returns_surveillance_dataset(self, adapter, mock_simple):
        ds = adapter.from_analytics_response(mock_simple)
        assert isinstance(ds, SurveillanceDataset)

    def test_total_cases_correct(self, adapter, mock_simple):
        ds = adapter.from_analytics_response(mock_simple, cases_element="dx1")
        assert ds.total_cases == 50

    def test_n_records_correct(self, adapter, mock_simple):
        ds = adapter.from_analytics_response(mock_simple, cases_element="dx1")
        assert ds.n_records == 4

    def test_district_col_set(self, adapter, mock_simple):
        ds = adapter.from_analytics_response(mock_simple)
        assert ds.district_col == "org_unit"

    def test_with_deaths_element(self, adapter, mock_with_deaths):
        ds = adapter.from_analytics_response(
            mock_with_deaths,
            cases_element  = "elem_cases",
            deaths_element = "elem_deaths",
        )
        assert ds.total_cases == 94
        assert ds.deaths_col is not None
        assert ds.total_deaths == 6

    def test_cfr_computed(self, adapter, mock_with_deaths):
        ds = adapter.from_analytics_response(
            mock_with_deaths,
            cases_element  = "elem_cases",
            deaths_element = "elem_deaths",
        )
        assert ds.cfr is not None
        assert 0 < ds.cfr < 1

    def test_empty_rows(self, adapter):
        ds = adapter.from_analytics_response({"headers":[],"rows":[]})
        assert isinstance(ds, SurveillanceDataset)
        assert ds.n_records == 0

    def test_missing_rows_key(self, adapter):
        ds = adapter.from_analytics_response({})
        assert isinstance(ds, SurveillanceDataset)

    def test_multi_district(self, adapter):
        response = {
            "headers": [{"name":"dx"},{"name":"pe"},{"name":"ou"},{"name":"value"}],
            "rows": [
                ["dx1","2024W01","Dist_A","10"],
                ["dx1","2024W01","Dist_B","20"],
                ["dx1","2024W01","Dist_C","5"],
            ]
        }
        ds = adapter.from_analytics_response(response, cases_element="dx1")
        assert len(ds.districts) == 3


#  DHIS2Adapter: period parsing 

class TestAdapterPeriodParsing:

    def _ds_from_period(self, adapter, period_str):
        response = {
            "headers": [{"name":"dx"},{"name":"pe"},{"name":"ou"},{"name":"value"}],
            "rows": [["dx1", period_str, "OU1", "5"]]
        }
        return adapter.from_analytics_response(response)

    def test_iso_week_parsed(self, adapter):
        ds = self._ds_from_period(adapter, "2024W01")
        p = ds.df["period"].iloc[0]
        assert p.year == 2024 and p.month == 1

    def test_iso_week_middle_year(self, adapter):
        ds = self._ds_from_period(adapter, "2024W26")
        p = ds.df["period"].iloc[0]
        assert p.year == 2024

    def test_month_parsed(self, adapter):
        ds = self._ds_from_period(adapter, "202403")
        p = ds.df["period"].iloc[0]
        assert p.year == 2024 and p.month == 3

    def test_quarter_q1(self, adapter):
        ds = self._ds_from_period(adapter, "2024Q1")
        p = ds.df["period"].iloc[0]
        assert p.month == 1

    def test_quarter_q2(self, adapter):
        ds = self._ds_from_period(adapter, "2024Q2")
        p = ds.df["period"].iloc[0]
        assert p.month == 4

    def test_quarter_q3(self, adapter):
        ds = self._ds_from_period(adapter, "2024Q3")
        p = ds.df["period"].iloc[0]
        assert p.month == 7

    def test_quarter_q4(self, adapter):
        ds = self._ds_from_period(adapter, "2024Q4")
        p = ds.df["period"].iloc[0]
        assert p.month == 10

    def test_year_parsed(self, adapter):
        ds = self._ds_from_period(adapter, "2024")
        p = ds.df["period"].iloc[0]
        assert p.year == 2024 and p.month == 1

    def test_all_four_types_no_nat(self, adapter):
        import pandas as pd
        response = {
            "headers": [{"name":"dx"},{"name":"pe"},{"name":"ou"},{"name":"value"}],
            "rows": [
                ["dx1","2024W01","OU1","1"],
                ["dx1","202401", "OU1","2"],
                ["dx1","2024Q1", "OU1","3"],
                ["dx1","2024",   "OU1","4"],
            ]
        }
        ds = adapter.from_analytics_response(response)
        assert ds.df["period"].notna().all()


#  DHIS2Adapter: from_data_value_sets 

class TestAdapterDataValueSets:

    def test_returns_dataframe(self, adapter, mock_dvs):
        import pandas as pd
        df = adapter.from_data_value_sets(mock_dvs)
        assert isinstance(df, pd.DataFrame)

    def test_correct_row_count(self, adapter, mock_dvs):
        df = adapter.from_data_value_sets(mock_dvs)
        assert len(df) == 3

    def test_expected_columns(self, adapter, mock_dvs):
        df = adapter.from_data_value_sets(mock_dvs)
        for col in ("period","org_unit","data_element","value"):
            assert col in df.columns

    def test_value_is_numeric(self, adapter, mock_dvs):
        df = adapter.from_data_value_sets(mock_dvs)
        assert df["value"].dtype in ["float64","int64"]

    def test_empty_returns_empty_df(self, adapter):
        import pandas as pd
        df = adapter.from_data_value_sets({"dataValues":[]})
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0


#  DHIS2Client (offline) 

class TestDHIS2ClientOffline:

    def test_repr_contains_url(self):
        pytest.importorskip("requests")
        from episia.dhis2 import DHIS2Client
        c = DHIS2Client("https://play.dhis2.org", "admin", "district")
        assert "play.dhis2.org" in repr(c)

    def test_repr_contains_username(self):
        pytest.importorskip("requests")
        from episia.dhis2 import DHIS2Client
        c = DHIS2Client("https://play.dhis2.org", "admin", "district")
        assert "admin" in repr(c)

    def test_trailing_slash_stripped(self):
        pytest.importorskip("requests")
        from episia.dhis2 import DHIS2Client
        c = DHIS2Client("https://play.dhis2.org/", "admin", "district")
        assert not c.url.endswith("/")

    def test_ping_unreachable_host_raises(self):
        pytest.importorskip("requests")
        from episia.dhis2 import DHIS2Client
        c = DHIS2Client("http://localhost:19999", "a", "b", timeout=1)
        with pytest.raises(ConnectionError):
            c.ping()

    def test_import_error_without_requests(self, monkeypatch):
        import builtins
        real = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name == "requests":
                raise ImportError("mocked")
            return real(name, *args, **kwargs)
        monkeypatch.setattr(builtins, "__import__", mock_import)
        with pytest.raises(ImportError, match="pip install episia"):
            from episia.dhis2.client import DHIS2Client as C
            C("http://x", "u", "p")


#  Integration: adapter + AlertEngine 

class TestDHIS2Integration:

    def test_to_alert_engine(self, adapter, mock_simple):
        ds = adapter.from_analytics_response(mock_simple, cases_element="dx1")
        engine = AlertEngine(ds)
        alerts = engine.run(threshold=12)
        assert isinstance(alerts, list)

    def test_alert_summary(self, adapter, mock_simple):
        ds = adapter.from_analytics_response(mock_simple, cases_element="dx1")
        engine = AlertEngine(ds)
        alerts = engine.run(threshold=8)
        summary = engine.alert_summary(alerts)
        assert "n_alerts" in summary
        assert summary["n_alerts"] >= 0

    def test_to_timeseries_result(self, adapter, mock_simple):
        from episia.api.results import TimeSeriesResult
        ds = adapter.from_analytics_response(mock_simple, cases_element="dx1")
        ts = ds.to_timeseries_result()
        assert isinstance(ts, TimeSeriesResult)
        assert len(ts.values) >= 1

    def test_aggregate_weekly(self, adapter, mock_simple):
        ds = adapter.from_analytics_response(mock_simple, cases_element="dx1")
        agg = ds.aggregate(freq="W")
        assert len(agg) >= 1

    def test_attack_rate(self, adapter, mock_simple):
        ds = adapter.from_analytics_response(mock_simple, cases_element="dx1")
        ar = ds.attack_rate(population=500_000, per=100_000)
        assert ar > 0

    def test_filter_district(self, adapter):
        response = {
            "headers": [{"name":"dx"},{"name":"pe"},{"name":"ou"},{"name":"value"}],
            "rows": [
                ["dx1","2024W01","Dist_A","10"],
                ["dx1","2024W02","Dist_A","15"],
                ["dx1","2024W01","Dist_B","5"],
            ]
        }
        ds = adapter.from_analytics_response(response, cases_element="dx1")
        ds_a = ds.filter_district("Dist_A")
        assert ds_a.total_cases == 25
        assert ds_a.n_records   == 2

    def test_endemic_channel_multiweek(self, adapter):
        rows = []
        for year in [2022,2023,2024]:
            for week in range(1,10):
                rows.append(["dx1",f"{year}W{week:02d}","OU1",str(week+1)])
        response = {
            "headers":[{"name":"dx"},{"name":"pe"},{"name":"ou"},{"name":"value"}],
            "rows": rows
        }
        ds = adapter.from_analytics_response(response, cases_element="dx1")
        channel = ds.endemic_channel()
        assert len(channel["weeks"]) > 0
        assert "p_high" in channel

# ── period_range (issue #6) ────────────────────────────────────────────────

class TestPeriodRange:

    def test_monthly_basic(self):
        from episia.dhis2 import period_range
        result = period_range("202401", "202406")
        assert result == "202401;202402;202403;202404;202405;202406"

    def test_monthly_single_period(self):
        from episia.dhis2 import period_range
        assert period_range("202401", "202401") == "202401"

    def test_monthly_year_boundary(self):
        from episia.dhis2 import period_range
        result = period_range("202311", "202402")
        assert result == "202311;202312;202401;202402"

    def test_weekly_basic(self):
        from episia.dhis2 import period_range
        result = period_range("2024W01", "2024W04")
        assert result == "2024W01;2024W02;2024W03;2024W04"

    def test_weekly_single(self):
        from episia.dhis2 import period_range
        assert period_range("2024W10", "2024W10") == "2024W10"

    def test_weekly_year_boundary(self):
        from episia.dhis2 import period_range
        result = period_range("2023W51", "2024W02")
        periods = result.split(";")
        assert periods[0] == "2023W51"
        assert periods[-1] == "2024W02"
        assert len(periods) >= 3

    def test_weekly_52_weeks(self):
        from episia.dhis2 import period_range
        result = period_range("2024W01", "2024W52")
        periods = result.split(";")
        assert len(periods) == 52

    def test_quarterly_basic(self):
        from episia.dhis2 import period_range
        result = period_range("2024Q1", "2024Q4")
        assert result == "2024Q1;2024Q2;2024Q3;2024Q4"

    def test_quarterly_year_boundary(self):
        from episia.dhis2 import period_range
        result = period_range("2023Q3", "2024Q2")
        assert result == "2023Q3;2023Q4;2024Q1;2024Q2"

    def test_start_after_end_raises(self):
        from episia.dhis2 import period_range
        with pytest.raises(ValueError):
            period_range("202406", "202401")

    def test_mixed_formats_raises(self):
        from episia.dhis2 import period_range
        with pytest.raises(ValueError):
            period_range("202401", "2024W04")

    def test_unknown_format_raises(self):
        from episia.dhis2 import period_range
        with pytest.raises(ValueError):
            period_range("2024-01", "2024-06")

    def test_exported_from_dhis2_module(self):
        from episia.dhis2 import period_range
        assert callable(period_range)


# ── SurveillanceDataset.completeness (issue #7) ───────────────────────────

class TestCompleteness:

    @pytest.fixture
    def weekly_ds_complete(self, adapter):
        """4 semaines consécutives sans gaps."""
        response = {
            "headers": [{"name":"dx"},{"name":"pe"},{"name":"ou"},{"name":"value"}],
            "rows": [
                ["dx1","2024W01","OU1","10"],
                ["dx1","2024W02","OU1","12"],
                ["dx1","2024W03","OU1","8"],
                ["dx1","2024W04","OU1","15"],
            ]
        }
        return adapter.from_analytics_response(response, cases_element="dx1")

    @pytest.fixture
    def weekly_ds_with_gap(self, adapter):
        """W01, W02, W04, W05 — W03 manquante."""
        response = {
            "headers": [{"name":"dx"},{"name":"pe"},{"name":"ou"},{"name":"value"}],
            "rows": [
                ["dx1","2024W01","OU1","10"],
                ["dx1","2024W02","OU1","12"],
                ["dx1","2024W04","OU1","15"],
                ["dx1","2024W05","OU1","9"],
            ]
        }
        return adapter.from_analytics_response(response, cases_element="dx1")

    def test_returns_dict(self, weekly_ds_complete):
        result = weekly_ds_complete.completeness()
        assert isinstance(result, dict)

    def test_required_keys(self, weekly_ds_complete):
        result = weekly_ds_complete.completeness()
        for key in ("expected_periods","reported_periods","completeness_rate","missing_periods"):
            assert key in result, f"Missing key: {key}"

    def test_complete_dataset_rate_is_one(self, weekly_ds_complete):
        result = weekly_ds_complete.completeness(freq="W")
        assert result["completeness_rate"] == pytest.approx(1.0)

    def test_complete_dataset_no_missing(self, weekly_ds_complete):
        result = weekly_ds_complete.completeness(freq="W")
        assert result["missing_periods"] == []

    def test_gap_detected(self, weekly_ds_with_gap):
        result = weekly_ds_with_gap.completeness(freq="W")
        assert result["completeness_rate"] < 1.0
        assert len(result["missing_periods"]) >= 1

    def test_reported_periods_count(self, weekly_ds_with_gap):
        result = weekly_ds_with_gap.completeness(freq="W")
        # reported = expected - nb de périodes manquantes
        assert result["reported_periods"] == result["expected_periods"] - len(result["missing_periods"])
        assert result["reported_periods"] >= 0

    def test_completeness_rate_range(self, weekly_ds_with_gap):
        result = weekly_ds_with_gap.completeness(freq="W")
        assert 0.0 <= result["completeness_rate"] <= 1.0

    def test_missing_periods_is_list(self, weekly_ds_complete):
        result = weekly_ds_complete.completeness()
        assert isinstance(result["missing_periods"], list)

    def test_single_record_raises(self, adapter):
        response = {
            "headers": [{"name":"dx"},{"name":"pe"},{"name":"ou"},{"name":"value"}],
            "rows": [["dx1","2024W01","OU1","5"]]
        }
        ds = adapter.from_analytics_response(response, cases_element="dx1")
        with pytest.raises(ValueError):
            ds.completeness()