"""
EpiTools - Epidemiology Toolbox for Python
Based on OpenEpi algorithms, extended for the African public health context.

Quick start::

    from epitools import epi

    # Modèle SEIR
    model  = epi.seir(N=1_000_000, I0=10, E0=50, beta=0.35,
                      sigma=1/5.2, gamma=1/14)
    result = model.run()
    result.plot().show()

    # Stats
    rr = epi.risk_ratio(a=40, b=10, c=20, d=30)
    print(rr)

    # Rapport
    report = epi.report(result, title="SEIR Burkina Faso 2024")
    report.save_html("rapport.html")
"""

__version__      = "0.1.0"
__author__       = "Fildouindé Ariel Shadrac Ouedraogo"
__email__        = "arielshadrac@gmail.com"
__organization__ = "Xcept-Health"
__license__      = "MIT"

from .api.unified import epi, EpiToolsAPI

__all__ = ["epi", "EpiToolsAPI", "__version__"]