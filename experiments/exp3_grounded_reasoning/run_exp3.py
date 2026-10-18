"""Experiment 3: Grounded Reasoning vs Pure LLM Benchmark.
Evaluates reduction in unsupported claims and citation correctness on 25 technical queries.
Acceptance Criterion: >=40% unsupported claim reduction.
"""

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.eval.grounding_eval import run_experiment_3_benchmark

EVAL_FILE = ROOT / "data" / "eval_set" / "eval_dataset.json"


def run_experiment_3():
    with open(EVAL_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)["exp3_grounded_reasoning"]

    print("\n=======================================================")
    print(f" EXPERIMENT 3: GROUNDED RAG VS PURE LLM ({len(cases)} Cases)")
    print("=======================================================")

    questions = [c["query"] for c in cases]
    results = run_experiment_3_benchmark(questions=questions)

    print("Results:")
    print(f"  Cases Evaluated:                {results['num_questions']}")
    print(f"  Grounded RAG Unsupported Rate: {results['grounded_rag_unsupported_rate'] * 100:.1f}%")
    print(f"  Pure LLM Unsupported Rate:     {results['pure_llm_unsupported_rate'] * 100:.1f}%")
    print(f"  Unsupported Claim Reduction:   {results['unsupported_claim_reduction_pct']:.1f}%")
    print(f"  Meets >=40% Target:            {'PASS' if results['meets_acceptance_criterion'] else 'FAIL'}")

    return results


if __name__ == "__main__":
    run_experiment_3()
