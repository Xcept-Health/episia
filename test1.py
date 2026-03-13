from models import SEIRModel
from models.parameters import SEIRParameters
from viz.plotters import AnimationConfig, PlotConfig

params = SEIRParameters(N=1_000_000, I0=1, E0=10,
                        beta=0.35, sigma=1/5.2, gamma=1/14)
result = SEIRModel(params).run()

# Animation Plotly — slider + play/pause intégré
result.plot(
    backend="plotly",
    animate=True,
    config=PlotConfig(title="SEIR — COVID-like", theme="scientific")
)