"""
models/__init__.py - EpiTools compartmental epidemic models.

Quick start::

    from epitools.models import SIRModel, SEIRModel, SEIRDModel
    from epitools.models.parameters import SIRParameters, SEIRParameters, SEIRDParameters
    from epitools.models.scenarios import ScenarioRunner, ScenarioSet
    from epitools.models.calibration import ModelCalibrator

    # Run a basic SIR model
    params = SIRParameters(N=1_000_000, I0=10, beta=0.3, gamma=0.1)
    result = SIRModel(params).run()
    print(result)
    result.plot().show()

    # Multi-scenario comparison
    from epitools.models.parameters import ScenarioSet
    scenarios = ScenarioSet([
        ("R0=1.5", SIRParameters(N=1_000_000, I0=10, beta=0.15, gamma=0.1)),
        ("R0=3.0", SIRParameters(N=1_000_000, I0=10, beta=0.30, gamma=0.1)),
    ])
    runner  = ScenarioRunner(SIRModel)
    results = runner.run(scenarios)
    results.plot(compartment="I").show()
"""

from .base   import CompartmentalModel
from .sir    import SIRModel
from .seir   import SEIRModel
from .seird  import SEIRDModel

from .parameters import (
    ModelParameters,
    SIRParameters,
    SEIRParameters,
    SEIRDParameters,
    ScenarioSet,
)

from .solver import (
    solve_model,
    estimate_herd_immunity,
    doubling_time,
)

from .scenarios import (
    ScenarioRunner,
    ScenarioResults,
)

from .calibration import (
    ModelCalibrator,
    CalibrationResult,
)

__all__ = [
    # Models
    "CompartmentalModel",
    "SIRModel",
    "SEIRModel",
    "SEIRDModel",
    # Parameters
    "ModelParameters",
    "SIRParameters",
    "SEIRParameters",
    "SEIRDParameters",
    "ScenarioSet",
    # Solver utilities
    "solve_model",
    "estimate_herd_immunity",
    "doubling_time",
    # Scenarios
    "ScenarioRunner",
    "ScenarioResults",
    # Calibration
    "ModelCalibrator",
    "CalibrationResult",
]

from .sensitivity import (
    SensitivityAnalysis,
    SensitivityResult,
)