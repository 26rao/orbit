"""Week 3 Verification Suite: Semantic Embeddings, Topic Clustering, and Novelty Benchmarking."""

import pytest
import numpy as np
from src.semantic.embeddings import SemanticEmbedder
from src.semantic.clustering import TopicClusterer
from src.semantic.novelty import is_novel, compute_title_similarity


def test_semantic_embedder():
    embedder = SemanticEmbedder(n_components=16)
    texts = [
        "Quantum computing algorithms for molecular simulation.",
        "Simulating complex molecular structures using quantum gates.",
        "Deep learning models for autonomous vehicle trajectory planning.",
    ]
    vecs = embedder.fit_transform(texts)
    assert vecs.shape[0] == 3
    # Check unit normalization
    norms = np.linalg.norm(vecs, axis=1)
    for n in norms:
        assert np.isclose(n, 1.0, atol=1e-3)

    # Dot product of normalized vectors equals cosine similarity
    sim_quantum = float(np.dot(vecs[0], vecs[1]))
    sim_unrelated = float(np.dot(vecs[0], vecs[2]))
    assert sim_quantum > sim_unrelated, f"Expected quantum papers to be closer ({sim_quantum} > {sim_unrelated})"


def test_differently_worded_clustering():
    """Verify related stories using different vocabulary cluster together."""
    items = [
        {
            "id": 1,
            "title": "Solid-state electrolyte breakthrough enables ultra-fast EV charging",
            "summary": "MIT engineers developed a lithium metal battery with non-flammable solid electrolyte.",
            "source_name": "MIT News",
            "published": "2026-10-17T00:00:00Z",
        },
        {
            "id": 2,
            "title": "Next-gen ceramic battery cell charges electric cars in 8 minutes",
            "summary": "New ceramic separator technology avoids dendrite growth in automotive power storage.",
            "source_name": "TechCrunch",
            "published": "2026-10-17T01:00:00Z",
        },
        {
            "id": 3,
            "title": "Supermassive black hole jet observed emitting TeV gamma rays",
            "summary": "Deep space observatory captured high-energy radiation from active galactic nucleus.",
            "source_name": "Nature Astronomy",
            "published": "2026-10-17T02:00:00Z",
        },
        {
            "id": 4,
            "title": "Astrophysicists record cosmic ray burst from relativistic galactic core",
            "summary": "Satellite array registers unprecedented particle acceleration in distant blazar.",
            "source_name": "arXiv Astro",
            "published": "2026-10-17T03:00:00Z",
        },
    ]

    clusterer = TopicClusterer(distance_threshold=0.92)
    clustered = clusterer.cluster_items(items)

    assert len(clustered) == 4
    # Battery items (1 and 2) must share the same cluster
    c1 = clustered[0]["cluster_id"]
    c2 = clustered[1]["cluster_id"]
    assert c1 == c2, f"Battery stories should share cluster, got {c1} and {c2}"

    # Astrophysics items (3 and 4) must share the same cluster
    c3 = clustered[2]["cluster_id"]
    c4 = clustered[3]["cluster_id"]
    assert c3 == c4, f"Astrophysics stories should share cluster, got {c3} and {c4}"

    # Battery and Astrophysics clusters must be different
    assert c1 != c3, f"Battery and Astrophysics should not be in same cluster ({c1} == {c3})"


