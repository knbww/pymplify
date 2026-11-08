# pymplify-tabular

Standardize numerical features in one call through **scikit-learn**. Python 3.10+,
MIT. Depends on `pymplify-core>=0.2.0,<0.3` and `scikit-learn>=1.4.2,<2`.

From the repository root:

```bash
python -m pip install -e ./packages/pymplify-core -e ./packages/pymplify-tabular
```

```python
from pymplify_tabular import scale

training = scale([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]])
queries = training.transform([[4.0, 40.0]])
print(training.data)
assert queries.model is training.model
```

`scale(data, *, model=None, **options)` returns `ScaledData` with native transformed
`data` and the fitted `StandardScaler` as `model`. Pass constructor options such as
`with_mean=False`, or supply an existing fitted model without additional options.
Use `training.transform(new_data)` to reuse training statistics without refitting.

Input must be a two-dimensional numeric dataset accepted by `StandardScaler`.
Validation and NaN handling follow upstream behavior. Sparse inputs require
`with_mean=False`; the adapter never densifies them automatically. Scaling does
not impute missing values, encode categories, or remove outliers.

The installed package advertises the `tabular` adapter with a `scale` operation
in the `pymplify.adapters` entry point group. Its library is `scikit-learn`, with
the explicit alias `sklearn`. Discovering it does not load the ML backend.

Constructor errors become `ConfigurationError`; operation errors become
`BackendError` with the original exception in `__cause__`.

Upstream reference:
[StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html).
