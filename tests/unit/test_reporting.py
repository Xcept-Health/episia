"""
tests/unit/test_reporting.py
Unit tests for epitools.api.reporting

Coverage
--------
    EpiReport.__init__          constructor defaults & custom values
    EpiReport.add_*             all section adders
    EpiReport.to_markdown()     structure, content, edge cases
    EpiReport.to_html()         structure, escaping, sections
    EpiReport.to_json()         schema, serialisation
    EpiReport.save_*            file creation, return value, encoding
    _fmt                        formatting helper
    _esc                        HTML-escaping helper
    report_from_result          factory (minimal stub)
    report_from_model           factory (minimal stub)
"""

from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import target 
from epitools.api.reporting import (
    EpiReport,
    ReportSection,
    _esc,
    _fmt,
    report_from_model,
    report_from_result,
)



# Fixtures


@pytest.fixture
def empty_report():
    return EpiReport(title="Test Report")


@pytest.fixture
def full_report():
    r = EpiReport(
        title="Weekly Bulletin – Week 12",
        author="Dr. Ouedraogo",
        institution="Xcept-Health",
        date="15 March 2026",
        description="Test description",
    )
    r.add_text("Intro paragraph.", title="Introduction")
    r.add_metrics({"Cases": 42, "Deaths": 3, "CFR": "7.1%"})
    r.add_divider()
    return r



# 1. EpiReport.__init__


class TestEpiReportInit:

    def test_default_title(self):
        r = EpiReport()
        assert r.title == "Rapport épidémiologique"

    def test_custom_title(self):
        r = EpiReport(title="My Report")
        assert r.title == "My Report"

    def test_author_none_by_default(self):
        r = EpiReport()
        assert r.author is None

    def test_institution_none_by_default(self):
        r = EpiReport()
        assert r.institution is None

    def test_date_set_automatically(self):
        r = EpiReport()
        # Auto date should be a non-empty string
        assert isinstance(r.date, str)
        assert len(r.date) > 0

    def test_custom_date(self):
        r = EpiReport(date="01 January 2025")
        assert r.date == "01 January 2025"

    def test_sections_empty_on_init(self):
        r = EpiReport()
        assert r.sections == []

    def test_description_none_by_default(self):
        r = EpiReport()
        assert r.description is None

    def test_all_fields_set(self):
        r = EpiReport(
            title="T", author="A",
            institution="I", date="D", description="Desc",
        )
        assert r.title == "T"
        assert r.author == "A"
        assert r.institution == "I"
        assert r.date == "D"
        assert r.description == "Desc"

    def test_repr(self):
        r = EpiReport(title="X")
        assert "X" in repr(r)
        assert "0 sections" in repr(r)



# 2. Section adders


class TestAddText:

    def test_adds_one_section(self, empty_report):
        empty_report.add_text("Hello")
        assert len(empty_report.sections) == 1

    def test_section_kind(self, empty_report):
        empty_report.add_text("Hello")
        assert empty_report.sections[0].kind == "text"

    def test_section_content(self, empty_report):
        empty_report.add_text("My text")
        assert empty_report.sections[0].content == "My text"

    def test_title_stored(self, empty_report):
        empty_report.add_text("Hello", title="Intro")
        assert empty_report.sections[0].title == "Intro"

    def test_title_none_by_default(self, empty_report):
        empty_report.add_text("Hello")
        assert empty_report.sections[0].title is None

    def test_level_default(self, empty_report):
        empty_report.add_text("Hello")
        assert empty_report.sections[0].level == 2

    def test_level_custom(self, empty_report):
        empty_report.add_text("Hello", level=3)
        assert empty_report.sections[0].level == 3

    def test_returns_self_for_chaining(self, empty_report):
        result = empty_report.add_text("Hello")
        assert result is empty_report

    def test_empty_string(self, empty_report):
        empty_report.add_text("")
        assert empty_report.sections[0].content == ""

    def test_multiline_text(self, empty_report):
        text = "Line 1\n\nLine 2"
        empty_report.add_text(text)
        assert empty_report.sections[0].content == text


