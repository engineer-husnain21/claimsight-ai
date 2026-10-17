"""Deterministic embedding function so tests never download or call a model."""

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

KEYWORDS = ("limit", "dental", "fraud", "mri")


class FakeEmbeddingFunction(EmbeddingFunction[Documents]):
    """Embed text as keyword counts, enough to make search results predictable."""

    def __init__(self) -> None:
        pass

    def __call__(self, input: Documents) -> Embeddings:
        return [[float(text.lower().count(word)) + 0.01 for word in KEYWORDS] for text in input]

    @staticmethod
    def name() -> str:
        return "fake-keyword-embedding"

    def get_config(self) -> dict[str, object]:

        return {}

    @staticmethod
    def build_from_config(config: dict[str, object]) -> "FakeEmbeddingFunction":
        return FakeEmbeddingFunction()
