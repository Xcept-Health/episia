"""
episia.dhis2.periods - DHIS2 period utilities.

Provides helpers to build period strings compatible with the DHIS2
analytics API.
"""
from __future__ import annotations

import re
from typing import List


def period_range(start: str, end: str) -> str:
    """
    Build a semicolon-separated DHIS2 period string from *start* to *end*
    (inclusive).

    Supports monthly, weekly, and quarterly period formats.

    Args:
        start: Start period string.  Examples: ``"202401"``, ``"2024W01"``,
               ``"2024Q1"``.
        end:   End period string in the same format as *start*.

    Returns:
        Semicolon-separated period string, e.g.
        ``"202401;202402;202403"``.

    Raises:
        ValueError: if *start* and *end* use different formats, or if the
                    format is not recognised, or if *start* is after *end*.

    Examples::

        from episia.dhis2 import period_range

        # Monthly
        period_range("202401", "202406")
        # → "202401;202402;202403;202404;202405;202406"

        # Weekly
        period_range("2024W01", "2024W04")
        # → "2024W01;2024W02;2024W03;2024W04"

        # Quarterly
        period_range("2024Q1", "2024Q4")
        # → "2024Q1;2024Q2;2024Q3;2024Q4"
    """
    periods = _generate_periods(start, end)
    if not periods:
        raise ValueError(
            f"No periods generated between '{start}' and '{end}'. "
            "Make sure start <= end."
        )
    return ";".join(periods)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_MONTHLY_RE   = re.compile(r"^(\d{4})(0[1-9]|1[0-2])$")
_WEEKLY_RE    = re.compile(r"^(\d{4})W(\d{1,2})$")
_QUARTERLY_RE = re.compile(r"^(\d{4})Q([1-4])$")


def _detect_format(period: str) -> str:
    """Return 'monthly', 'weekly', or 'quarterly'; raise ValueError otherwise."""
    if _MONTHLY_RE.match(period):
        return "monthly"
    if _WEEKLY_RE.match(period):
        return "weekly"
    if _QUARTERLY_RE.match(period):
        return "quarterly"
    raise ValueError(
        f"Unrecognised DHIS2 period format: '{period}'. "
        "Expected monthly (YYYYMM), weekly (YYYYWnn), or quarterly (YYYYQn)."
    )


def _generate_periods(start: str, end: str) -> List[str]:
    fmt_start = _detect_format(start)
    fmt_end   = _detect_format(end)

    if fmt_start != fmt_end:
        raise ValueError(
            f"start ('{start}') and end ('{end}') use different period formats: "
            f"'{fmt_start}' vs '{fmt_end}'."
        )

    if fmt_start == "monthly":
        return _monthly_range(start, end)
    if fmt_start == "weekly":
        return _weekly_range(start, end)
    return _quarterly_range(start, end)


def _monthly_range(start: str, end: str) -> List[str]:
    sy, sm = int(start[:4]), int(start[4:])
    ey, em = int(end[:4]),   int(end[4:])

    if (sy, sm) > (ey, em):
        raise ValueError(f"start '{start}' is after end '{end}'.")

    result: List[str] = []
    y, m = sy, sm
    while (y, m) <= (ey, em):
        result.append(f"{y}{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return result


def _weekly_range(start: str, end: str) -> List[str]:
    """
    Generate ISO-week period strings from start to end.

    Uses the ISO 8601 week calendar: week 1 is the week containing the
    first Thursday of the year (same as Python's datetime.isocalendar).
    """
    import datetime

    def _parse_week(s: str):
        m = _WEEKLY_RE.match(s)
        year, week = int(m.group(1)), int(m.group(2))
        # ISO weeks are 1-based; validate range
        max_week = _iso_weeks_in_year(year)
        if not (1 <= week <= max_week):
            raise ValueError(
                f"Week {week} is out of range for year {year} "
                f"(max {max_week} ISO weeks)."
            )
        return year, week

    def _iso_weeks_in_year(year: int) -> int:
        # The last day of the ISO year is the Thursday of the last week.
        # Dec 28 is always in the last ISO week of its year.
        return datetime.date(year, 12, 28).isocalendar()[1]

    def _next_week(year: int, week: int):
        max_week = _iso_weeks_in_year(year)
        week += 1
        if week > max_week:
            week = 1
            year += 1
        return year, week

    sy, sw = _parse_week(start)
    ey, ew = _parse_week(end)

    if (sy, sw) > (ey, ew):
        raise ValueError(f"start '{start}' is after end '{end}'.")

    result: List[str] = []
    y, w = sy, sw
    while (y, w) <= (ey, ew):
        result.append(f"{y}W{w:02d}")
        y, w = _next_week(y, w)
    return result


def _quarterly_range(start: str, end: str) -> List[str]:
    sy, sq = int(start[:4]), int(start[5])
    ey, eq = int(end[:4]),   int(end[5])

    if (sy, sq) > (ey, eq):
        raise ValueError(f"start '{start}' is after end '{end}'.")

    result: List[str] = []
    y, q = sy, sq
    while (y, q) <= (ey, eq):
        result.append(f"{y}Q{q}")
        q += 1
        if q > 4:
            q = 1
            y += 1
    return result