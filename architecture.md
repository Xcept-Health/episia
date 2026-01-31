epitools/                                  # 📦 PACKAGE PRINCIPAL
│
├── 📄 __init__.py                        # Interface principale exportant `epi`
│
├── 📁 core/                              # 🧩 CŒUR TECHNIQUE
│   ├── __init__.py
│   ├── calculator.py                     # Calculateurs optimisés avec cache
│   ├── validator.py                      # Validation données et paramètres
│   ├── exceptions.py                     # EpiToolsError, ValidationError
│   ├── constants.py                      # Méthodes IC, seuils, constantes
│   └── utilities.py                      # Formateurs, helpers, décorateurs
│
├── 📁 stats/                             # 📊 STATISTIQUES ÉPIDÉMIOLOGIQUES
│   ├── __init__.py
│   ├── descriptive.py                    # IC proportions, moyennes, quantiles
│   ├── contingency.py                    # 🎯 CLASSE MAÎTRESSE Table2x2
│   ├── stratified.py                     # Mantel-Haenszel, Rothman
│   ├── samplesize.py                     # Calcul taille échantillon & puissance
│   ├── diagnostic.py                     # Sensibilité, spécificité, ROC, AUC
│   ├── regression.py                     # Régression logistique simple
│   └── time_series.py                    # Taux, incidence, agrégations temp.
│
├── 📁 models/                            # 🔬 MODÉLISATION COMPARTIMENTALE
│   ├── __init__.py
│   ├── base.py                           # CompartmentalModel (abstraite)
│   ├── sir.py                            # Modèle SIR
│   ├── seir.py                           # Modèle SEIR (Susceptible-Exposé-Infectieux-Rétabli)
│   ├── seird.py                          # SEIR avec Décès
│   ├── parameters.py                     # Gestion β, γ, σ, N, R₀, interventions
│   ├── solver.py                         # Solveurs ODE (solve_ivp)
│   ├── calibration.py                    # Ajustement aux données
│   ├── scenarios.py                      # Gestion multi-scénarios
│   └── visualization.py                  # Visualisations modèles
│
├── 📁 viz/                               # 🎨 SYSTÈME DE VISUALISATION
│   ├── __init__.py                       # API unifiée plot_*
│   │
│   ├── plotters/                         # 🖥️ ABSTRACTION MOTEURS
│   │   ├── __init__.py
│   │   ├── base_plotter.py               # Interface commune Plotter
│   │   ├── mpl_plotter.py                # Moteur Matplotlib (par défaut)
│   │   ├── plotly_plotter.py             # Moteur Plotly (interactif)
│   │   └── browser_plotter.py            # Export HTML navigateur
│   │
│   ├── themes/                           # 🎭 SYSTÈME THÈMES
│   │   ├── __init__.py
│   │   ├── registry.py                   # Gestionnaire thèmes
│   │   ├── scientific.mplstyle           # Style publication
│   │   ├── minimal.mplstyle              # Style épuré
│   │   ├── dark.mplstyle                 # Style sombre
│   │   └── colorblind.mplstyle           # Accessibilité
│   │
│   ├── curves.py                         # Courbes épidémiques, tendances
│   ├── roc.py                            # Courbes ROC, AUC
│   ├── forest.py                         # Forest plots
│   ├── contingency_plot.py               # Visualisations tables 2×2
│   ├── model_plots.py                    # Visualisations modèles
│   └── utils.py                          # Outils graphiques communs
│
├── 📁 data/                              # 💾 GESTION DONNÉES
│   ├── __init__.py
│   ├── dataset.py                        # 🎯 CLASSE MAÎTRESSE Dataset
│   ├── io.py                             # read_csv, from_pandas, from_dict
│   ├── transformers.py                   # Nettoyage, filtrage, agrégation
│   ├── types.py                          # Optimisation types pandas
│   └── surveillance.py                   # Formats surveillance spécifiques
│
├── 📁 api/                               # 🚀 INTERFACE PUBLIQUE
│   ├── __init__.py
│   ├── unified.py                        # Point d'entrée `epi` (singleton)
│   ├── results.py                        # Classes résultats riches (RRResult, etc.)
│   └── reporting.py                      # Génération rapports
│
├── 📁 simulation/                        # 🎲 SIMULATIONS ÉPIDÉMIQUES (optionnel)
│   ├── __init__.py
│   ├── outbreak.py                       # Simulation foyers épidémiques
│   ├── networks.py                       # Modélisation réseaux sociaux
│   └── spatial.py                        # Diffusion spatiale
│
└── 📁 compatibility/                     # 🔗 COMPATIBILITÉ
    ├── __init__.py
    ├── openepi.py                        # Conversion OpenEpi → EpiTools
    ├── repitools.py                      # Compatibilité R-epitools
    └── common_formats.py                 // Formats données standard