def test_50_item_duplicate_precision_benchmark():
    """
    Acceptance benchmark: 50-item hand-labeled evaluation set:
    - 25 novel items across distinct scientific and technical domains
    - 25 pure syndicated reprints of those announcements
    Verify:
    - Pure reprints are detected as duplicates with >90% precision.
    """
    # 25 original announcements
    anchors = [
        "OpenAI releases lightweight reasoning model for edge devices",
        "DeepSeek announces open weights multimodal vision architecture",
        "Google Quantum AI demonstrates fault-tolerant logical qubit memory",
        "NVIDIA unveils Blackwell ultra architecture for generative computing",
        "Tesla initiates commercial robotaxi pilot in Austin Texas",
        "Meta open sources Llama 4 family with native multi-token prediction",
        "Apple introduces Apple Intelligence integration across Xcode IDE",
        "Anthropic launches autonomous computer use capability for Claude",
        "Microsoft researchers build DNA storage system with random access",
        "Toyota announces solid state battery mass production timeline for 2027",
        "SpaceX Starship completes orbital capture and tower catch in Boca Chica",
        "CERN reports observation of rare Higgs boson decay channel",
        "Moderna begins clinical trial for universal mRNA influenza vaccine",
        "DeepMind AlphaFold 3 predicts biomolecular structures with ligands",
        "Amazon introduces autonomous drone delivery fleet in Phoenix Arizona",
        "Sony showcases microLED display with 4000 nits peak brightness",
        "Neuralink second human patient successfully operates digital cursor",
        "Mistral AI releases Pixtral 12B multimodal open vision model",
        "Intel confirms 18A manufacturing process readiness for high volume",
        "Fusion reactor Tokamak achieves 100 million degree plasma for 10 minutes",
        "Waymo expands driverless ride-hailing services across Los Angeles",
        "ASML ships high-NA EUV lithography tool to semiconductor fabrication plant",
        "Perplexity announces Comet financial analysis intelligence search engine",
        "Cisco completes Splunk integration to unify enterprise cybersecurity",
        "Figure AI humanoid robot demonstrates autonomous logistics fulfillment",
    ]

    # 25 pure reprints / wire syndications (syndicated news with identical core title)
    pure_reprints = [
        "OpenAI releases lightweight reasoning model for edge devices - Tech Wire",
        "DeepSeek announces open weights multimodal vision architecture | AI News",
        "[Breaking] Google Quantum AI demonstrates fault-tolerant logical qubit memory",
        "NVIDIA unveils Blackwell ultra architecture for generative computing.",
        "Tesla initiates commercial robotaxi pilot in Austin Texas - Reuters",
        "Meta open sources Llama 4 family with native multi-token prediction (Update)",
        "Apple introduces Apple Intelligence integration across Xcode IDE - MacRumors",
        "Anthropic launches autonomous computer use capability for Claude - VentureBeat",
        "Microsoft researchers build DNA storage system with random access: Report",
        "Toyota announces solid state battery mass production timeline for 2027.",
        "SpaceX Starship completes orbital capture and tower catch in Boca Chica!",
        "CERN reports observation of rare Higgs boson decay channel (Phys.org)",
        "Moderna begins clinical trial for universal mRNA influenza vaccine - BioSpace",
        "DeepMind AlphaFold 3 predicts biomolecular structures with ligands.",
        "Amazon introduces autonomous drone delivery fleet in Phoenix Arizona - TechCrunch",
        "Sony showcases microLED display with 4000 nits peak brightness (AVS)",
        "Neuralink second human patient successfully operates digital cursor - Bloomberg",
        "Mistral AI releases Pixtral 12B multimodal open vision model | Hacker News",
        "Intel confirms 18A manufacturing process readiness for high volume.",
        "Fusion reactor Tokamak achieves 100 million degree plasma for 10 minutes - Science",
        "Waymo expands driverless ride-hailing services across Los Angeles - The Verge",
        "ASML ships high-NA EUV lithography tool to semiconductor fabrication plant - EE Times",
        "Perplexity announces Comet financial analysis intelligence search engine.",
        "Cisco completes Splunk integration to unify enterprise cybersecurity (PR)",
        "Figure AI humanoid robot demonstrates autonomous logistics fulfillment - Robotics",
    ]

    assert len(anchors) == 25
    assert len(pure_reprints) == 25

    # Measure detection
    true_positives = 0
    false_positives = 0
    false_negatives = 0

    for reprint in pure_reprints:
        novel, sim, match = is_novel(reprint, anchors, similarity_threshold=0.80)
        if not novel:
            true_positives += 1
        else:
            false_negatives += 1

    # Also test that truly distinct new announcements are NOT flagged as duplicates
    distinct_novel_announcements = [
        "James Webb Telescope detects atmospheric water on rocky exoplanet",
        "Researchers develop room-temperature magnetic levitation polymer",
        "New CRISPR enzyme achieves single-base editing without double-strand breaks",
        "Synthetic biocatalyst converts ambient carbon dioxide into jet fuel",
        "Optical interconnect delivers 100 terabits per second data transfer",
    ]
    for distinct in distinct_novel_announcements:
        novel, sim, match = is_novel(distinct, anchors, similarity_threshold=0.80)
        if not novel:
            false_positives += 1

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0

    print(f"\nPure Reprint Benchmark: TP={true_positives}/25, FP={false_positives}, Precision={precision:.3f}, Recall={recall:.3f}")
    assert precision >= 0.90, f"Expected duplicate precision >= 0.90, got {precision:.3f}"
    assert recall >= 0.90, f"Expected duplicate recall >= 0.90, got {recall:.3f}"


if __name__ == "__main__":
    print("Running ORBIT Week 3 Semantic Intelligence checks...")
    test_semantic_embedder()
    print("  [x] Semantic embedder & normalization verified")
    test_differently_worded_clustering()
    print("  [x] Semantic grouping of differently worded stories verified")
    test_50_item_duplicate_precision_benchmark()
    print("  [x] 50-item duplicate detection precision benchmark verified (>90%)")
    print("\nALL ORBIT WEEK 3 CHECKS PASSED SUCCESSFULLY!")
