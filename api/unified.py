class EpiToolsAPI:
    """Interface unifiée d'EpiTools (singleton)."""
    
    # Calculs directs
    from ..stats.contingency import risk_ratio, odds_ratio
    from ..stats.descriptive import proportion_ci, mean_ci
    from ..stats.samplesize import sample_size_risk_ratio
    from ..stats.diagnostic import sensitivity_specificity
    
    # Modélisation
    from ..models.seir import SEIRModel
    from ..models.sir import SIRModel
    
    # Visualisations
    from ..viz.curves import plot_epicurve, plot_trend
    from ..viz.roc import plot_roc
    from ..viz.forest import plot_forest
    from ..models.visualization import plot_seir_standard
    
    # Gestion données
    from ..data.io import read_csv, from_pandas, from_dict
    
    # Configuration
    from ..viz.themes.registry import set_theme, get_available_themes
    
    def __repr__(self):
        return "EpiTools API - Use epi.function()"

# Instance unique exportée
epi = EpiToolsAPI()