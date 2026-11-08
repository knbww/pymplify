"""Installed plugin factory. Importing it does not load scikit-learn."""

from pymplify_core import Adapter, Operation

from pymplify_tabular.scaling import scale


def get_adapter() -> Adapter:
    """Describe the tabular adapter without processing any data."""
    return Adapter(
        name="tabular",
        library="scikit-learn",
        aliases=("sklearn",),
        description="Numerical feature preprocessing with scikit-learn.",
        operations=(Operation("scale", scale, "Standardize features or reuse a fitted scaler."),),
    )
