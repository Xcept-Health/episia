"""
episia.dhis2.adapter - Convert DHIS2 API responses to SurveillanceDataset.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..data.surveillance import SurveillanceDataset


class DHIS2Adapter:
    """
    Converts raw DHIS2 analytics API responses to SurveillanceDataset.

    This class is used internally by DHIS2Client but can also be used
    standalone to convert data you have already fetched.

    Example::

        adapter = DHIS2Adapter()
        ds = adapter.from_analytics_response(raw_json)
    """

    def from_analytics_response(
        self,
        response: Dict[str, Any],
        cases_element:  Optional[str] = None,
        deaths_element: Optional[str] = None,
    ) -> SurveillanceDataset:
        """
        Convert a DHIS2 /api/analytics JSON response to SurveillanceDataset.

        The analytics API returns rows like:
            [dx, pe, ou, value]
        where dx=data element UID, pe=period, ou=org unit UID.

        Args:
            response:        Raw JSON dict from DHIS2 analytics endpoint.
            cases_element:   UID of the cases data element (filters rows).
            deaths_element:  UID of the deaths data element (optional).

        Returns:
            SurveillanceDataset with date_col='period', cases_col='cases'.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required: pip install pandas")

        headers = [h["name"] for h in response.get("headers", [])]
        rows    = response.get("rows", [])

        if not rows:
            import pandas as pd
            empty = pd.DataFrame(columns=["period", "org_unit", "data_element", "cases"])
            return SurveillanceDataset(empty, date_col="period", cases_col="cases")

        df = pd.DataFrame(rows, columns=headers)

        # Rename standard DHIS2 columns
        rename = {}
        if "pe" in df.columns: rename["pe"] = "period"
        if "ou" in df.columns: rename["ou"] = "org_unit"
        if "dx" in df.columns: rename["dx"] = "data_element"
        df = df.rename(columns=rename)

        df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0)

        # Filter and pivot cases vs deaths
        if cases_element and "data_element" in df.columns:
            cases_df = df[df["data_element"] == cases_element].copy()
            cases_df = cases_df.rename(columns={"value": "cases"})
            # If filter returned nothing, fall back to all rows
            if len(cases_df) == 0:
                cases_df = df.copy()
                cases_df = cases_df.rename(columns={"value": "cases"})
        else:
            cases_df = df.copy()
            cases_df = cases_df.rename(columns={"value": "cases"})

        # Ensure cases column always exists
        if "cases" not in cases_df.columns:
            cases_df["cases"] = 0

        if deaths_element and "data_element" in df.columns:
            deaths_df = df[df["data_element"] == deaths_element][["period","org_unit","value"]].copy()
            deaths_df = deaths_df.rename(columns={"value": "deaths"})
            cases_df  = cases_df.merge(deaths_df, on=["period","org_unit"], how="left")
            deaths_col = "deaths"
        else:
            deaths_col = None

        # Parse period → datetime
        cases_df["period"] = self._parse_dhis2_period(cases_df["period"])

        return SurveillanceDataset(
            cases_df,
            date_col     = "period",
            cases_col    = "cases",
            deaths_col   = deaths_col,
            district_col = "org_unit" if "org_unit" in cases_df.columns else None,
        )

    def from_data_value_sets(
        self,
        response: Dict[str, Any],
    ) -> "pd.DataFrame":
        """
        Convert a DHIS2 /api/dataValueSets response to a flat DataFrame.

        Args:
            response: Raw JSON from dataValueSets endpoint.

        Returns:
            pandas DataFrame with columns: period, org_unit, data_element, value.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required: pip install pandas")

        values = response.get("dataValues", [])
        if not values:
            return pd.DataFrame(columns=["period","org_unit","data_element","value"])

        rows = []
        for v in values:
            rows.append({
                "period":       v.get("period",""),
                "org_unit":     v.get("orgUnit",""),
                "data_element": v.get("dataElement",""),
                "value":        float(v.get("value", 0) or 0),
            })

        df = pd.DataFrame(rows)
        df["period"] = self._parse_dhis2_period(df["period"])
        return df

    def _parse_dhis2_period(self, series) -> "pd.Series":
        """
        Parse DHIS2 period strings to pandas Timestamps.

        Handles:
            2024W01   ISO week
            202401    month YYYYMM
            2024Q1    quarter
            2024      year
        """
        import pandas as pd
        import re

        def _parse_one(p: str):
            p = str(p).strip()
            # ISO week: 2024W01
            m = re.match(r'^(\d{4})W(\d{1,2})$', p)
            if m:
                year, week = int(m.group(1)), int(m.group(2))
                return pd.Timestamp.fromisocalendar(year, week, 1)
            # Month: 202401
            m = re.match(r'^(\d{4})(\d{2})$', p)
            if m:
                return pd.Timestamp(f"{m.group(1)}-{m.group(2)}-01")
            # Quarter: 2024Q1
            m = re.match(r'^(\d{4})Q(\d)$', p)
            if m:
                month = (int(m.group(2)) - 1) * 3 + 1
                return pd.Timestamp(f"{m.group(1)}-{month:02d}-01")
            # Year: 2024
            m = re.match(r'^(\d{4})$', p)
            if m:
                return pd.Timestamp(f"{m.group(1)}-01-01")
            # Fallback
            try:
                return pd.Timestamp(p)
            except Exception:
                return pd.NaT

        return series.apply(_parse_one)