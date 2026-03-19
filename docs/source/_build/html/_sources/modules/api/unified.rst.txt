unified Module
==============

Unified Episia interface - main entry point.

This module provides the :class:`EpisiaAPI` class and the :data:`epi` singleton,
which serves as the single entry point for all Episia functionality.

Class
-----

.. autoclass:: episia.api.unified.EpisiaAPI
   :members:
   :undoc-members:
   :show-inheritance:

Singleton
---------

.. autodata:: episia.api.unified.epi
   :annotation: = EpisiaAPI()

Usage Examples
--------------

Basic statistics::

    from episia import epi
    
    # Risk ratio
    rr = epi.risk_ratio(a=40, b=10, c=20, d=30)
    print(rr)
    
    # Confidence interval for a proportion
    prop = epi.proportion_ci(k=45, n=200, method="wilson")
    print(prop)

Epidemic models::

    # SEIR model
    model = epi.seir(
        N=1_000_000, I0=10, E0=50,
        beta=0.35, sigma=1/5.2, gamma=1/14
    )
    result = model.run()
    result.plot().show()

Data handling::

    # Read surveillance data
    ds = epi.read_csv("cases.csv", date_col="date", cases_col="cases")
    ds.epicurve().plot().show()

Reporting::

    # Generate report
    report = epi.report(result, title="SEIR Analysis")
    report.save_html("report.html")
    report.save_markdown("report.md")

Theming::

    # Change visualization theme
    epi.set_theme("dark")
    print(epi.get_available_themes())