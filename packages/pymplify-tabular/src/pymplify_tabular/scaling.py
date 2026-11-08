"""A thin adapter over StandardScaler with training-state reuse."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pymplify_core import BackendError, ConfigurationError, require_dependency

if TYPE_CHECKING:
    from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class ScaledData:
    """Native transformed data and the fitted upstream scaler.

    The references are fixed; the underlying data and model remain mutable.
    Changing the model can invalidate the relationship to previously scaled data.
    """

    data: Any
    model: StandardScaler

    def transform(self, data: Any) -> ScaledData:
        """Transform new samples using training statistics without refitting."""
        return scale(data, model=self.model)


def scale(data: Any, *, model: StandardScaler | None = None, **options: Any) -> ScaledData:
    """Fit StandardScaler in one call, or transform with an existing fitted model.

    ``data`` must be a two-dimensional numeric input accepted by StandardScaler.
    Options are passed to its constructor. Sparse inputs require ``with_mean=False``;
    the adapter never densifies them automatically. Native input validation and
    NaN handling are delegated to scikit-learn.
    """
    if model is not None:
        if options:
            raise ConfigurationError("Pass either a fitted model or scaler options, not both.")
        if not callable(getattr(model, "transform", None)):
            raise ConfigurationError("model must be a fitted scaler with a transform method.")
        try:
            transformed = model.transform(data)
        except (TypeError, ValueError) as exc:
            raise BackendError(f"Feature transformation failed: {exc}") from exc
        return ScaledData(data=transformed, model=model)

    backend = require_dependency("sklearn.preprocessing", install="scikit-learn>=1.4.2,<2")
    try:
        fitted_model = backend.StandardScaler(**options)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(f"Invalid scaler options: {exc}") from exc
    try:
        transformed = fitted_model.fit_transform(data)
    except (TypeError, ValueError) as exc:
        raise BackendError(f"Feature scaling failed: {exc}") from exc
    return ScaledData(data=transformed, model=fitted_model)
