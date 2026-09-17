#!/usr/bin/env python3
"""
CLI Analytics & Reporting for AI-Maths-Researcher.
Displays success rates, iteration counts, token costs, and model performance.
"""

from agent.db import AttemptsDB

def main():
    db = AttemptsDB()
    stats = db.get_summary()

    print("\n" + "=" * 60)
    print("📊 AI-Maths-Researcher — Rapport d'Exécution & Métriques")
    print("=" * 60)

    print(f"Total des tentatives : {stats['total_attempts']}")
    print(f"Tentatives réussies  : {stats['success_count']} ({stats['attempt_success_rate'] * 100:.1f}%)")
    print(f"Problèmes uniques    : {stats['base_problems_count']}")
    print(f"Problèmes résolus    : {stats['solved_base_count']} ({stats['base_solve_rate'] * 100:.1f}%)")
    print(f"Sous-lemmes explorés : {stats['sub_lemmas_count']} (résolus: {stats['solved_sub_lemmas_count']})")
    print(f"Temps moyen REPL     : {stats['avg_duration_ms']:.1f} ms")
    print(f"Coût total API       : ${stats['total_cost_usd']:.4f}")

    if stats["models"]:
        print("\n" + "-" * 60)
        print(f"{'Modèle':<25} {'Essais':<10} {'Succès':<10} {'Taux':<10} {'Coût':<10}")
        print("-" * 60)
        for m in stats["models"]:
            print(f"{m['model']:<25} {m['total']:<10} {m['successes']:<10} {m['rate']*100:.1f}%     ${m['cost']:.4f}")

    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
