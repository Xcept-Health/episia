API Module
==========

The API module provides the unified interface, result objects, and reporting tools for Episia.

This module contains three main components:

- **reporting**: Generate professional reports in HTML, Markdown, and JSON
- **results**: Unified result classes with consistent serialization and visualization
- **unified**: The main ``epi`` entry point for all Episia functionality

.. toctree::
   :maxdepth: 2
   :caption: API Submodules:

   reporting
   results
   unified

Examples
--------

Using the unified interface::

    from episia import epi

    # SEIR model
    model = epi.seir(N=1_000_000, I0=10, E0=50,
                      beta=0.35, sigma=1/5.2, gamma=1/14)
    result = model.run()

    # Generate report
    report = epi.report(result, title="SEIR Analysis")
    report.save_html("report.html")

Using result objects::

    from episia.api.results import AssociationResult

    rr = AssociationResult(
        measure="risk_ratio",
        estimate=2.667,
        ci=make_ci(1.514, 4.696)
    )
    print(rr.to_dict())

Using reporting directly::

    from episia.api.reporting import EpiReport

    report = EpiReport(
        title="Outbreak Report",
        author="Dr. Ouedraogo",
        institution="Xcept-Health"
    )
    report.add_metrics({"R0": 2.5, "Cases": 1500})
    report.save_html("outbreak.html")