class TestAddMetrics:

    def test_adds_one_section(self, empty_report):
        empty_report.add_metrics({"Cases": 42})
        assert len(empty_report.sections) == 1

    def test_section_kind(self, empty_report):
        empty_report.add_metrics({"Cases": 42})
        assert empty_report.sections[0].kind == "metrics"

    def test_content_preserved(self, empty_report):
        m = {"Cases": 42, "Deaths": 3, "CFR": "7.1%"}
        empty_report.add_metrics(m)
        assert empty_report.sections[0].content == m

    def test_default_title(self, empty_report):
        empty_report.add_metrics({"x": 1})
        assert empty_report.sections[0].title == "Indicateurs clés"

    def test_custom_title(self, empty_report):
        empty_report.add_metrics({"x": 1}, title="My Metrics")
        assert empty_report.sections[0].title == "My Metrics"

    def test_returns_self(self, empty_report):
        assert empty_report.add_metrics({"x": 1}) is empty_report

    def test_empty_dict(self, empty_report):
        empty_report.add_metrics({})
        assert empty_report.sections[0].content == {}

    def test_mixed_value_types(self, empty_report):
        m = {"int": 1, "float": 3.14, "str": "ok", "none": None}
        empty_report.add_metrics(m)
        assert empty_report.sections[0].content == m


class TestAddDivider:

    def test_adds_one_section(self, empty_report):
        empty_report.add_divider()
        assert len(empty_report.sections) == 1

    def test_section_kind(self, empty_report):
        empty_report.add_divider()
        assert empty_report.sections[0].kind == "divider"

    def test_content_is_none(self, empty_report):
        empty_report.add_divider()
        assert empty_report.sections[0].content is None

    def test_returns_self(self, empty_report):
        assert empty_report.add_divider() is empty_report

    def test_multiple_dividers(self, empty_report):
        empty_report.add_divider().add_divider()
        assert len(empty_report.sections) == 2


class TestAddFigure:

    def test_adds_one_section(self, empty_report):
        fig = MagicMock()
        fig.savefig = MagicMock()

        with patch("epitools.api.reporting._figure_to_html", return_value="<div>fig</div>"):
            empty_report.add_figure(fig, title="My Figure")

        assert len(empty_report.sections) == 1

    def test_section_kind(self, empty_report):
        with patch("epitools.api.reporting._figure_to_html", return_value="<div>fig</div>"):
            empty_report.add_figure(MagicMock(), title="Fig")
        assert empty_report.sections[0].kind == "figure"

    def test_title_and_caption_stored(self, empty_report):
        with patch("epitools.api.reporting._figure_to_html", return_value="<div>fig</div>"):
            empty_report.add_figure(MagicMock(), title="T", caption="C")
        sec = empty_report.sections[0]
        assert sec.title == "T"
        assert sec.caption == "C"

    def test_returns_self(self, empty_report):
        with patch("epitools.api.reporting._figure_to_html", return_value="<div>fig</div>"):
            result = empty_report.add_figure(MagicMock())
        assert result is empty_report


class TestChaining:

    def test_full_chain(self, empty_report):
        result = (
            empty_report
            .add_text("Hello")
            .add_metrics({"x": 1})
            .add_divider()
            .add_text("End")
        )
        assert result is empty_report
        assert len(empty_report.sections) == 4

    def test_section_order_preserved(self, empty_report):
        empty_report.add_text("A").add_metrics({"b": 2}).add_divider()
        kinds = [s.kind for s in empty_report.sections]
        assert kinds == ["text", "metrics", "divider"]



# 3. to_markdown()


class TestToMarkdown:

    def test_title_in_output(self, full_report):
        md = full_report.to_markdown()
        assert "Weekly Bulletin" in md

    def test_author_in_output(self, full_report):
        md = full_report.to_markdown()
        assert "Dr. Ouedraogo" in md

    def test_institution_in_output(self, full_report):
        md = full_report.to_markdown()
        assert "Xcept-Health" in md

    def test_date_in_output(self, full_report):
        md = full_report.to_markdown()
        assert "15 March 2026" in md

    def test_text_section_rendered(self, full_report):
        md = full_report.to_markdown()
        assert "Intro paragraph." in md

    def test_section_title_rendered(self, full_report):
        md = full_report.to_markdown()
        assert "Introduction" in md

    def test_metrics_table_rendered(self, full_report):
        md = full_report.to_markdown()
        assert "Cases" in md
        assert "42" in md

    def test_divider_rendered(self, full_report):
        md = full_report.to_markdown()
        assert "---" in md

    def test_no_author_omitted(self):
        r = EpiReport(title="T")
        r.add_text("body")
        md = r.to_markdown()
        assert "Auteur" not in md

    def test_no_institution_omitted(self):
        r = EpiReport(title="T")
        md = r.to_markdown()
        assert "Institution" not in md

    def test_figure_placeholder(self):
        r = EpiReport(title="T")
        with patch("epitools.api.reporting._figure_to_html", return_value="<div>fig</div>"):
            r.add_figure(MagicMock())
        md = r.to_markdown()
        assert "Figure" in md or "figure" in md

    def test_returns_string(self, empty_report):
        assert isinstance(empty_report.to_markdown(), str)

    def test_empty_report_is_valid(self):
        r = EpiReport(title="Empty")
        md = r.to_markdown()
        assert "Empty" in md

    def test_description_in_output(self):
        r = EpiReport(title="T", description="My desc")
        md = r.to_markdown()
        assert "My desc" in md



