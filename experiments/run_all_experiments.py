"""Master Runner for all 4 ORBIT Scientific Experiments (100 Cases Total).
Executes benchmarks and saves standardized metric results to data/eval_set/experiment_results.json.
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
from datetime import datetime

from experiments.exp1_trend_detection.run_exp1 import run_experiment_1
from experiments.exp2_novelty.run_exp2 import run_experiment_2
from experiments.exp3_grounded_reasoning.run_exp3 import run_experiment_3
from experiments.exp4_autonomous_vs_scheduled.run_exp4 import run_experiment_4

OUTPUT_PATH = ROOT / "data" / "eval_set" / "experiment_results.json"


def run_all():
    print("=" * 65)
    print("  ORBIT BENCHMARK SUITE — EXECUTING ALL 4 EXPERIMENTS")
    print("=" * 65)

    exp1_res = run_experiment_1()
    exp2_res = run_experiment_2()
    exp3_res = run_experiment_3()
    exp4_res = run_experiment_4()

    summary_payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "benchmark_suite": "ORBIT 100-Case Evaluation Standard",
        "experiments": {
            "exp1_trend_detection": exp1_res,
            "exp2_novelty_deduplication": exp2_res,
            "exp3_grounded_reasoning": exp3_res,
            "exp4_autonomous_vs_scheduled": exp4_res,
        },
        "all_acceptance_criteria_passed": (
            exp1_res.get("semantic_cluster_purity", 0) >= 0.70
            and exp2_res.get("duplicate_detection_precision", 0) >= 0.90
            and exp3_res.get("meets_acceptance_criterion", False)
            and exp4_res.get("meets_acceptance_criterion", False)
        ),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)

    print("\n" + "=" * 65)
    print("  ORBIT BENCHMARK SUITE SCOREBOARD")
    print("=" * 65)
    print(f"  Exp 1 (Trend Clustering Purity):     {exp1_res.get('semantic_cluster_purity', 0) * 100:.1f}%")
    print(f"  Exp 2 (Duplicate Precision / Recall): {exp2_res.get('duplicate_detection_precision', 0) * 100:.1f}% / {exp2_res.get('duplicate_detection_recall', 0) * 100:.1f}%")
    print(f"  Exp 3 (Unsupported Claim Reduction): {exp3_res.get('unsupported_claim_reduction_pct', 0):.1f}% (Target: >=40%)")
    print(f"  Exp 4 (Autonomous Novelty Gain):     +{exp4_res.get('relative_improvement_pct', 0):.1f}% (Target: >=30%)")
    print(f"  Status:                              {'ALL TARGETS PASSED' if summary_payload['all_acceptance_criteria_passed'] else 'TARGETS FAILED'}")
    print(f"  Results saved to:                    {OUTPUT_PATH.as_posix()}")
    print("=" * 65)

    return summary_payload


if __name__ == "__main__":
    run_all()
