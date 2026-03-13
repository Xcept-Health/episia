from epitools.models import SensitivityAnalysis, SEIRModel
from epitools.models.parameters import SEIRParameters

sa = SensitivityAnalysis(
    model_class=SEIRModel,
    param_class=SEIRParameters,
    fixed=dict(N=1_000_000, I0=10, E0=50, t_span=(0, 365)),
    distributions={
        "beta":  ("uniform",    0.25, 0.50),
        "sigma": ("normal",     1/5.2, 0.02),
        "gamma": ("triangular", 1/21, 1/14, 1/7),
    },
    n_samples=500,
    seed=42,
)

result = sa.run()
result.plot("I").show()                          # enveloppe percentile
result.plot_metric_distribution("r0").show()     # histogramme R₀
result.to_dataframe()                            # une ligne par run
print(result.summary())                          # stats descriptives
