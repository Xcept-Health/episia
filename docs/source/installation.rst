Installation
============

Standard Install
----------------

.. code-block:: bash

    pip install episia

Development Install
-------------------

.. code-block:: bash

    git clone https://github.com/Xcept-Health/episia.git
    cd episia
    pip install -e .

Optional Dependencies
---------------------

.. code-block:: bash

    # Full install with all extras
    pip install episia[full]

    # For Jupyter notebooks
    pip install episia[jupyter]

    # For PNG/SVG/PDF export (requires kaleido)
    pip install episia[export]

    # For DHIS2 integration
    pip install episia[dhis2]

    # For development
    pip install episia[dev]

Requirements
------------

- Python 3.9+
- numpy
- scipy
- pandas
- plotly
- matplotlib

Verify Installation
-------------------

.. code-block:: python

    from episia import epi
    print(epi)
    print(f"Episia version: {epi.__version__}")