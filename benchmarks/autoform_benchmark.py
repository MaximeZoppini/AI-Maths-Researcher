"""
Autoformalization Benchmark for Phase 3 of VISION.md.txt.
Evaluates the Autoformalizer with triple guardrails on 15 diverse mathematical problems.
"""

from dataclasses import dataclass
from typing import List, Optional
import time

from agent.autoformalizer import Autoformalizer, AutoformalizationResult

@dataclass
class BenchmarkProblem:
    id: str
    name: str
    category: str
    text: str

BENCHMARK_DATASET: List[BenchmarkProblem] = [
    BenchmarkProblem(
        id="af_01",
        name="rect_diag_sq",
        category="Algebra",
        text="Let a and b be real numbers. If a * b = 180 and 2 * (a + b) = 54, prove that a^2 + b^2 = 369."
    ),
    BenchmarkProblem(
        id="af_02",
        name="cone_volume",
        category="Geometry/Algebra",
        text="Let b, h, and v be positive real numbers. If v = 1 / 3 * (b * h), b = 30, and h = 13 / 2, prove that v = 65."
    ),
    BenchmarkProblem(
        id="af_03",
        name="even_sq_even",
        category="Number Theory",
        text="For every integer n, if n^2 is even, then n is even."
    ),
    BenchmarkProblem(
        id="af_04",
        name="mod3_sq_ne_two",
        category="Number Theory",
        text="For every integer n, n^2 % 3 ≠ 2."
    ),
    BenchmarkProblem(
        id="af_05",
        name="diff_of_squares",
        category="Algebra",
        text="For all real numbers a and b, (a - b) * (a + b) = a^2 - b^2."
    ),
    BenchmarkProblem(
        id="af_06",
        name="am_gm_two",
        category="Inequalities",
        text="For all non-negative real numbers a and b, 2 * Real.sqrt (a * b) ≤ a + b."
    ),
    BenchmarkProblem(
        id="af_07",
        name="sum_two_odds",
        category="Number Theory",
        text="For all integers a and b, if a and b are odd, then a + b is even."
    ),
    BenchmarkProblem(
        id="af_08",
        name="linear_system",
        category="Algebra",
        text="Let x and y be real numbers. If 2 * x + 3 * y = 12 and x - y = 1, then x = 3 ∧ y = 2."
    ),
    BenchmarkProblem(
        id="af_09",
        name="pos_mul_pos",
        category="Order",
        text="For all real numbers a and b, if 0 < a and 0 < b, then 0 < a * b."
    ),
    BenchmarkProblem(
        id="af_10",
        name="nat_sub_add_cancel",
        category="Arithmetics",
        text="For all natural numbers n and m, (n + m) - m = n."
    ),
    BenchmarkProblem(
        id="af_11",
        name="cauchy_schwarz_2d",
        category="Inequalities",
        text="For all real numbers a1 a2 b1 b2, (a1 * b1 + a2 * b2)^2 ≤ (a1^2 + a2^2) * (b1^2 + b2^2)."
    ),
    BenchmarkProblem(
        id="af_12",
        name="square_nonneg",
        category="Algebra",
        text="For every real number x, 0 ≤ x^2."
    ),
    BenchmarkProblem(
        id="af_13",
        name="arithmetic_mean",
        category="Algebra",
        text="Let x and y be real numbers. If (x + y) / 2 = 10 and x = 4, then y = 16."
    ),
    BenchmarkProblem(
        id="af_14",
        name="mul_zero_prod",
        category="Algebra",
        text="For all real numbers a and b, if a * b = 0, then a = 0 ∨ b = 0."
    ),
    BenchmarkProblem(
        id="af_15",
        name="div_by_six",
        category="Number Theory",
        text="For every integer n, 6 ∣ (n^3 - n)."
    )
]

def run_autoform_benchmark(limit: int = 15):
    selected = BENCHMARK_DATASET[:limit]
    print("\n" + "=" * 65)
    print(f"🏁 Benchmark d'Autoformalisation Triple Garde-Fou ({len(selected)} problèmes)")
    print("=" * 65)

    autoform = Autoformalizer()
    results = []

    passed_compilation = 0
    passed_non_vacuity = 0
    passed_round_trip = 0
    fully_certified = 0

    t0 = time.time()

    for idx, prob in enumerate(selected, 1):
        print(f"\n[{idx}/{len(selected)}] [{prob.category}] {prob.name}")
        res = autoform.formalize_problem(prob.text, theorem_name=prob.name, max_attempts=2)
        results.append(res)

        if res.compiles:
            passed_compilation += 1
        if res.non_vacuous:
            passed_non_vacuity += 1
        if res.round_trip_valid:
            passed_round_trip += 1
        if res.is_valid:
            fully_certified += 1
            print(f"  ✨ Déclaration validée : {res.lean_statement}")

    total_time = time.time() - t0

    print("\n" + "=" * 65)
    print("🏆 RÉSULTATS DU BENCHMARK D'AUTOFORMALISATION (PHASE 3)")
    print("=" * 65)
    print(f"Problèmes testés         : {len(selected)}")
    print(f"Garde-fou 1 (Compile)    : {passed_compilation} / {len(selected)} ({passed_compilation/len(selected)*100:.1f}%)")
    print(f"Garde-fou 2 (Non-Vacuité): {passed_non_vacuity} / {len(selected)} ({passed_non_vacuity/len(selected)*100:.1f}%)")
    print(f"Garde-fou 3 (Round-Trip) : {passed_round_trip} / {len(selected)} ({passed_round_trip/len(selected)*100:.1f}%)")
    print(f"TOTALEMENT CERTIFIÉS     : {fully_certified} / {len(selected)} ({fully_certified/len(selected)*100:.1f}%)")
    print(f"Temps total d'exécution  : {total_time:.1f}s (Moyenne : {total_time/len(selected):.1f}s/problème)")
    print("=" * 65)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5, help="Nombre de problèmes à tester")
    args = parser.parse_args()
    run_autoform_benchmark(limit=args.limit)
