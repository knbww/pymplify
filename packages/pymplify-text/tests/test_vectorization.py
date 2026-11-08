import numpy as np
import pytest
from pymplify_core import BackendError, ConfigurationError
from pymplify_text import TextVectors, vectorize
from scipy.sparse import issparse
from sklearn.exceptions import NotFittedError
from sklearn.feature_extraction.text import TfidfVectorizer

DOCUMENTS = ["Python makes machine learning simpler", "Machine learning uses data"]


def test_default_output_matches_native_sklearn_and_stays_sparse():
    expected_model = TfidfVectorizer()
    expected = expected_model.fit_transform(DOCUMENTS)
    result = vectorize(DOCUMENTS)

    assert isinstance(result, TextVectors)
    assert isinstance(result.model, TfidfVectorizer)
    assert issparse(result.matrix)
    np.testing.assert_allclose(result.matrix.toarray(), expected.toarray())
    np.testing.assert_array_equal(
        result.model.get_feature_names_out(), expected_model.get_feature_names_out()
    )


def test_options_are_passed_to_the_original_vectorizer():
    options = {"ngram_range": (1, 2), "max_features": 6, "binary": True, "norm": None}
    expected = TfidfVectorizer(**options).fit_transform(DOCUMENTS)
    result = vectorize(DOCUMENTS, **options)
    np.testing.assert_allclose(result.matrix.toarray(), expected.toarray())
    assert result.model.get_params()["ngram_range"] == (1, 2)


def test_new_documents_share_training_vocabulary_without_refitting():
    training = vectorize(DOCUMENTS)
    vocabulary = dict(training.model.vocabulary_)
    original_matrix = training.matrix.copy()
    queries = training.transform(["python data", "unseenword"])

    assert queries.model is training.model
    assert queries.matrix.shape == (2, training.matrix.shape[1])
    assert queries.matrix[1].nnz == 0
    assert training.model.vocabulary_ == vocabulary
    np.testing.assert_allclose(training.matrix.toarray(), original_matrix.toarray())
    np.testing.assert_allclose(
        queries.matrix.toarray(), training.model.transform(["python data", "unseenword"]).toarray()
    )


def test_existing_sklearn_model_is_reused_by_identity():
    model = TfidfVectorizer().fit(DOCUMENTS)
    result = vectorize(["data"], model=model)
    assert result.model is model
    np.testing.assert_allclose(result.matrix.toarray(), model.transform(["data"]).toarray())


def test_consumes_a_finite_generator_once():
    result = vectorize(document for document in DOCUMENTS)
    assert result.matrix.shape[0] == len(DOCUMENTS)


def test_handles_unicode_without_english_specific_defaults():
    result = vectorize(["модель упрощает обучение", "обучение использует данные"])
    assert "обучение" in result.model.vocabulary_
    assert result.matrix.shape[0] == 2


@pytest.mark.parametrize(
    "documents",
    [None, 42, "one document", b"bytes", [], iter([]), {}, {"text"}, [""], ["  "], [1]],
)
def test_rejects_ambiguous_or_invalid_documents_with_actionable_errors(documents):
    with pytest.raises(ConfigurationError, match="documents"):
        vectorize(documents)


def test_points_to_invalid_document_index():
    with pytest.raises(ConfigurationError, match=r"documents\[1\]"):
        vectorize(["valid text", None])


def test_rejects_options_when_reusing_a_model():
    model = TfidfVectorizer().fit(DOCUMENTS)
    with pytest.raises(ConfigurationError, match="either a fitted model or vectorizer options"):
        vectorize(DOCUMENTS, model=model, max_features=10)


def test_rejects_invalid_model_before_backend_execution():
    with pytest.raises(ConfigurationError, match="transform method"):
        vectorize(DOCUMENTS, model=object())


def test_unknown_options_preserve_original_exception():
    with pytest.raises(ConfigurationError, match="Invalid vectorizer options") as caught:
        vectorize(DOCUMENTS, nonexistent_option=True)
    assert isinstance(caught.value.__cause__, TypeError)


@pytest.mark.parametrize("options", [{"max_features": -1}, {"ngram_range": (2, 1)}])
def test_backend_parameter_validation_preserves_original_exception(options):
    with pytest.raises(BackendError, match="Text vectorization failed") as caught:
        vectorize(DOCUMENTS, **options)
    assert isinstance(caught.value.__cause__, ValueError)


def test_corpus_without_usable_tokens_reports_backend_reason():
    with pytest.raises(BackendError, match="empty vocabulary") as caught:
        vectorize(["! ?", "..."])
    assert isinstance(caught.value.__cause__, ValueError)


def test_unfitted_model_reports_the_original_not_fitted_error():
    with pytest.raises(BackendError, match="Text transformation failed") as caught:
        vectorize(DOCUMENTS, model=TfidfVectorizer())
    assert isinstance(caught.value.__cause__, NotFittedError)