# 4. to_html()


class TestToHtml:

    def test_returns_string(self, empty_report):
        assert isinstance(empty_report.to_html(), str)

    def test_valid_html_structure(self, full_report):
        html = full_report.to_html()
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html

    def test_title_in_head(self, full_report):
        html = full_report.to_html()
        assert "Weekly Bulletin" in html

    def test_author_in_body(self, full_report):
        html = full_report.to_html()
        assert "Dr. Ouedraogo" in html

    def test_institution_in_body(self, full_report):
        html = full_report.to_html()
        assert "Xcept-Health" in html

    def test_text_section_in_body(self, full_report):
        html = full_report.to_html()
        assert "Intro paragraph." in html

    def test_metrics_table_present(self, full_report):
        html = full_report.to_html()
        assert "<table" in html
        assert "Cases" in html

    def test_divider_rendered_as_hr(self, full_report):
        html = full_report.to_html()
        assert "<hr>" in html

    def test_dark_light_toggle_present(self, full_report):
        html = full_report.to_html()
        assert "dark" in html or "theme" in html

    def test_xss_escaping_in_title(self):
        import re
        r = EpiReport(title="<script>alert('xss')</script>")
        html = r.to_html()
        # The <title> tag must be escaped  raw <script> must not appear there
        title_tag = re.search(r"<title>(.*?)</title>", html, re.DOTALL)
        assert title_tag is not None
        assert "<script>" not in title_tag.group(1)
        assert "&lt;script&gt;" in title_tag.group(1)

    def test_xss_escaping_in_text(self):
        r = EpiReport(title="T")
        r.add_text("<b>bold</b>")
        html = r.to_html()
        assert "<b>bold</b>" not in html
        assert "&lt;b&gt;" in html

    def test_xss_escaping_in_metrics_key(self):
        r = EpiReport(title="T")
        r.add_metrics({"<evil>": "value"})
        html = r.to_html()
        assert "<evil>" not in html

    def test_xss_escaping_in_author(self):
        r = EpiReport(title="T", author='"><img src=x onerror=alert(1)>')
        html = r.to_html()
        # Raw <img must not appear  it must be escaped
        assert "<img" not in html
        # onerror may appear as text inside &lt;img ... onerror=...&gt; which is safe
        # but must not appear as a live attribute
        assert 'onerror=' not in html.replace("&lt;img", "").replace("onerror=alert", "")
        assert "&lt;img" in html

    def test_section_heading_level(self):
        r = EpiReport(title="T")
        r.add_text("body", title="My Section", level=3)
        html = r.to_html()
        assert "<h3>" in html

    def test_caption_rendered(self):
        r = EpiReport(title="T")
        with patch("epitools.api.reporting._figure_to_html", return_value="<div>f</div>"):
            r.add_figure(MagicMock(), caption="My caption")
        html = r.to_html()
        assert "My caption" in html

    def test_empty_report_valid_html(self):
        r = EpiReport(title="Empty")
        html = r.to_html()
        assert "<!DOCTYPE html>" in html

    def test_utf8_content_preserved(self):
        r = EpiReport(title="T", author="Ariel Shadrac Ouédraogo")
        html = r.to_html()
        assert "Ouédraogo" in html



# 5. to_json()


