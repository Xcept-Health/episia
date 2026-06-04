"""
data/__init__.py - Episia data management layer.
"""

from .dataset import Dataset
from .io import (
    from_dict,
    from_pandas,
    read_csv,
    read_excel,
)
from .surveillance import (
    Alert,
    AlertEngine,
    SurveillanceDataset,
    aggregate_by,
    compute_attack_rate,
    endemic_channel,
    from_dhis2_csv,
)

__all__ = [
    "Dataset",
    "read_csv", "read_excel", "from_pandas", "from_dict",
    "SurveillanceDataset", "AlertEngine", "Alert",
    "from_dhis2_csv", "compute_attack_rate",
    "endemic_channel", "aggregate_by",
]
