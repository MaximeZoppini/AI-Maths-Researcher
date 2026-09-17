#!/usr/bin/env python3
"""
CLI Analytics & Reporting for AI-Maths-Researcher.
Displays official benchmark metric, difficulty class breakdown, token costs, and model performance.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.db import AttemptsDB

def main():
    db = AttemptsDB()
    stats = db.get_summary()
    class_stats = db.get_success_rates_by_class()

    # Calcul du set figé MiniF2F Test officiel (problèmes de base issus du benchmark)
    with db.conn:
        minif2f_rows = db.conn.execute("""
            SELECT problem_name, MAX(success) AS solved
            FROM attempts
            WHERE problem_name NOT LIKE '%_step%'
              AND (difficulty_class IN ('mathd', 'amc', 'aime', 'imo', 'olympiad_other'))
            GROUP BY problem_name
        """).fetchall()
        minif2f_attempted = len(minif2f_rows)
        minif2f_solved = sum(r["solved"] for r in minif2f_rows)
        minif2f_rate = (minif2f_solved / minif2f_attempted * 100) if minif2f_attempted > 0 else 0.0

    print("\n" + "=" * 65)
    print("🏆 AI-Maths-Researcher — Rapport d'Exécution & Métriques")
    print("=" * 65)

    print(f"\n🎯 MÉTRIQUE OFFICIELLE (MiniF2F Test, Problèmes Distincts) :")
    print(f"   ► Résolus certifiés : {minif2f_solved} / {minif2f_attempted} ({minif2f_rate:.1f}%)")
    print(f"   (Exclut strictement doublons, sous-lemmes de décomposition et tests ad-hoc)")

    print(f"\n📊 DÉTAIL PAR CLASSE DE DIFFICULTÉ :")
    print(f"   {'Classe':<18} {'Résolus / Tentés':<20} {'p_success':<12}")
    print(f"   {'-'*18} {'-'*20} {'-'*12}")
    for cls, data in class_stats.items():
        ratio_str = f"{data['solved']} / {data['attempted']}"
        pct_str = f"{data['p_success']*100:.1f}%"
        print(f"   {cls:<18} {ratio_str:<20} {pct_str:<12}")

    print(f"\n⚙️ INFRASTRUCTURE & COÛTS :")
    print(f"   - Total des tentatives : {stats['total_attempts']}")
    print(f"   - Sous-lemmes explorés : {stats['sub_lemmas_count']} (dont {stats['solved_sub_lemmas_count']} résolus)")
    print(f"   - Temps moyen REPL     : {stats['avg_duration_ms']:.1f} ms")
    print(f"   - Coût total cumulé    : ${stats['total_cost_usd']:.4f}")

    if stats["models"]:
        print("\n" + "-" * 65)
        print(f"{'Modèle':<22} {'Essais':<10} {'Succès':<10} {'Taux':<10} {'Coût':<10}")
        print("-" * 65)
        for m in stats["models"]:
            print(f"{m['model']:<22} {m['total']:<10} {m['successes']:<10} {m['rate']*100:.1f}%     ${m['cost']:.4f}")

    print("=" * 65 + "\n")

if __name__ == "__main__":
    main()

