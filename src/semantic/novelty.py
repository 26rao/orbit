"""Novelty and similarity calculation engine."""

import math
import re
from collections import Counter
from typing import List, Tuple, Optional


def _tokenize_ngrams(text: str, n: int = 3) -> Counter:
    """Generate character n-grams from normalized text for robust subword similarity."""
    cleaned = re.sub(r"\W+", " ", text.lower()).strip()
    words = cleaned.split()
    # Word unigrams + char trigrams for high semantic & lexical overlap accuracy
    tokens = list(words)
    for word in words:
        if len(word) >= n:
            tokens.extend([word[i:i+n] for i in range(len(word) - n + 1)])
        else:
            tokens.append(word)
    return Counter(tokens)


def compute_title_similarity(title_a: str, title_b: str) -> float:
    """
    Compute cosine similarity between two titles using term/n-gram vectors.
    Returns float in range [0.0, 1.0].
    """
    vec_a = _tokenize_ngrams(title_a)
    vec_b = _tokenize_ngrams(title_b)

    intersection = set(vec_a.keys()) & set(vec_b.keys())
    numerator = sum(vec_a[x] * vec_b[x] for x in intersection)

    sum_a = sum(val ** 2 for val in vec_a.values())
    sum_b = sum(val ** 2 for val in vec_b.values())
    denominator = math.sqrt(sum_a) * math.sqrt(sum_b)

    if not denominator:
        return 0.0
    return float(numerator) / denominator


def is_novel(
    candidate_title: str,
    existing_titles: List[str],
    similarity_threshold: float = 0.92,
) -> Tuple[bool, float, Optional[str]]:
    """
    Check if a candidate title is novel against a list of existing titles.
    Returns (is_novel, max_similarity, most_similar_title).
    If max_similarity >= similarity_threshold, is_novel is False.
    """
    if not existing_titles:
        return True, 0.0, None

    max_sim = 0.0
    closest_match = None

    for existing in existing_titles:
        sim = compute_title_similarity(candidate_title, existing)
        if sim > max_sim:
            max_sim = sim
            closest_match = existing
        if max_sim >= similarity_threshold:
            return False, max_sim, closest_match

    return (max_sim < similarity_threshold), max_sim, closest_match
