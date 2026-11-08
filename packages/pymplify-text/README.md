# pymplify-text

Text vectorization in one call through **scikit-learn**. Part of the Pymplify
ecosystem. Python 3.10+, MIT. Depends on `pymplify-core>=0.1.0,<0.2` and
`scikit-learn>=1.4.2,<2`.

Run from the repository root:

```bash
python -m pip install -e ./packages/pymplify-core -e ./packages/pymplify-text
```

```python
from pymplify_text import vectorize

training = vectorize(["small language model", "simple machine learning"])
queries = training.transform(["language learning"])

print(training.matrix.shape)
print(queries.matrix.shape)
print(training.model.get_feature_names_out())
```

`vectorize(documents, *, model=None, **options)` returns `TextVectors`:

- `matrix`: a native SciPy sparse feature matrix;
- `model`: a fitted `sklearn.feature_extraction.text.TfidfVectorizer`;
- `transform(documents)`: a new `TextVectors` using the same model without fitting.

Without `model`, `**options` are passed to the `TfidfVectorizer` constructor.
With `model`, only `transform` is called; additional options are not allowed.
Input must be an ordered iterable of non-empty strings, including finite generators.
Empty strings and ambiguous inputs are rejected with `ConfigurationError`.

The default method is TF-IDF, with no network requests or neural models.
Unknown words are ignored during `transform`. Use the same model for training and
queries: independent `vectorize` calls create independent vocabularies.
Do not change the fitted model's vocabulary if you need to preserve its mapping
to columns in an existing matrix. Converting a large matrix with `.toarray()`
requires memory; the package keeps results sparse.

Operation failures are wrapped in `BackendError`, with the original exception in
`__cause__`. After installation, get the version with
`importlib.metadata.version("pymplify-text")`.

Upstream documentation:
[TfidfVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html).
