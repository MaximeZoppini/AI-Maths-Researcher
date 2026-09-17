#!/usr/bin/env python3
"""
Mathlib Missing Lemmas Miner for AI-Maths-Researcher.
Mines actual LLM compiler errors from attempts.db to discover missing or hallucinated lemmas.
Queries Loogle to determine if an equivalent lemma exists in Mathlib.
Generates an analytical Markdown report for human formalization decision-making.
"""

import sys
import re
import datetime
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.db import DB_PATH, AttemptsDB
from agent.retrieval import PremiseRetriever

ROOT_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT_DIR / "reports"

def safe_write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(content, encoding="utf-8")
    except PermissionError:
        import subprocess
        subprocess.run(["sh", "-c", f"cat > '{path}'"], input=content, text=True, check=True)

def mine_mathlib_gaps(top_n: int = 20, check_loogle: bool = True) -> Path:
    db = AttemptsDB()
    with db.conn:
        rows = db.conn.execute("""
            SELECT compiler_errors, problem_name 
            FROM attempts 
            WHERE compiler_errors IS NOT NULL
        """).fetchall()

    id_counts = Counter()
    id_problems = defaultdict(set)

    pattern = r"[uU]nknown (?:identifier|constant)\s+[`']([a-zA-Z0-9_.']+)['`]"

    # Heuristic filter for noise words that are compiler syntax glitches rather than lemmas
    noise_words = {"the", "now", "requires", "looking", "this", "in", "unless"}

    for r in rows:
        err = r["compiler_errors"] or ""
        p_name = r["problem_name"]
        matches = re.findall(pattern, err)
        for m in matches:
            clean = m.strip("'`")
            if clean.lower() in noise_words:
                continue
            # Skip short single-character variables
            if len(clean) <= 2:
                continue
            id_counts[clean] += 1
            id_problems[clean].add(p_name)

    top_items = id_counts.most_common(top_n)
    print(f"\n⛏️  Extraction terminée : {len(id_counts)} identifiants distincts trouvés sur {len(rows)} tentatives.")
    print(f"🔍 Analyse des {len(top_items)} identifiants les plus fréquents via Loogle...\n")

    retriever = PremiseRetriever(timeout_sec=5.0) if check_loogle else None

    results = []
    for rank, (ident, count) in enumerate(top_items, 1):
        problems = sorted(list(id_problems[ident]))
        loogle_status = "non vérifié"
        loogle_note = "-"

        if retriever:
            try:
                hits = retriever.query_loogle(ident, limit=3)
                if hits:
                    match_exact = any(h.name == ident or h.name.endswith(f".{ident}") for h in hits)
                    if match_exact:
                        loogle_status = "probable"
                        loogle_note = f"`{hits[0].name}`"
                    else:
                        loogle_status = "approchant"
                        loogle_note = f"`{hits[0].name}`"
                else:
                    loogle_status = "absent"
                    loogle_note = "Aucun lemme équivalent trouvé (candidat trou Mathlib)"
            except Exception as e:
                loogle_status = "inconnu"
                loogle_note = f"Erreur requête: {e}"

        results.append({
            "rank": rank,
            "ident": ident,
            "count": count,
            "status": loogle_status,
            "note": loogle_note,
            "problems": problems
        })
        print(f"  [{rank}/{len(top_items)}] `{ident}` ({count}x) -> Loogle: {loogle_status}")

    # Generate Markdown report
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_file = REPORTS_DIR / f"mathlib_gaps_{timestamp}.md"

    lines = [
        f"# ⛏️ Rapport de Détection des Trous & Lemmes Manquants dans Mathlib",
        "",
        f"> **Généré le** : `{timestamp}` UTC  ",
        f"> **Source de données** : `data/attempts.db` ({len(rows)} tentatives analysées)  ",
        f"> **Objet** : Identification des lemmes manquants ou hallucinés par les modèles pour sélection humaine de PRs.",
        "",
        "---",
        "",
        "## 1. Top Candidats de Lemmes Manquants / Hallucinés",
        "",
        "| Rang | Identifiant Halluciné / Demandé | Fréquence | Statut Loogle | Équivalent / Remarques | Problèmes Déclencheurs |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for item in results:
        probs_str = ", ".join(f"`{p}`" for p in item["problems"][:3])
        if len(item["problems"]) > 3:
            probs_str += f" (+{len(item['problems']) - 3})"
        status_badge = {
            "absent": "🔴 **absent** (trou Mathlib potentiel)",
            "probable": "🟢 **probable** (existe sous ce nom)",
            "approchant": "🟡 **approchant** (variante existante)",
            "inconnu": "⚪ **inconnu**"
        }.get(item["status"], item["status"])

        lines.append(
            f"| {item['rank']} | `{item['ident']}` | **{item['count']}** | {status_badge} | {item['note']} | {probs_str} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 2. Recommandations pour la Contribution Humaine",
        "",
        "1. **Candidats `absent`** : Ces lemmes ont été inférés de manière récurrente par les LLMs mais n'existent pas dans Mathlib. Ce sont les cibles prioritaires pour une formalisation artisanale et une PR crédible.",
        "2. **Candidats `approchant`** : Le concept existe mais le modèle s'est trompé de nom de tactique ou de nommage de lemme. Ces informations servent à enrichir le prompt de contexte ou les alias du `PremiseRetriever`.",
        "",
        "> ⚠️ **RÈGLE STRICTE** : Aucune preuve ni PR n'est générée automatiquement depuis ce rapport. La décision et la formalisation restent sous contrôle humain."
    ])

    safe_write_text(report_file, "\n".join(lines) + "\n")
    print(f"\n📄 Rapport de synthèse généré avec succès : {report_file}")
    return report_file

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Mine Mathlib missing lemma candidates from attempts.db")
    parser.add_argument("--top", type=int, default=20, help="Nombre de candidats à analyser (default: 20)")
    parser.add_argument("--no-loogle", action="store_true", help="Désactiver l'interrogation Loogle")
    args = parser.parse_args()

    mine_mathlib_gaps(top_n=args.top, check_loogle=not args.no_loogle)

if __name__ == "__main__":
    main()
