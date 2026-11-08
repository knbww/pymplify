"""A thin adapter that preserves scikit-learn's model and sparse output."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Set
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pymplify_core import BackendError, ConfigurationError, require_dependency

if TYPE_CHECKING:
    from scipy.sparse import csr_matrix
    from sklearn.feature_extraction.text import TfidfVectorizer


@dataclass(frozen=True)
class TextVectors:
    """Native sparse matrix and fitted model sharing one feature space.

    The container is immutable; the underlying scikit-learn objects remain
    accessible and mutable. Changing the model can invalidate this matrix's
    vocabulary, so use a separate model when fitting a new corpus.
    """

    matrix: csr_matrix
    model: TfidfVectorizer

    def transform(self, documents: Iterable[str]) -> TextVectors:
        """Encode new documents with the existing vocabulary, without refitting."""
        return vectorize(documents, model=self.model)


def _documents(documents: Iterable[str]) -> list[str]:
    if isinstance(documents, (str, bytes, Mapping, Set)):
        raise ConfigurationError("documents must be an ordered iterable of strings, e.g. ['text'].")
    try:
        values = list(documents)
    except TypeError as exc:
        raise ConfigurationError("documents must be an ordered iterable of strings.") from exc
    if not values:
        raise ConfigurationError("documents must contain at least one string.")
    for index, value in enumerate(values):
        if not isinstance(value, str) or not value.strip():
            raise ConfigurationError(f"documents[{index}] must be a non-empty string.")
    return values


def vectorize(
    documents: Iterable[str],
    *,
    model: TfidfVectorizer | None = None,
    **options: Any,
) -> TextVectors:
    """Fit TF-IDF in one call, or transform with an existing fitted model.

    Extra keyword arguments pass directly to ``TfidfVectorizer``. When ``model``
    is provided it must already be fitted, and options cannot be supplied.
    Input is materialized once, so finite generators are supported. Results stay
    sparse; no models are downloaded and input is never sent to a service.
    """
    values = _documents(documents)
    if model is not None:
        if options:
            raise ConfigurationError("Pass either a fitted model or vectorizer options, not both.")
        if not callable(getattr(model, "transform", None)):
            raise ConfigurationError("model must be a fitted vectorizer with a transform method.")
        try:
            matrix = model.transform(values)
        except (TypeError, ValueError) as exc:
            raise BackendError(f"Text transformation failed: {exc}") from exc
        return TextVectors(matrix=matrix, model=model)

    backend = require_dependency(
        "sklearn.feature_extraction.text", install="scikit-learn>=1.4.2,<2"
    )
    try:
        fitted_model = backend.TfidfVectorizer(**options)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(f"Invalid vectorizer options: {exc}") from exc
    try:
        matrix = fitted_model.fit_transform(values)
    except (TypeError, ValueError) as exc:
        raise BackendError(f"Text vectorization failed: {exc}") from exc
    return TextVectors(matrix=matrix, model=fitted_model)
