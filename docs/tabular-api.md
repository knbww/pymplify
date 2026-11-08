# Tabular preprocessing

```python
from pymplify_tabular import ScaledData, scale
```

## `scale(data, *, model=None, **options) -> ScaledData`

| Argument | Behavior |
| --- | --- |
| `data` | Two-dimensional numeric input accepted by scikit-learn's `StandardScaler` |
| `model=None` | Construct and fit a scaler, then transform the training data |
| `model=<fitted StandardScaler>` | Transform using existing statistics without fitting |
| `**options` | Original constructor options, allowed only without `model` |

`ScaledData.data` is the native output from the scaler. `ScaledData.model` is the
fitted upstream model. `ScaledData.transform(data)` returns a new container using
the same model. The container's field references are fixed, while its data and
model remain mutable.

```python
training = scale([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]])
queries = training.transform([[4.0, 40.0]])
assert queries.model is training.model
print(training.model.mean_)  # [2.0, 20.0]
```

Fit on training samples only, then transform validation and test samples. Fitting
a separate scaler on test data changes the transformation and leaks test-set
statistics. The adapter does not choose a data split for you.

Defaults center features and scale them to unit variance using `StandardScaler`.
Constant features follow upstream behavior. NaNs are ignored while fitting and
preserved during transformation; no imputation is performed. Empty, non-numeric,
or incorrectly shaped inputs and incompatible feature counts are validated by
the backend. Sparse input requires `with_mean=False`; implicit densification is
never used to make centering succeed. To control copies, pass the native `copy`
option; `copy=False` may modify compatible input arrays in place.

Invalid model objects, mixing a model with constructor options, and constructor
failures raise `ConfigurationError`. Backend `TypeError`/`ValueError` failures,
including an unfitted model, become `BackendError` with the original `__cause__`.
No model downloads or network calls are performed.

The distribution advertises adapter `tabular`, library `scikit-learn`, alias
`sklearn`, and operation `scale`. It can be called through the optional catalog:

```python
from pymplify_core import discover_adapters

catalog = discover_adapters(strict=True)
training = catalog.run("tabular", "scale", [[1.0, 10.0], [2.0, 20.0]])
```

Upstream reference:
[StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html).
