"""
data/__init__.py - EpiTools data management layer.
"""

from .dataset import Dataset
from .io import (
    read_csv, read_excel, from_pandas, from_dict,
)
from .surveillance import (
    SurveillanceDataset,
    AlertEngine,
    Alert,
    from_dhis2_csv,
    compute_attack_rate,
    endemic_channel,
    aggregate_by,
)

__all__ = [
    "Dataset",
    "read_csv", "read_excel", "from_pandas", "from_dict",
    "SurveillanceDataset", "AlertEngine", "Alert",
    "from_dhis2_csv", "compute_attack_rate",
    "endemic_channel", "aggregate_by",
]