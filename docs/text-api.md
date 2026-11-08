# Text vectorization

```python
from pymplify_text import TextVectors, vectorize
```

## `vectorize(documents, *, model=None, **options) -> TextVectors`

| Argument | Behavior |
| --- | --- |
| `documents` | A non-empty ordered iterable of non-empty strings; finite generators are supported |
| `model=None` | Create and fit a `TfidfVectorizer` on the supplied corpus |
| `model=<fitted TfidfVectorizer>` | Call only `transform`, without refitting |
| `**options` | Upstream constructor parameters; allowed only without `model` |

Input is materialized into a list once. This API is not suitable for infinite
streams or corpora that do not fit into memory. A string instead of an iterable
of documents, bytes, dictionaries, sets, empty corpora, and empty elements are
rejected before the backend is called.

`TextVectors.matrix` is a sparse matrix with shape `(number of documents, number of features)`.
`TextVectors.model` is the original fitted model. The container holds fixed field
references, but the model and matrix remain mutable upstream objects.
`TextVectors.transform(documents)` returns a new container using the same model.

```python
training = vectorize(["small model", "large model"], ngram_range=(1, 2))
test = training.transform(["small model", "unknown"])
assert test.matrix.shape[1] == training.matrix.shape[1]
assert test.matrix[1].nnz == 0
```

For ML evaluation, split the data first: fit the vocabulary on the training set,
then call `transform` for validation and test sets. Vectorizing the test set
independently creates a different vocabulary.

By default, scikit-learn lowercases text and uses words of at least two characters.
A corpus containing only punctuation or single-character words can produce an
empty vocabulary; the package preserves the reason in `BackendError.__cause__`.
Supported options include `analyzer`, `token_pattern`, `stop_words`, `ngram_range`,
`max_features`, and other original constructor parameters.

This is TF-IDF, not a neural semantic model. Automatic language selection,
translation, stemming, and task-quality-based feature selection are not performed.

Original API reference:
[TfidfVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html).
