"""
EpiTools - Epidemiology Toolbox for Python, based on OpenEpi

"""

__version__ = "0.1.0"
__author__ = "Ariel Shadrac Ouedrago"
__email__ = "arielshadrac@gmail.com"
__organization__ = "Xcept-Health"
__copyright__ = "Copyright (c) 2024 Votre Nom & Xcept-Health"
__license__ = "MIT"

# Export principal : l'objet API unifié
from .api.unified import epi

# Export pour utilisateurs avancés
from .data.io import read_csv, from_pandas
from .stats.contingency import risk_ratio, odds_ratio

__all__ = ['epi', 'risk_ratio', 'odds_ratio', 'read_csv']