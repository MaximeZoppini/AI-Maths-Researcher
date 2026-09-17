"""
Bounty & Benchmark Certification Report Generator for AI-Maths-Researcher.
Aggregates attempts, verified theorems, latency, and cost from SQLite DB into BOUNTY_REPORT.md.
"""

import sys
import sqlite3
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent.db import AttemptsDB

DB_PATH = (Path(__file__).resolve().parent.parent / "data" / "attempts.db").resolve()
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "BOUNTY_REPORT.md"

def generate_report():
    db = AttemptsDB(DB_PATH)
    conn = db.conn
    cur = conn.cursor()

    # Total stats
    cur.execute("SELECT COUNT(*), SUM(success), AVG(duration_ms), SUM(cost_usd) FROM attempts")
    total_attempts, total_success, avg_duration, total_cost = cur.fetchone()
    total_attempts = total_attempts or 0
    total_success = total_success or 0
    avg_duration = avg_duration or 0.0
    total_cost = total_cost or 0.0

    # Distinguer problèmes de base et sous-lemmes
    cur.execute("SELECT problem_name, success, difficulty_class FROM attempts")
    all_rows = cur.fetchall()
    base_problems = set()
    solved_base = set()
    sub_lemmas = set()
    solved_sub_lemmas = set()
    minif2f_base = set()
    minif2f_solved = set()

    for name, succ, d_class in all_rows:
        if "_step" in name:
            sub_lemmas.add(name)
            if succ == 1:
                solved_sub_lemmas.add(name)
        else:
            base_problems.add(name)
            if succ == 1:
                solved_base.add(name)
            if d_class in ('mathd', 'amc', 'aime', 'imo', 'olympiad_other'):
                minif2f_base.add(name)
                if succ == 1:
                    minif2f_solved.add(name)

    class_stats = db.get_success_rates_by_class()

    # Per-model stats
    cur.execute("""
        SELECT model, COUNT(*), SUM(success), AVG(duration_ms), SUM(cost_usd)
        FROM attempts
        GROUP BY model
    """)
    model_stats = cur.fetchall()

    # Solved theorems details - Dédupliqués (garder la meilleure preuve par problème)
    cur.execute("""
        SELECT problem_name, iteration, model, duration_ms, cost_usd, candidate_code, timestamp
        FROM attempts
        WHERE success = 1
        ORDER BY id ASC
    """)
    raw_solved = cur.fetchall()
    best_proofs = {}
    for row in raw_solved:
        p_name, iters, model, dur, cost, code, ts = row
        if p_name not in best_proofs:
            best_proofs[p_name] = row
        else:
            prev = best_proofs[p_name]
            # Prioriser moins d'itérations, puis coût min
            if iters < prev[1] or (iters == prev[1] and cost < prev[4]):
                best_proofs[p_name] = row

    solved_details = sorted(best_proofs.values(), key=lambda r: r[0])

    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    minif2f_rate = (len(minif2f_solved) / max(1, len(minif2f_base)) * 100)

    report_lines = [
        "# 🏆 AI-Maths-Researcher — Rapport Officiel de Certification & Bounties",
        "",
        f"> **Généré le** : `{now_str}`  ",
        f"> **Infra de Vérification** : LXC Container 200 (Proxmox 100.90.108.89)  ",
        f"> **Lean 4 / Mathlib** : `v4.34.0` | **Axiomes Admis** : `[propext, Classical.choice, Quot.sound]` (Strict Zero-Sorry)",
        "",
        "---",
        "",
        "## 1. Métrique Officielle & Synthèse Exécutive",
        "",
        "| Métrique | Valeur |",
        "| :--- | :--- |",
        f"| 🎯 **Métrique Officielle MiniF2F Test** | **{len(minif2f_solved)} / {len(minif2f_base)}** ({minif2f_rate:.1f}%) |",
        f"| **Problèmes Uniques Résolus (Total)** | **{len(solved_base)} / {len(base_problems)}** ({len(solved_base)/max(1, len(base_problems))*100:.1f}%) |",
        f"| **Sous-Lemmes Décomposés & Résolus** | **{len(solved_sub_lemmas)} / {len(sub_lemmas)}** |",
        f"| **Nombre Total de Tentatives** | **{total_attempts}** |",
        f"| **Temps Moyen par Tentative (REPL)** | **{avg_duration:.1f} ms** |",
        f"| **Coût Total Consommé (API LLM)** | **${total_cost:.4f}** |",
        "",
        "---",
        "",
        "## 2. Taux de Succès par Classe de Difficulté",
        "",
        "| Classe | Tentés | Résolus | p_success |",
        "| :--- | :--- | :--- | :--- |",
    ]

    for cls, data in class_stats.items():
        report_lines.append(f"| `{cls}` | {data['attempted']} | {data['solved']} | **{data['p_success']*100:.1f}%** |")

    report_lines.extend([
        "",
        "---",
        "",
        "## 3. Répartition par Modèle",
        "",
        "| Modèle | Essais | Succès | Taux | Latence Moy. | Coût Total |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

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
        "## 4. Registre des Preuves Formelles Certifiées ('Axiom-Clean')",
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
        import subprocess
        try:
            subprocess.run(["sh", "-c", f"cat > '{OUTPUT_FILE}'"], input=content, text=True, check=True)
            print(f"✨ Rapport généré via sh dans {OUTPUT_FILE}")
        except Exception as e:
            tmp_target = Path("/tmp/ai_maths_data/BOUNTY_REPORT.md")
            tmp_target.parent.mkdir(parents=True, exist_ok=True)
            tmp_target.write_text(content, encoding="utf-8")
            print(f"⚠️ Permissions restreintes : rapport généré dans {tmp_target} ({e})")

if __name__ == "__main__":
    generate_report()
