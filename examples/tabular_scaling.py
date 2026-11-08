"""Run after installing core and tabular: python examples/tabular_scaling.py."""

from pymplify_tabular import scale


def main() -> None:
    training = scale([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]])
    queries = training.transform([[4.0, 40.0]])
    print("Standardized training data:", training.data)
    print("Query using training statistics:", queries.data)
    print("Training means:", training.model.mean_)
    assert queries.model is training.model


if __name__ == "__main__":
    main()
