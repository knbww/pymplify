"""Discover installed adapters: python examples/adapter_catalog.py."""

from pymplify_core import Adapter, Operation, discover_adapters


def main() -> None:
    catalog = discover_adapters(strict=True)
    for adapter in catalog.adapters:
        print(adapter.name, adapter.library, [operation.name for operation in adapter.operations])
    print("scikit-learn adapters:", [item.name for item in catalog.for_library("sklearn")])
    print("Unsupported library:", catalog.for_library("not-supported"))

    texts = catalog.run("text", "vectorize", ["small language model", "simple machine learning"])
    print("Text matrix:", texts.matrix.shape)
    scaled = catalog.run("tabular", "scale", [[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]])
    print("Standardized features:", scaled.data)

    catalog.register(
        Adapter(
            name="custom",
            library="my-tools",
            operations=(Operation("word_count", lambda text: len(text.split()), "Count words."),),
        )
    )
    assert catalog.run("custom", "word_count", "one import one action") == 4


if __name__ == "__main__":
    main()
