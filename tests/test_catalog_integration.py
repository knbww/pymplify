import numpy as np
from pymplify_core import discover_adapters
from pymplify_tabular import scale
from pymplify_text import vectorize


def test_installed_adapters_are_discovered_and_match_direct_package_calls():
    catalog = discover_adapters(strict=True)
    assert {"text", "tabular"} <= {adapter.name for adapter in catalog.adapters}
    assert {"text", "tabular"} <= {adapter.name for adapter in catalog.for_library("sklearn")}
    documents = ["small language model", "simple machine learning"]
    vectors = catalog.run("text", "vectorize", documents, max_features=4)
    expected = vectorize(documents, max_features=4)
    np.testing.assert_allclose(vectors.matrix.toarray(), expected.matrix.toarray())
    assert vectors.transform(["language"]).model is vectors.model
    data = [[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]]
    scaled = catalog.run("tabular", "scale", data)
    np.testing.assert_allclose(scaled.data, scale(data).data)
    assert scaled.transform([[4.0, 40.0]]).model is scaled.model
