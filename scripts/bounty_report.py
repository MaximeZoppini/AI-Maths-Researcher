"""
Bounty & Benchmark Certification Report Generator for AI-Maths-Researcher.
Aggregates attempts, verified theorems, latency, and cost from SQLite DB into BOUNTY_REPORT.md.
"""

import sqlite3
import datetime
from pathlib import Path

DB_PATH = "/tmp/ai_maths_data/attempts.db"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "BOUNTY_REPORT.md"

def generate_report():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Total stats
    cur.execute("SELECT COUNT(*), SUM(success), AVG(duration_ms), SUM(cost_usd) FROM attempts")
    total_attempts, total_success, avg_duration, total_cost = cur.fetchone()
    total_attempts = total_attempts or 0
    total_success = total_success or 0
    avg_duration = avg_duration or 0.0
    total_cost = total_cost or 0.0

    # Solved unique problems
    cur.execute("SELECT DISTINCT problem_name FROM attempts WHERE success = 1")
    solved_problems = [r[0] for r in cur.fetchall()]

    # Total distinct problems
    cur.execute("SELECT COUNT(DISTINCT problem_name) FROM attempts")
    total_problems = cur.fetchone()[0] or 0

    # Per-model stats
    cur.execute("""
        SELECT model, COUNT(*), SUM(success), AVG(duration_ms), SUM(cost_usd)
        FROM attempts
        GROUP BY model
    """)
    model_stats = cur.fetchall()

    # Solved theorems details
    cur.execute("""
        SELECT problem_name, iteration, model, duration_ms, cost_usd, candidate_code, timestamp
        FROM attempts
        WHERE success = 1
        ORDER BY id ASC
    """)
    solved_details = cur.fetchall()

    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    report_lines = [
        "# 🏆 AI-Maths-Researcher — Rapport Officiel de Certification & Bounties",
        "",
        f"> **Généré le** : `{now_str}`  ",
        f"> **Infra de Vérification** : LXC Container 200 (Proxmox 100.90.108.89)  ",
        f"> **Lean 4 / Mathlib** : `v4.34.0` | **Axiomes Admis** : `[propext, Classical.choice, Quot.sound]` (Strict Zero-Sorry)",
        "",
        "---",
        "",
        "## 1. Synthèse Exécutive",
        "",
        "| Métrique | Valeur |",
        "| :--- | :--- |",
        f"| **Problèmes Résolus & Certifiés** | **{len(solved_problems)} / {total_problems}** ({len(solved_problems)/max(1, total_problems)*100:.1f}%) |",
        f"| **Nombre Total de Tentatives** | **{total_attempts}** |",
        f"| **Temps Moyen par Tentative (REPL)** | **{avg_duration:.1f} ms** |",
        f"| **Coût Total Consommé (API LLM)** | **${total_cost:.4f}** |",
        "",
        "---",
        "",
        "## 2. Répartition par Modèle",
        "",
        "| Modèle | Essais | Succès | Taux | Latence Moy. | Coût Total |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for model, attempts, succ, dur, cost in model_stats:
        succ = succ or 0
        dur = dur or 0.0
        cost = cost or 0.0
        rate = (succ / attempts * 100) if attempts else 0.0
        report_lines.append(f"| `{model}` | {attempts} | {succ} | {rate:.1f}% | {dur:.1f} ms | ${cost:.4f} |")

    report_lines.extend([
        "",
        "---",
        "",
        "## 3. Registre des Preuves Formelles Certifiées ('Axiom-Clean')",
        ""
    ])

    for prob_name, iters, model, dur, cost, code, ts in solved_details:
        report_lines.extend([
            f"### 🎯 Théorème : `{prob_name}`",
            f"- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**",
            f"- **Modèle** : `{model}` | **Itération** : {iters} | **Latence REPL** : {dur:.1f} ms | **Coût** : ${cost:.5f}",
            f"- **Timestamp** : `{ts}`",
            "",
            "```lean",
            code.strip(),
            "```",
            ""
        ])

    content = "\n".join(report_lines)
    try:
        OUTPUT_FILE.write_text(content, encoding="utf-8")
        print(f"✨ Rapport généré avec succès dans {OUTPUT_FILE}")
    except PermissionError:
        tmp_target = Path("/tmp/ai_maths_data/BOUNTY_REPORT.md")
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        tmp_target.write_text(content, encoding="utf-8")
        print(f"⚠️ Permissions restreintes : rapport généré dans {tmp_target}")

if __name__ == "__main__":
    generate_report()
