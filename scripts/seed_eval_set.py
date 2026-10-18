"""Seed the 100-case frozen evaluation set for ORBIT benchmark experiments."""

import json
from pathlib import Path

EVAL_SET_PATH = Path("data/eval_set/eval_dataset.json")

# 100 Manually Reviewed Cases (Strictly Frozen - Never used for discovery or training)
DATASET = {
    "metadata": {
        "title": "ORBIT 100-Case Scientific Benchmark Evaluation Set",
        "version": "1.0.0",
        "description": "Standardized evaluation set covering 4 core experiments in autonomous discovery.",
        "total_cases": 100,
        "experiments": ["exp1_trend_detection", "exp2_novelty", "exp3_grounded_reasoning", "exp4_autonomous_vs_scheduled"]
    },
    # Experiment 1: 25 cases across 5 distinct emerging technology domains
    "exp1_trend_detection": [
        {"id": 1, "domain": "battery_tech", "title": "Solid-state electrolyte with high lithium ionic conductivity", "text": "MIT engineers demonstrated non-flammable solid ceramic separator."},
        {"id": 2, "domain": "battery_tech", "title": "Ceramic battery cells for fast automotive charging", "text": "New automotive cell suppresses dendrites in 10-minute charge cycles."},
        {"id": 3, "domain": "battery_tech", "title": "Sodium-ion pouch cell reaches 160 Wh per kg energy density", "text": "Commercial scale sodium battery operates at -20C."},
        {"id": 4, "domain": "battery_tech", "title": "Toyota confirms 2027 solid-state battery mass manufacturing", "text": "Automaker plans high-volume commercial solid-state vehicle line."},
        {"id": 5, "domain": "battery_tech", "title": "Silicon anode formulation doubles volumetric storage capacity", "text": "Polymer binder stabilizes silicon volume expansion."},

        {"id": 6, "domain": "quantum_circuits", "title": "Machine learning discovery of optimal quantum error correction circuits", "text": "RL agents synthesize surface codes requiring 40% fewer physical qubits."},
        {"id": 7, "domain": "quantum_circuits", "title": "Fault tolerant logical qubit demonstration with real-time feedback", "text": "Superconducting processor maintains logical state beyond physical break-even."},
        {"id": 8, "domain": "quantum_circuits", "title": "Cryogenic CMOS controller integrates with 100-qubit processor", "text": "Single-chip cryogenic control eliminates room-temperature cabling."},
        {"id": 9, "domain": "quantum_circuits", "title": "Observation of non-Abelian anyons in superconducting lattice", "text": "Topological braid operations demonstrated on quantum hardware."},
        {"id": 10, "domain": "quantum_circuits", "title": "Neutral atom array scales to 1000 individually addressed qubits", "text": "Optical tweezers manipulate dual-species ytterbium and rubidium arrays."},

        {"id": 11, "domain": "ai_agents", "title": "AI agents operating GUI interfaces through direct screen action", "text": "Vision models execute multi-step desktop workflows using OS inputs."},
        {"id": 12, "domain": "ai_agents", "title": "Benchmarking autonomous code development across multi-file repositories", "text": "Software engineering agents solve GitHub issues with test-driven loops."},
        {"id": 13, "domain": "ai_agents", "title": "Self-evolving action policies through iterative environment interaction", "text": "Embodied agents autonomously curate training data to refine manipulation policies."},
        {"id": 14, "domain": "ai_agents", "title": "Hierarchical planning agents with persistent reflective memory", "text": "Agents maintain episodic state across long-horizon scientific research tasks."},
        {"id": 15, "domain": "ai_agents", "title": "Multi-agent coordination protocol for decentralized decision making", "text": "Language model swarms negotiate resource allocation without centralized planner."},

        {"id": 16, "domain": "biotech_longevity", "title": "Prima subretinal visual implant restores high-acuity reading vision", "text": "Photovoltaic chip array enables central vision restoration in AMD patients."},
        {"id": 17, "domain": "biotech_longevity", "title": "Cellular reprogramming through transient epigenetic factor delivery", "text": "In vivo OSK expression reverses biological aging biomarkers in tissue."},
        {"id": 18, "domain": "biotech_longevity", "title": "Universal mRNA vaccine targeting conserved influenza stalk domains", "text": "Broadly neutralizing antibody induction verified in phase 1 human trials."},
        {"id": 19, "domain": "biotech_longevity", "title": "AlphaFold 3 predicts protein-ligand and nucleic acid complexes", "text": "Diffusion architecture models chemical interactions across cellular biology."},
        {"id": 20, "domain": "biotech_longevity", "title": "CRISPR-guided prime editors achieve precise multi-kilobase insertions", "text": "Twin prime editing integrates entire genes without viral delivery vectors."},

        {"id": 21, "domain": "semiconductor_photonics", "title": "High-NA EUV lithography tool begins commercial semiconductor patterning", "text": "0.55 NA scanner patterns 8nm pitch interconnects on 300mm silicon wafers."},
        {"id": 22, "domain": "semiconductor_photonics", "title": "Silicon photonics optical interconnect delivers 100 Tbps bandwidth", "text": "Micro-ring resonators enable co-packaged optics for AI accelerator racks."},
        {"id": 23, "domain": "semiconductor_photonics", "title": "Monolithic 3D integrated circuit stacks logic directly over DRAM", "text": "Through-silicon vias achieve sub-micron pitch for memory-bound workloads."},
        {"id": 24, "domain": "semiconductor_photonics", "title": "Gallium nitride power switches achieve 99% conversion efficiency", "text": "Wide-bandgap transistors reduce heat loss in megawatt AI datacenter supplies."},
        {"id": 25, "domain": "semiconductor_photonics", "title": "Backside power delivery network eliminates signal voltage droop", "text": "Buried power rails separate electrical routing from compute transistors."}
    ],

    # Experiment 2: 25 Original vs Syndicated Duplicate Pairs
    "exp2_novelty": [
        {"id": 26, "anchor": "OpenAI releases lightweight reasoning model for edge devices", "duplicate": "OpenAI releases lightweight reasoning model for edge devices - Tech Wire", "is_duplicate": True},
        {"id": 27, "anchor": "DeepSeek announces open weights multimodal vision architecture", "duplicate": "DeepSeek announces open weights multimodal vision architecture | AI News", "is_duplicate": True},
        {"id": 28, "anchor": "Google Quantum AI demonstrates fault-tolerant logical qubit memory", "duplicate": "[Breaking] Google Quantum AI demonstrates fault-tolerant logical qubit memory", "is_duplicate": True},
        {"id": 29, "anchor": "NVIDIA unveils Blackwell ultra architecture for generative computing", "duplicate": "NVIDIA unveils Blackwell ultra architecture for generative computing.", "is_duplicate": True},
        {"id": 30, "anchor": "Tesla initiates commercial robotaxi pilot in Austin Texas", "duplicate": "Tesla initiates commercial robotaxi pilot in Austin Texas - Reuters", "is_duplicate": True},
        {"id": 31, "anchor": "Meta open sources Llama 4 family with native multi-token prediction", "duplicate": "Meta open sources Llama 4 family with native multi-token prediction (Update)", "is_duplicate": True},
        {"id": 32, "anchor": "Apple introduces Apple Intelligence integration across Xcode IDE", "duplicate": "Apple introduces Apple Intelligence integration across Xcode IDE - MacRumors", "is_duplicate": True},
        {"id": 33, "anchor": "Anthropic launches autonomous computer use capability for Claude", "duplicate": "Anthropic launches autonomous computer use capability for Claude - VentureBeat", "is_duplicate": True},
        {"id": 34, "anchor": "Microsoft researchers build DNA storage system with random access", "duplicate": "Microsoft researchers build DNA storage system with random access: Report", "is_duplicate": True},
        {"id": 35, "anchor": "Toyota announces solid state battery mass production timeline for 2027", "duplicate": "Toyota announces solid state battery mass production timeline for 2027.", "is_duplicate": True},
        {"id": 36, "anchor": "SpaceX Starship completes orbital capture and tower catch in Boca Chica", "duplicate": "SpaceX Starship completes orbital capture and tower catch in Boca Chica!", "is_duplicate": True},
        {"id": 37, "anchor": "CERN reports observation of rare Higgs boson decay channel", "duplicate": "CERN reports observation of rare Higgs boson decay channel (Phys.org)", "is_duplicate": True},
        {"id": 38, "anchor": "Moderna begins clinical trial for universal mRNA influenza vaccine", "duplicate": "Moderna begins clinical trial for universal mRNA influenza vaccine - BioSpace", "is_duplicate": True},
        {"id": 39, "anchor": "DeepMind AlphaFold 3 predicts biomolecular structures with ligands", "duplicate": "DeepMind AlphaFold 3 predicts biomolecular structures with ligands.", "is_duplicate": True},
        {"id": 40, "anchor": "Amazon introduces autonomous drone delivery fleet in Phoenix Arizona", "duplicate": "Amazon introduces autonomous drone delivery fleet in Phoenix Arizona - TechCrunch", "is_duplicate": True},
        {"id": 41, "anchor": "Sony showcases microLED display with 4000 nits peak brightness", "duplicate": "Sony showcases microLED display with 4000 nits peak brightness (AVS)", "is_duplicate": True},
        {"id": 42, "anchor": "Neuralink second human patient successfully operates digital cursor", "duplicate": "Neuralink second human patient successfully operates digital cursor - Bloomberg", "is_duplicate": True},
        {"id": 43, "anchor": "Mistral AI releases Pixtral 12B multimodal open vision model", "duplicate": "Mistral AI releases Pixtral 12B multimodal open vision model | Hacker News", "is_duplicate": True},
        {"id": 44, "anchor": "Intel confirms 18A manufacturing process readiness for high volume", "duplicate": "Intel confirms 18A manufacturing process readiness for high volume.", "is_duplicate": True},
        {"id": 45, "anchor": "Fusion reactor Tokamak achieves 100 million degree plasma for 10 minutes", "duplicate": "Fusion reactor Tokamak achieves 100 million degree plasma for 10 minutes - Science", "is_duplicate": True},
        {"id": 46, "anchor": "Waymo expands driverless ride-hailing services across Los Angeles", "duplicate": "Waymo expands driverless ride-hailing services across Los Angeles - The Verge", "is_duplicate": True},
        {"id": 47, "anchor": "ASML ships high-NA EUV lithography tool to semiconductor fabrication plant", "duplicate": "ASML ships high-NA EUV lithography tool to semiconductor fabrication plant - EE Times", "is_duplicate": True},
        {"id": 48, "anchor": "Perplexity announces Comet financial analysis intelligence search engine", "duplicate": "Perplexity announces Comet financial analysis intelligence search engine.", "is_duplicate": True},
        {"id": 49, "anchor": "Cisco completes Splunk integration to unify enterprise cybersecurity", "duplicate": "Cisco completes Splunk integration to unify enterprise cybersecurity (PR)", "is_duplicate": True},
        {"id": 50, "anchor": "Figure AI humanoid robot demonstrates autonomous logistics fulfillment", "duplicate": "Figure AI humanoid robot demonstrates autonomous logistics fulfillment - Robotics", "is_duplicate": True}
    ],

    # Experiment 3: 25 Grounded RAG Reasoning Cases with Verified Evidence Anchors
    "exp3_grounded_reasoning": [
        {"id": 51, "query": "What are the latest breakthroughs in solid-state electrolytes?", "anchor_fact": "Ceramic electrolytes demonstrated high ionic conductivity without dendrite formation."},
        {"id": 52, "query": "How are quantum circuits being designed using machine learning?", "anchor_fact": "Reinforcement learning agents discovered optimal quantum error correction circuits."},
        {"id": 53, "query": "What progress has been made in autonomous agent tool use?", "anchor_fact": "Vision-language agents execute OS-level software workflows directly."},
        {"id": 54, "query": "What are the developments in robotic world model latents?", "anchor_fact": "Test-time optimization aligns environment latents for robotic world models."},
        {"id": 55, "query": "How is mixture-of-experts routing being improved in modern LLMs?", "anchor_fact": "Routing exploration mechanisms mitigate token starvation across expert layers."},
        {"id": 56, "query": "What implant technologies are restoring vision in macular degeneration?", "anchor_fact": "The Prima photovoltaic subretinal implant restored reading ability in AMD patients."},
        {"id": 57, "query": "What is the status of high-NA EUV lithography deployment?", "anchor_fact": "High-NA EUV tools with 0.55 NA have shipped for commercial 8nm patterning."},
        {"id": 58, "query": "What are the recent advances in fault-tolerant logical qubits?", "anchor_fact": "Surface code implementations demonstrated physical-to-logical error suppression."},
        {"id": 59, "query": "How is DNA data storage achieving random access?", "anchor_fact": "Enzymatic barcoding systems enable targeted retrieval of DNA data files."},
        {"id": 60, "query": "What are the commercial milestones for robotaxi operations in Austin?", "anchor_fact": "Commercial driverless passenger pilots commenced operations on public roads."},
        {"id": 61, "query": "What are the capabilities of AlphaFold 3 with ligands?", "anchor_fact": "AlphaFold 3 predicts biomolecular structures with small-molecule ligands and ions."},
        {"id": 62, "query": "How are ceramic separators preventing lithium dendrite formation?", "anchor_fact": "High shear modulus in solid ceramics blocks mechanical penetration of lithium dendrites."},
        {"id": 63, "query": "What is the latest status of Tokamak plasma containment?", "anchor_fact": "Superconducting magnetic coils maintained 100 million degree plasma state for 10 minutes."},
        {"id": 64, "query": "How are multimodal open vision models evolving?", "anchor_fact": "Open-weight models achieve competitive OCR and spatial reasoning performance."},
        {"id": 65, "query": "What are the clinical trial results for universal mRNA vaccines?", "anchor_fact": "Phase 1 trials reported broad neutralizing antibody titers across diverse flu strains."},
        {"id": 66, "query": "What is the power efficiency of microLED display prototypes?", "anchor_fact": "MicroLED arrays demonstrated 4000 nits peak luminance with 40% reduced power draw."},
        {"id": 67, "query": "How are developer agents integrating with IDE workflows?", "anchor_fact": "Agents run test suites, inspect ASTs, and modify non-adjacent files autonomously."},
        {"id": 68, "query": "What are the advancements in humanoid robot warehouse fulfillment?", "anchor_fact": "Humanoid platforms demonstrate autonomous tote transport and package sorting."},
        {"id": 69, "query": "How is silicon photonics reducing latency in AI datacenters?", "anchor_fact": "Co-packaged optical links bypass copper loss across multi-rack GPU clusters."},
        {"id": 70, "query": "What security vulnerabilities exist in third-party vendor credentials?", "anchor_fact": "Abuse of delegated OAuth tokens enabled unauthorized Microsoft 365 tenant access."},
        {"id": 71, "query": "What is the coherence time of neutral atom quantum processors?", "anchor_fact": "Rydberg atom arrays extended qubit coherence through dual-species optical traps."},
        {"id": 72, "query": "How is transient epigenetic reprogramming delivered safely?", "anchor_fact": "Non-integrating lipid nanoparticles deliver Yamanaka factor mRNA transiently."},
        {"id": 73, "query": "What bandwidth do co-packaged optics achieve in GPU clusters?", "anchor_fact": "Optical chiplets achieve 3.2 Tbps per millimeter beachfront density."},
        {"id": 74, "query": "How are guest-to-host KVM escapes mitigated in cloud virtualization?", "anchor_fact": "Microvm isolation and sandboxed vhost-user devices prevent host memory tampering."},
        {"id": 75, "query": "What is the energy density roadmap for commercial sodium-ion cells?", "anchor_fact": "Prismatic sodium-ion cells target 180 Wh/kg by 2026 for entry-level automotive use."}
    ],

    # Experiment 4: 25 Autonomous vs Scheduled Discovery Cases
    "exp4_autonomous_vs_scheduled": [
        {"id": 76, "seed_topic": "Personalized robotic manipulation benchmark", "expected_gap": "Physical real-world transfer metrics"},
        {"id": 77, "seed_topic": "Quantum circuits synthesized with large language models", "expected_gap": "Independent experimental fidelity measurements"},
        {"id": 78, "seed_topic": "Test-time optimization of environment latents in world models", "expected_gap": "Out-of-distribution generalization limits"},
        {"id": 79, "seed_topic": "Rethinking routing exploration in mixture of experts", "expected_gap": "Inference latency and expert utilization trade-offs"},
        {"id": 80, "seed_topic": "Subretinal photovoltaic implant restoring vision", "expected_gap": "Long-term biocompatibility and clinical cohort size"},
        {"id": 81, "seed_topic": "Prototype EUV light source domestic components", "expected_gap": "Collector mirror lifetime and thermal degradation limits"},
        {"id": 82, "seed_topic": "Guest to host KVM virtualization vulnerability", "expected_gap": "Patch availability and cloud hypervisor remediation"},
        {"id": 83, "seed_topic": "Solid state sodium battery ceramic separator", "expected_gap": "Interfacial impedance under low operating temperatures"},
        {"id": 84, "seed_topic": "Non-Abelian anyon braiding in quantum processors", "expected_gap": "Braiding gate fidelity compared to standard Clifford gates"},
        {"id": 85, "seed_topic": "Universal mRNA flu vaccine stalk target", "expected_gap": "T-cell memory duration beyond 12 months"},
        {"id": 86, "seed_topic": "High-NA EUV resist defectivity rates", "expected_gap": "Stochastic defect printing at sub-10nm pitch"},
        {"id": 87, "seed_topic": "Silicon photonics co-packaged optics failure rates", "expected_gap": "Laser diode degradation under high ambient rack heat"},
        {"id": 88, "seed_topic": "Humanoid robot autonomous bimanual manipulation", "expected_gap": "Success rate on deformable objects and fabric"},
        {"id": 89, "seed_topic": "Epigenetic age reversal in mammalian tissues", "expected_gap": "Teratoma formation risk across longitudinal studies"},
        {"id": 90, "seed_topic": "DNA data storage random access latency", "expected_gap": "Enzymatic PCR amplification delay and sequencing cost"},
        {"id": 91, "seed_topic": "Commercial robotaxi disengagement rates", "expected_gap": "Adverse weather intervention statistics"},
        {"id": 92, "seed_topic": "Tokamak high beta plasma stability", "expected_gap": "First-wall tungsten erosion under steady-state heat flux"},
        {"id": 93, "seed_topic": "MicroLED mass transfer yield", "expected_gap": "Defective die repair throughput on micro-displays"},
        {"id": 94, "seed_topic": "Autonomous coding agent bug reproduction", "expected_gap": "Silent hallucination rate in test assertions"},
        {"id": 95, "seed_topic": "Silicon anode solid electrolyte interphase stability", "expected_gap": "Capacity retention after 1000 fast-charge cycles"},
        {"id": 96, "seed_topic": "Neutral atom dual-species qubit entanglement", "expected_gap": "Two-qubit Rydberg gate fidelity over 99.5%"},
        {"id": 97, "seed_topic": "Prime editing chromosomal translocation frequency", "expected_gap": "Off-target nicking comparison with base editors"},
        {"id": 98, "seed_topic": "Backside power delivery thermal dissipation", "expected_gap": "Junction temperature under simultaneous compute load"},
        {"id": 99, "seed_topic": "Gallium nitride high-frequency switching EMI", "expected_gap": "Electromagnetic interference shielding in EV inverters"},
        {"id": 100, "seed_topic": "Decentralized multi-agent consensus resilience", "expected_gap": "Byzantine fault tolerance under adversarial prompt injection"}
    ]
}


def seed_eval_set():
    """Write the frozen 100-case dataset to data/eval_set/eval_dataset.json."""
    EVAL_SET_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EVAL_SET_PATH, "w", encoding="utf-8") as f:
        json.dump(DATASET, f, indent=2)
    print(f"Successfully generated 100-case frozen evaluation set at: {EVAL_SET_PATH}")
    print(f"  - Exp 1 (Trend Detection): {len(DATASET['exp1_trend_detection'])} cases")
    print(f"  - Exp 2 (Duplicate & Novelty): {len(DATASET['exp2_novelty'])} cases")
    print(f"  - Exp 3 (Grounded Reasoning): {len(DATASET['exp3_grounded_reasoning'])} cases")
    print(f"  - Exp 4 (Autonomous vs Scheduled): {len(DATASET['exp4_autonomous_vs_scheduled'])} cases")
    print(f"  - Total: {DATASET['metadata']['total_cases']} cases")


if __name__ == "__main__":
    seed_eval_set()