class TestToJson:

    def test_returns_valid_json(self, full_report):
        raw = full_report.to_json()
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)

    def test_top_level_keys(self, full_report):
        parsed = json.loads(full_report.to_json())
        assert "title" in parsed
        assert "author" in parsed
        assert "institution" in parsed
        assert "date" in parsed
        assert "sections" in parsed

    def test_title_value(self, full_report):
        parsed = json.loads(full_report.to_json())
        assert parsed["title"] == "Weekly Bulletin – Week 12"

    def test_author_value(self, full_report):
        parsed = json.loads(full_report.to_json())
        assert parsed["author"] == "Dr. Ouedraogo"

    def test_sections_is_list(self, full_report):
        parsed = json.loads(full_report.to_json())
        assert isinstance(parsed["sections"], list)

    def test_section_count(self, full_report):
        parsed = json.loads(full_report.to_json())
        # text + metrics + divider = 3
        assert len(parsed["sections"]) == 3

    def test_text_section_schema(self, full_report):
        parsed = json.loads(full_report.to_json())
        text_sec = parsed["sections"][0]
        assert text_sec["kind"] == "text"
        assert "content" in text_sec

    def test_metrics_section_content(self, full_report):
        parsed = json.loads(full_report.to_json())
        metrics_sec = parsed["sections"][1]
        assert metrics_sec["kind"] == "metrics"
        assert isinstance(metrics_sec["content"], dict)
        assert "Cases" in metrics_sec["content"]

    def test_divider_section(self, full_report):
        parsed = json.loads(full_report.to_json())
        divider = parsed["sections"][2]
        assert divider["kind"] == "divider"

    def test_figure_omitted_in_json(self):
        r = EpiReport(title="T")
        with patch("epitools.api.reporting._figure_to_html", return_value="<div>f</div>"):
            r.add_figure(MagicMock(), title="Fig")
        parsed = json.loads(r.to_json())
        fig_sec = parsed["sections"][0]
        assert fig_sec["kind"] == "figure"
        assert "[figure" in str(fig_sec.get("content", "")).lower()

    def test_none_author_in_json(self):
        r = EpiReport(title="T")
        parsed = json.loads(r.to_json())
        assert parsed["author"] is None

    def test_utf8_in_json(self):
        r = EpiReport(title="Épidémiologie")
        raw = r.to_json()
        assert "Épidémiologie" in raw

    def test_indent_default(self, empty_report):
        raw = empty_report.to_json()
        # default indent=2 → should have newlines
        assert "\n" in raw



# 6. save_*  file I/O


class TestSaveHtml:

    def test_creates_file(self, full_report, tmp_path):
        out = tmp_path / "report.html"
        full_report.save_html(out)
        assert out.exists()

    def test_returns_path(self, full_report, tmp_path):
        out = tmp_path / "report.html"
        result = full_report.save_html(out)
        assert result == out

    def test_file_content_is_html(self, full_report, tmp_path):
        out = tmp_path / "report.html"
        full_report.save_html(out)
        content = out.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content

    def test_accepts_string_path(self, full_report, tmp_path):
        out = str(tmp_path / "report.html")
        result = full_report.save_html(out)
        assert Path(out).exists()

    def test_utf8_encoding(self, tmp_path):
        r = EpiReport(title="Épidémiologie", author="Ouédraogo")
        out = tmp_path / "report.html"
        r.save_html(out)
        content = out.read_text(encoding="utf-8")
        assert "Épidémiologie" in content


class TestSaveMarkdown:

    def test_creates_file(self, full_report, tmp_path):
        out = tmp_path / "report.md"
        full_report.save_markdown(out)
        assert out.exists()

    def test_returns_path(self, full_report, tmp_path):
        out = tmp_path / "report.md"
        result = full_report.save_markdown(out)
        assert result == out

    def test_file_content_is_markdown(self, full_report, tmp_path):
        out = tmp_path / "report.md"
        full_report.save_markdown(out)
        content = out.read_text(encoding="utf-8")
        assert content.startswith("#")

    def test_utf8_encoding(self, tmp_path):
        r = EpiReport(title="Méningite", author="Ariel")
        out = tmp_path / "report.md"
        r.save_markdown(out)
        content = out.read_text(encoding="utf-8")
        assert "Méningite" in content


