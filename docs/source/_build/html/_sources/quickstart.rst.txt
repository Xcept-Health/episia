Quick Start
===========

Epidemic Model
--------------

.. code-block:: python

    from episia import epi

    # Run SEIR model
    model = epi.seir(
        N=1_000_000,
        I0=10,
        E0=50,
        beta=0.35,
        sigma=1/5.2,
        gamma=1/14
    )
    result = model.run()
    print(result)

    # Plot results
    result.plot().show()

Biostatistics
-------------

.. code-block:: python

    from episia import epi

    # Calculate risk ratio
    rr = epi.risk_ratio(a=40, b=10, c=20, d=30)
    print(rr)
    # Output: Risk Ratio: 2.667 (1.514-4.696)

    # Confidence interval for proportion
    prop = epi.proportion_ci(k=45, n=100)
    print(prop)
    # Output: Proportion: 0.4500 (0.354-0.549)

    # Diagnostic test evaluation
    diag = epi.diagnostic_test_2x2(tp=80, fp=20, fn=10, tn=90)
    print(f"Sensitivity: {diag.sensitivity:.3f}")
    print(f"Specificity: {diag.specificity:.3f}")

DHIS2 Integration
-----------------

.. code-block:: python

    from episia.dhis2 import DHIS2Client

    # Connect to DHIS2 demo instance
    client = DHIS2Client(
        url      = "https://play.dhis2.org/40.2.2",
        username = "admin",
        password = "district",
    )

    # Fetch surveillance data
    ds = client.to_dataset(
        data_element = "FTRrcoaog83",  # Malaria cases
        period       = "LAST_52_WEEKS",
        org_unit     = "ImspTQPwCqd",   # Sierra Leone
    )

    print(f"Loaded {ds.total_cases} cases")
    print(f"Date range: {ds.date_range}")

    # Generate epidemic curve
    ds.to_timeseries_result().plot().show()

Reporting
---------

.. code-block:: python

    from episia import epi

    # Generate report from model result
    report = epi.report(
        result,
        title="SEIR Model - Burkina Faso 2024",
        author="Dr. Ouedraogo"
    )

    # Export in multiple formats
    report.save_html("report.html")
    report.save_markdown("report.md")
    report.save_json("report.json")

More Examples
-------------

See the `Examples directory <https://github.com/Xcept-Health/episia/tree/main/examples>`_ for more detailed examples.