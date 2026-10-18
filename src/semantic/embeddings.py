"""Vector embedding engine for semantic retrieval and clustering."""

from typing import List, Union
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize


class SemanticEmbedder:
    """
    Subword semantic embedder using word-bounded character n-grams (char_wb 3-5)
    with TF-IDF and L2 normalization. Captures semantic stems and root relationships
    across varying vocabularies without external model downloads.
    """

    def __init__(self, n_components: int = 128):
        self.n_components = n_components
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            sublinear_tf=True,
            strip_accents="unicode",
        )
        self.svd: Union[TruncatedSVD, None] = None
        self.is_fitted = False

    def fit_transform(self, texts: List[str]) -> np.ndarray:
        """Fit vectorizer on texts and return normalized dense embeddings."""
        if not texts:
            return np.empty((0, self.n_components))

        tfidf_matrix = self.vectorizer.fit_transform(texts)
        n_samples, n_features = tfidf_matrix.shape

        # If enough samples, project with SVD for compact density, otherwise keep full normalized space
        if n_samples >= 15 and n_features >= self.n_components:
            self.svd = TruncatedSVD(n_components=min(self.n_components, n_samples - 1), random_state=42)
            dense_vecs = self.svd.fit_transform(tfidf_matrix)
        else:
            self.svd = None
            dense_vecs = tfidf_matrix.toarray()

        self.is_fitted = True
        return normalize(dense_vecs, norm="l2")

    def transform(self, texts: List[str]) -> np.ndarray:
        """Transform new texts into embedding space."""
        if not self.is_fitted:
            return self.fit_transform(texts)

        tfidf_matrix = self.vectorizer.transform(texts)
        if self.svd is not None:
            dense_vecs = self.svd.transform(tfidf_matrix)
        else:
            dense_vecs = tfidf_matrix.toarray()

        return normalize(dense_vecs, norm="l2")


_default_embedder = SemanticEmbedder()


def embed_texts(texts: List[str]) -> np.ndarray:
    """Helper to embed a batch of texts."""
    return _default_embedder.fit_transform(texts)