class TestSaveJson:

    def test_creates_file(self, full_report, tmp_path):
        out = tmp_path / "report.json"
        full_report.save_json(out)
        assert out.exists()

    def test_returns_path(self, full_report, tmp_path):
        out = tmp_path / "report.json"
        result = full_report.save_json(out)
        assert result == out

    def test_file_is_valid_json(self, full_report, tmp_path):
        out = tmp_path / "report.json"
        full_report.save_json(out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_utf8_encoding(self, tmp_path):
        r = EpiReport(title="Données épidémiologiques")
        out = tmp_path / "report.json"
        r.save_json(out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["title"] == "Données épidémiologiques"



# 7. Helper functions


class TestFmt:

    def test_none_returns_empty(self):
        assert _fmt(None) == ""

    def test_int_formatted_with_commas(self):
        assert _fmt(1_000_000) == "1,000,000"

    def test_small_int(self):
        assert _fmt(42) == "42"

    def test_large_float_formatted(self):
        result = _fmt(12345.6)
        assert "12,345" in result

    def test_small_float_four_decimals(self):
        result = _fmt(0.1234)
        assert "0.1234" in result

    def test_string_passthrough(self):
        assert _fmt("7.1%") == "7.1%"

    def test_zero_int(self):
        assert _fmt(0) == "0"

    def test_zero_float(self):
        result = _fmt(0.0)
        assert "0" in result

    def test_negative_float(self):
        result = _fmt(-3.14)
        assert "-" in result


class TestEsc:

    def test_ampersand(self):
        assert _esc("a & b") == "a &amp; b"

    def test_less_than(self):
        assert _esc("<tag>") == "&lt;tag&gt;"

    def test_greater_than(self):
        assert _esc("x > y") == "x &gt; y"

    def test_double_quote(self):
        assert _esc('"quoted"') == "&quot;quoted&quot;"

    def test_no_special_chars(self):
        assert _esc("hello world") == "hello world"

    def test_combined(self):
        result = _esc('<a href="url">link & more</a>')
        assert "<" not in result
        assert ">" not in result
        assert '"' not in result
        assert "&amp;" in result

    def test_non_string_input(self):
        # Should coerce to string
        result = _esc(42)
        assert result == "42"

    def test_empty_string(self):
        assert _esc("") == ""



# 8. Factory functions  report_from_result & report_from_model

class TestReportFromResult:

    def _make_result(self, with_to_dict=True):
        result = MagicMock()
        result.__class__.__name__ = "MockResult"
        result.__repr__ = lambda self: "MockResult()"
        if with_to_dict:
            result.to_dict.return_value = {
                "r0": 2.5, "peak": 50000, "nested": {"a": 1}
            }
        else:
            del result.to_dict
        return result

    def test_returns_epireport(self):
        result = self._make_result()
        with patch("epitools.api.reporting._figure_to_html", return_value="<div>f</div>"):
            report = report_from_result(result)
        assert isinstance(report, EpiReport)

    def test_has_sections(self):
        result = self._make_result()
        with patch("epitools.api.reporting._figure_to_html", return_value="<div>f</div>"):
            report = report_from_result(result)
        assert len(report.sections) > 0

    def test_custom_title(self):
        result = self._make_result()
        with patch("epitools.api.reporting._figure_to_html", return_value="<div>f</div>"):
            report = report_from_result(result, title="My Title")
        assert report.title == "My Title"

    def test_custom_author(self):
        result = self._make_result()
        with patch("epitools.api.reporting._figure_to_html", return_value="<div>f</div>"):
            report = report_from_result(result, author="Dr. Test")
        assert report.author == "Dr. Test"

    def test_default_title_uses_class_name(self):
        result = self._make_result()
        with patch("epitools.api.reporting._figure_to_html", return_value="<div>f</div>"):
            report = report_from_result(result)
        assert "MockResult" in report.title


class TestReportFromModel:

    def _make_model_result(self):
        mr = MagicMock()
        mr.model_type = "SEIR"
        mr.r0 = 4.9
        mr.peak_infected = 7_331_552.0
        mr.peak_time = 120.0
        mr.final_size = 0.992
        mr.parameters = {
            "N": 22_100_000, "beta": 0.35,
            "sigma": 0.192, "gamma": 0.071,
        }
        import numpy as np
        mr.t = np.linspace(0, 365, 366)
        mr.compartments = {
            "S": np.ones(366), "E": np.ones(366),
            "I": np.ones(366), "R": np.ones(366),
        }
        mr.to_dataframe.return_value = __import__("pandas").DataFrame({
            "t": [0, 90, 180, 270, 365],
            "S": [22099989, 15000000, 5000000, 200000, 170927],
            "I": [1, 500000, 7000000, 100000, 1],
        })
        mr.plot.return_value = MagicMock()
        return mr

    def test_returns_epireport(self):
        mr = self._make_model_result()
        with patch("epitools.api.reporting._figure_to_html", return_value="<div>f</div>"):
            report = report_from_model(mr)
        assert isinstance(report, EpiReport)

    def test_model_type_in_title(self):
        mr = self._make_model_result()
        with patch("epitools.api.reporting._figure_to_html", return_value="<div>f</div>"):
            report = report_from_model(mr)
        assert "SEIR" in report.title

    def test_custom_title(self):
        mr = self._make_model_result()
        with patch("epitools.api.reporting._figure_to_html", return_value="<div>f</div>"):
            report = report_from_model(mr, title="Custom Title")
        assert report.title == "Custom Title"

    def test_author_and_institution_set(self):
        mr = self._make_model_result()
        with patch("epitools.api.reporting._figure_to_html", return_value="<div>f</div>"):
            report = report_from_model(
                mr, author="Dr. A", institution="Xcept-Health"
            )
        assert report.author == "Dr. A"
        assert report.institution == "Xcept-Health"

    def test_has_multiple_sections(self):
        mr = self._make_model_result()
        with patch("epitools.api.reporting._figure_to_html", return_value="<div>f</div>"):
            report = report_from_model(mr)
        assert len(report.sections) >= 3

    def test_r0_present_in_metrics(self):
        mr = self._make_model_result()
        with patch("epitools.api.reporting._figure_to_html", return_value="<div>f</div>"):
            report = report_from_model(mr)
        all_content = " ".join(
            str(s.content) for s in report.sections if s.kind == "metrics"
        )
        assert "R" in all_content or "r0" in all_content.lower()

    def test_html_is_valid(self):
        mr = self._make_model_result()
        with patch("epitools.api.reporting._figure_to_html", return_value="<div>f</div>"):
            report = report_from_model(mr)
        html = report.to_html()
        assert "<!DOCTYPE html>" in html

    def test_json_is_valid(self):
        mr = self._make_model_result()
        with patch("epitools.api.reporting._figure_to_html", return_value="<div>f</div>"):
            report = report_from_model(mr)
        data = json.loads(report.to_json())
        assert data["title"] is not None



# 9. Edge cases & error paths

class TestEdgeCases:

    def test_very_long_title(self):
        title = "A" * 1000
        r = EpiReport(title=title)
        html = r.to_html()
        assert title in html

    def test_unicode_title(self):
        r = EpiReport(title="épidémiologie ‒ 流行病学 ‒ epidemiología")
        html = r.to_html()
        assert "流行病学" in html

    def test_metrics_with_special_chars_in_key(self):
        r = EpiReport(title="T")
        r.add_metrics({"R₀": 4.9, "Taux d'attaque": "8.4/100k"})
        html = r.to_html()
        assert "R₀" in html

    def test_many_sections(self):
        r = EpiReport(title="T")
        for i in range(100):
            r.add_text(f"Section {i}", title=f"Title {i}")
        assert len(r.sections) == 100
        html = r.to_html()
        assert "Section 99" in html

    def test_save_html_overwrites_existing(self, tmp_path):
        out = tmp_path / "report.html"
        out.write_text("old content", encoding="utf-8")
        r = EpiReport(title="New")
        r.save_html(out)
        content = out.read_text(encoding="utf-8")
        assert "old content" not in content
        assert "New" in content

    def test_report_with_no_sections_saves(self, tmp_path):
        r = EpiReport(title="Empty")
        out = tmp_path / "empty.html"
        r.save_html(out)
        assert out.exists()

    def test_metrics_with_none_value(self):
        r = EpiReport(title="T")
        r.add_metrics({"key": None})
        html = r.to_html()
        assert "key" in html

    def test_add_text_with_html_in_content(self):
        import re
        r = EpiReport(title="T")
        r.add_text("<script>evil()</script>")
        html = r.to_html()
        # User content must be escaped; find paragraphs only (not template scripts)
        assert "&lt;script&gt;evil()&lt;/script&gt;" in html
        # The raw injected string must not appear literally in a <p> tag
        assert "<p><script>" not in html

    def test_repr_shows_section_count(self):
        r = EpiReport(title="T")
        r.add_text("a").add_text("b").add_text("c")
        assert "3 sections" in repr(r)