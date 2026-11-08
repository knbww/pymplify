import numpy as np
import pytest
from pymplify_core import BackendError, ConfigurationError
from pymplify_tabular import ScaledData, scale
from scipy.sparse import csr_matrix, issparse
from sklearn.exceptions import NotFittedError
from sklearn.preprocessing import StandardScaler

DATA = [[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]]


def test_scaling_matches_native_sklearn_and_keeps_the_model():
    native = StandardScaler()
    result = scale(DATA)
    assert isinstance(result, ScaledData)
    assert isinstance(result.model, StandardScaler)
    np.testing.assert_allclose(result.data, native.fit_transform(DATA))
    np.testing.assert_allclose(result.model.mean_, native.mean_)
    np.testing.assert_allclose(result.data.mean(axis=0), [0, 0], atol=1e-12)


def test_new_samples_reuse_training_statistics():
    training = scale(DATA)
    mean = training.model.mean_.copy()
    queries = training.transform([[4.0, 40.0]])
    assert queries.model is training.model
    np.testing.assert_allclose(queries.data, training.model.transform([[4.0, 40.0]]))
    np.testing.assert_allclose(training.model.mean_, mean)


def test_existing_native_model_and_constructor_options_are_supported():
    model = StandardScaler(with_std=False).fit(DATA)
    reused = scale(DATA, model=model)
    assert reused.model is model
    np.testing.assert_allclose(reused.data, model.transform(DATA))
    result = scale(DATA, with_mean=False)
    np.testing.assert_allclose(result.data, StandardScaler(with_mean=False).fit_transform(DATA))


def test_sparse_input_stays_sparse_when_centering_is_disabled():
    source = csr_matrix(DATA)
    result = scale(source, with_mean=False)
    assert issparse(result.data)
    np.testing.assert_allclose(
        result.data.toarray(), StandardScaler(with_mean=False).fit_transform(source).toarray()
    )


def test_sparse_centering_is_rejected_instead_of_silently_densifying():
    with pytest.raises(BackendError, match="sparse"):
        scale(csr_matrix(DATA))


def test_nan_and_constant_features_preserve_upstream_behavior():
    source = [[1.0, np.nan], [1.0, 2.0], [1.0, 4.0]]
    result = scale(source)
    np.testing.assert_allclose(result.data, StandardScaler().fit_transform(source), equal_nan=True)
    np.testing.assert_allclose(result.data[:, 0], [0, 0, 0])


@pytest.mark.parametrize("source", [[], [1, 2, 3], [["text"]], [[float("inf")]], None])
def test_invalid_numeric_input_preserves_original_backend_error(source):
    with pytest.raises(BackendError, match="Feature scaling failed") as caught:
        scale(source)
    assert isinstance(caught.value.__cause__, (TypeError, ValueError))


def test_invalid_options_and_models_have_actionable_errors():
    with pytest.raises(ConfigurationError, match="Invalid scaler options") as caught:
        scale(DATA, nonexistent=True)
    assert isinstance(caught.value.__cause__, TypeError)
    with pytest.raises(ConfigurationError, match="transform method"):
        scale(DATA, model=object())
    with pytest.raises(ConfigurationError, match="either a fitted model or scaler options"):
        scale(DATA, model=StandardScaler().fit(DATA), with_mean=False)


def test_unfitted_model_and_wrong_feature_count_are_reported():
    with pytest.raises(BackendError, match="Feature transformation failed") as caught:
        scale(DATA, model=StandardScaler())
    assert isinstance(caught.value.__cause__, NotFittedError)
    with pytest.raises(BackendError, match="Feature transformation failed"):
        scale([[1.0]], model=StandardScaler().fit(DATA))
