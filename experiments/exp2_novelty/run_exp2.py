"""Experiment 2: Duplicate and Novelty Detection Benchmark.
Tests whether ORBIT distinguishes genuine new developments from syndicated reprints.
"""

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.semantic.novelty import is_novel, compute_title_similarity

EVAL_FILE = ROOT / "data" / "eval_set" / "eval_dataset.json"


def run_experiment_2():
    with open(EVAL_FILE, "r", encoding="utf-8") as f:
        pairs = json.load(f)["exp2_novelty"]

    print(f"\n=======================================================")
    print(f" EXPERIMENT 2: DUPLICATE & NOVELTY DETECTION (25 Pairs)")
    print(f"=======================================================")

    anchors = [p["anchor"] for p in pairs]
    duplicates = [p["duplicate"] for p in pairs]

    # Evaluate duplicate detection
    true_positives = 0
    false_negatives = 0
    false_positives = 0
    similarities = []

    for i in range(len(pairs)):
        anchor = anchors[i]
        dup = duplicates[i]
        sim = compute_title_similarity(anchor, dup)
        similarities.append(sim)

        # Check against all anchors
        novel, max_sim, match = is_novel(dup, anchors, similarity_threshold=0.80)
        if not novel:
            true_positives += 1
        else:
            false_negatives += 1

    precision = true_positives / float(true_positives + false_positives) if (true_positives + false_positives) else 0.0
    recall = true_positives / float(true_positives + false_negatives) if (true_positives + false_negatives) else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) else 0.0

    results = {
        "test_pairs": len(pairs),
        "true_positives": true_positives,
        "false_negatives": false_negatives,
        "false_positives": false_positives,
        "duplicate_detection_precision": round(precision, 3),
        "duplicate_detection_recall": round(recall, 3),
        "duplicate_detection_f1": round(f1, 3),
        "mean_syndicated_similarity": round(sum(similarities) / len(similarities), 3),
    }

    print(f"Results:")
    print(f"  Precision:           {results['duplicate_detection_precision'] * 100:.1f}%")
    print(f"  Recall:              {results['duplicate_detection_recall'] * 100:.1f}%")
    print(f"  F1 Score:            {results['duplicate_detection_f1']:.3f}")
    print(f"  Mean Similarity:     {results['mean_syndicated_similarity']:.3f}")
    return results


if __name__ == "__main__":
    run_experiment_2()
