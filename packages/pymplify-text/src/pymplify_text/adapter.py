"""Installed plugin factory. Importing it does not load scikit-learn."""

from pymplify_core import Adapter, Operation

from pymplify_text.vectorization import vectorize


def get_adapter() -> Adapter:
    """Describe the text adapter without running any text processing."""
    return Adapter(
        name="text",
        library="scikit-learn",
        aliases=("sklearn",),
        description="Text features with native scikit-learn models.",
        operations=(Operation("vectorize", vectorize, "Fit TF-IDF or reuse a fitted vocabulary."),),
    )
