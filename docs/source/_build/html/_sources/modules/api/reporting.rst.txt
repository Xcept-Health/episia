reporting Module
================

Report generation for Episia analyses.

This module provides classes and functions for generating structured
epidemiological reports in multiple formats (Markdown, HTML, JSON).

Classes
-------

.. autoclass:: episia.api.reporting.EpiReport
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.api.reporting.ReportSection
   :members:
   :undoc-members:
   :show-inheritance:

Functions
---------

.. autofunction:: episia.api.reporting.report_from_result
.. autofunction:: episia.api.reporting.report_from_model

Examples
--------

Basic report creation::

    from episia.api.reporting import EpiReport
    
    report = EpiReport(
        title="COVID-19 Analysis",
        author="Dr. Ouedraogo",
        institution="Xcept-Health"
    )
    
    report.add_text("This is an introduction...", title="Introduction")
    report.add_metrics({"R0": 2.5, "Cases": 1500})
    report.save_html("report.html")
    report.save_markdown("report.md")