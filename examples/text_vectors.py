"""Run after installing the two local packages: python examples/text_vectors.py."""

from pymplify_text import vectorize


def main() -> None:
    result = vectorize(["Python simplifies machine learning", "Machine learning uses data"])
    queries = result.transform(["Python uses data"])
    print("Training matrix:", result.matrix.shape)
    print("Query matrix:", queries.matrix.shape)
    print("Vocabulary:", result.model.get_feature_names_out().tolist())

    # Every native option is available when fitting a new model.
    advanced = vectorize(["small model", "simple model"], ngram_range=(1, 2), max_features=100)
    print("Unigrams and bigrams:", advanced.model.get_feature_names_out().tolist())


if __name__ == "__main__":
    main()
