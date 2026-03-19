"""
Constants for DHIS2 integration.

This module provides endpoint definitions, field mappings, and preset
data element UIDs for common WHO/AFRO notifiable diseases.

API Endpoints
-------------

.. autodata:: ENDPOINTS
   :annotation:

Standard field mappings
-----------------------

.. autodata:: ANALYTICS_FIELDS
   :annotation:

Period type mappings
--------------------

.. autodata:: PERIOD_TYPES
   :annotation:

WHO/AFRO data elements
----------------------

.. autodata:: WHO_AFRO_ELEMENTS
   :annotation:
"""

ENDPOINTS = {
    "analytics":     "/api/analytics",
    "data_values":   "/api/dataValueSets",
    "org_units":     "/api/organisationUnits",
    "data_elements": "/api/dataElements",
    "datasets":      "/api/dataSets",
    "periods":       "/api/periods",
    "me":            "/api/me",
}

ANALYTICS_FIELDS = {
    "period":   "pe",
    "org_unit": "ou",
    "data":     "dx",
    "value":    "value",
}

PERIOD_TYPES = {
    "weekly":    "W",
    "monthly":   "M",
    "quarterly": "Q",
    "yearly":    "Y",
}

WHO_AFRO_ELEMENTS = {
    "malaria_confirmed": "fbfJHSPpUQD",
    "malaria_deaths":    "cYeuwXTCPkU",
    "meningitis_cases":  "hfdmMSPBgLG",
    "cholera_cases":     "bqK6eSIwo3h",
    "measles_cases":     "Jtf34kNZhzP",
}