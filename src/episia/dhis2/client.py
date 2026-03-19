"""
episia.dhis2.client - DHIS2 REST API client.

Requires: pip install episia[dhis2]   (adds requests dependency)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from .adapter   import DHIS2Adapter
from .constants import ENDPOINTS
from ..data.surveillance import SurveillanceDataset


class DHIS2Client:
    """
    DHIS2 REST API client for Episia.

    Connects to any DHIS2 instance and converts data to
    SurveillanceDataset for immediate analysis with Episia.

    Requires ``requests``:  pip install episia[dhis2]

    Args:
        url:      Base URL of the DHIS2 instance (no trailing slash).
        username: DHIS2 username.
        password: DHIS2 password.
        timeout:  HTTP timeout in seconds (default 30).
        verify:   SSL certificate verification (default True).

    Example::

        from episia.dhis2 import DHIS2Client

        # Public DHIS2 demo instance
        client = DHIS2Client(
            url      = "https://play.dhis2.org/40.2.2",
            username = "admin",
            password = "district",
        )

        # Check connection
        client.ping()

        # Fetch data as SurveillanceDataset
        ds = client.to_dataset(
            data_element = "FTRrcoaog83",
            period       = "2024W01:2024W52",
            org_unit     = "ImspTQPwCqd",
        )
        print(ds)
        ds.to_timeseries_result().plot().show()
    """

    def __init__(
        self,
        url:       str,
        username:  str,
        password:  str,
        api_token: Optional[str] = None,
        timeout:   int  = 30,
        verify:    bool = True,
    ):
        """
        Args:
            url:       Base URL of the DHIS2 instance.
            username:  DHIS2 username (used when api_token is None).
            password:  DHIS2 password (used when api_token is None).
            api_token: Personal access token (PAT). When provided,
                       Basic Auth is not used. Generate one at:
                       Profile -> Personal access tokens in DHIS2.
            timeout:   HTTP timeout in seconds (default 30).
            verify:    SSL certificate verification (default True).
        """
        try:
            import requests
        except ImportError:
            raise ImportError(
                "requests is required for DHIS2 integration.\n"
                "Install with: pip install episia[dhis2]"
            )

        self.url       = url.rstrip("/")
        self.username  = username
        self.password  = password
        self.api_token = api_token
        self.timeout   = timeout
        self.verify    = verify
        self._session  = requests.Session()

        if api_token:
            # PAT authentication -- DHIS2 2.38+
            self._session.headers.update({
                "Authorization":    f"ApiToken {api_token}",
                "Accept":           "application/json",
                "X-Requested-With": "XMLHttpRequest",
            })
        else:
            # Basic Auth -- older instances or service accounts
            self._session.auth = (username, password)
            self._session.headers.update({
                "Accept":           "application/json",
                "X-Requested-With": "XMLHttpRequest",
            })

        self._adapter = DHIS2Adapter()

    # Connection

    def ping(self) -> bool:
        """
        Test connection to the DHIS2 instance.

        Returns:
            True if connection is successful.

        Raises:
            ConnectionError: if the server is unreachable or credentials invalid.
        """
        try:
            r = self._get(ENDPOINTS["me"])
            return "id" in r
        except Exception as e:
            raise ConnectionError(f"DHIS2 connection failed: {e}")

    # Data fetching

    def fetch_analytics(
        self,
        data_elements: Union[str, List[str]],
        period:        str,
        org_unit:      str,
        org_unit_mode: str = "SELECTED",
    ) -> Dict[str, Any]:
        """
        Fetch data from the DHIS2 /api/analytics endpoint.

        Args:
            data_elements: Data element UID or list of UIDs.
            period:        Period expression. Examples:
                           - Single week: '2024W01'
                           - Range:       '2024W01:2024W52'
                           - Last N:      'LAST_12_WEEKS'
            org_unit:      Organisation unit UID.
            org_unit_mode: SELECTED, CHILDREN, or DESCENDANTS.

        Returns:
            Raw DHIS2 analytics JSON response.
        """
        if isinstance(data_elements, str):
            data_elements = [data_elements]

        dx = ";".join(data_elements)
        params = {
            "dimension": [f"dx:{dx}", f"pe:{period}", f"ou:{org_unit}"],
            "displayProperty": "NAME",
            "outputIdScheme": "UID",
            "ignoreLimit": "true",
        }
        if org_unit_mode != "SELECTED":
            params["ouMode"] = org_unit_mode

        return self._get(ENDPOINTS["analytics"], params=params)

    def fetch_data_value_sets(
        self,
        data_set:  str,
        period:    str,
        org_unit:  str,
    ) -> Dict[str, Any]:
        """
        Fetch raw data values from /api/dataValueSets.

        Args:
            data_set:  Data set UID.
            period:    Period string (e.g. '2024W01').
            org_unit:  Organisation unit UID.

        Returns:
            Raw DHIS2 dataValueSets JSON response.
        """
        params = {
            "dataSet":  data_set,
            "period":   period,
            "orgUnit":  org_unit,
        }
        return self._get(ENDPOINTS["data_values"], params=params)

    def list_org_units(
        self,
        level:   Optional[int] = None,
        parent:  Optional[str] = None,
        fields:  str = "id,name,level,shortName",
    ) -> List[Dict[str, Any]]:
        """
        List organisation units from DHIS2.

        Args:
            level:   Filter by hierarchy level (1=national, 2=region…).
            parent:  Filter by parent UID.
            fields:  Comma-separated fields to return.

        Returns:
            List of organisation unit dicts.
        """
        params: Dict[str, Any] = {"fields": fields, "paging": "false"}
        if level is not None:
            params["level"] = level
        if parent is not None:
            params["parent"] = parent

        response = self._get(ENDPOINTS["org_units"], params=params)
        return response.get("organisationUnits", [])

    def list_data_elements(
        self,
        fields: str = "id,name,shortName,valueType",
    ) -> List[Dict[str, Any]]:
        """
        List available data elements from DHIS2.

        Args:
            fields: Comma-separated fields to return.

        Returns:
            List of data element dicts.
        """
        params = {"fields": fields, "paging": "false"}
        response = self._get(ENDPOINTS["data_elements"], params=params)
        return response.get("dataElements", [])

    # High-level convenience

    def to_dataset(
        self,
        data_element:   str,
        period:         str,
        org_unit:       str,
        deaths_element: Optional[str] = None,
        org_unit_mode:  str = "SELECTED",
    ) -> SurveillanceDataset:
        """
        Fetch data from DHIS2 and return a ready-to-use SurveillanceDataset.

        This is the main entry point for Episia-DHIS2 integration.

        Args:
            data_element:   UID of the cases data element.
            period:         Period expression (e.g. '2024W01:2024W52').
            org_unit:       Organisation unit UID.
            deaths_element: UID of deaths data element (optional).
            org_unit_mode:  SELECTED, CHILDREN, or DESCENDANTS.

        Returns:
            SurveillanceDataset ready for Episia analysis.

        Example::

            ds = client.to_dataset(
                data_element = "FTRrcoaog83",
                period       = "LAST_52_WEEKS",
                org_unit     = "ImspTQPwCqd",
            )
            engine = AlertEngine(ds)
            alerts = engine.run(threshold=15)
        """
        elements = [data_element]
        if deaths_element:
            elements.append(deaths_element)

        raw = self.fetch_analytics(
            data_elements = elements,
            period        = period,
            org_unit      = org_unit,
            org_unit_mode = org_unit_mode,
        )

        return self._adapter.from_analytics_response(
            raw,
            cases_element  = data_element,
            deaths_element = deaths_element,
        )

    def to_dataset_by_district(
        self,
        data_element: str,
        period:       str,
        org_unit:     str,
    ) -> SurveillanceDataset:
        """
        Fetch data disaggregated by child org units (districts).

        Equivalent to to_dataset() with org_unit_mode='CHILDREN'.

        Returns:
            SurveillanceDataset with district_col='org_unit'.
        """
        return self.to_dataset(
            data_element  = data_element,
            period        = period,
            org_unit      = org_unit,
            org_unit_mode = "CHILDREN",
        )

    # Internal HTTP helper

    def _get(
        self,
        endpoint: str,
        params:   Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a GET request to the DHIS2 API.

        Args:
            endpoint: API endpoint path (e.g. '/api/analytics').
            params:   Query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            requests.HTTPError: on non-2xx responses.
            ConnectionError:    on network errors.
        """

        url = self.url + endpoint
        try:
            response = self._session.get(
                url, params=params,
                timeout=self.timeout,
                verify=self.verify,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"DHIS2 request failed [{url}]: {e}")

    def __repr__(self) -> str:
        auth = "token" if self.api_token else f"user={self.username}"
        return f"DHIS2Client(url='{self.url}', {auth})"