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
    noise_words = {
        "the", "now", "requires", "looking", "this", "in", "unless",
        "note", "here", "then", "have", "let", "show", "from", "case",
        "with", "intro", "by", "exact", "apply", "using"
    }

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
            # 1. Filtrer les noms d'hypothèses locales (hy1, hc2... : minuscule + court + sans namespace)
            if "." not in clean:
                if re.match(r"^(?:h|ih)[a-z0-9_]{1,4}$", clean, re.IGNORECASE):
                    continue
                if len(clean) <= 3 and clean.islower():
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
        matched_name = None

        if retriever:
            try:
                # 1. Requête sur le nom exact
                hits_exact = retriever.query_loogle(ident, limit=5)
                exact_match = None
                for h in hits_exact:
                    if h.name == ident or h.name.endswith(f".{ident}"):
                        exact_match = h.name
                        break

                if exact_match:
                    loogle_status = "probable"
                    loogle_note = f"`{exact_match}` (existe sous ce nom exact)"
                else:
                    # 2. Requête sur le dernier segment si namespace (ex: Real.sq_abs -> sq_abs)
                    last_seg = ident.split(".")[-1] if "." in ident else None
                    seg_match = None
                    if last_seg and last_seg != ident:
                        hits_seg = retriever.query_loogle(last_seg, limit=5)
                        for h in hits_seg:
                            if h.name == last_seg or h.name.endswith(f".{last_seg}"):
                                seg_match = h.name
                                break

                    if seg_match:
                        loogle_status = "existe_sous_autre_nom"
                        loogle_note = f"`{seg_match}` (existe sans le préfixe `{ident.rsplit('.', 1)[0]}`)"
                        matched_name = seg_match
                    elif hits_exact:
                        loogle_status = "approchant"
                        loogle_note = f"`{hits_exact[0].name}` (variante trouvée)"
                    else:
                        loogle_status = "introuvable_via_loogle"
                        loogle_note = "Aucun lemme équivalent trouvé via Loogle"
            except Exception as e:
                loogle_status = "inconnu"
                loogle_note = f"Erreur requête: {e}"

        results.append({
            "rank": rank,
            "ident": ident,
            "count": count,
            "status": loogle_status,
            "matched_name": matched_name,
            "note": loogle_note,
            "problems": problems
        })
        display_status = f"{loogle_status} ({matched_name})" if matched_name else loogle_status
        print(f"  [{rank}/{len(top_items)}] `{ident}` ({count}x) -> Loogle: {display_status}")

    # Nettoyage des anciens rapports trompeurs
    for old_report in REPORTS_DIR.glob("mathlib_gaps_*.md"):
        try:
            old_report.unlink()
            print(f"🗑️  Ancien rapport supprimé : {old_report.name}")
        except Exception:
            import subprocess
            subprocess.run(["rm", "-f", str(old_report)], check=False)
            print(f"🗑️  Ancien rapport supprimé via sh : {old_report.name}")

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

        if item["status"] == "existe_sous_autre_nom":
            status_badge = f"🔵 **existe_sous_autre_nom** (`{item['matched_name']}`)"
        elif item["status"] == "introuvable_via_loogle":
            status_badge = "🔴 **introuvable_via_loogle** (trou Mathlib potentiel)"
        elif item["status"] == "probable":
            status_badge = "🟢 **probable** (existe sous ce nom exact)"
        elif item["status"] == "approchant":
            status_badge = "🟡 **approchant** (variante existante)"
        else:
            status_badge = "⚪ **inconnu**"

        lines.append(
            f"| {item['rank']} | `{item['ident']}` | **{item['count']}** | {status_badge} | {item['note']} | {probs_str} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 2. Recommandations pour la Contribution Humaine",
        "",
        "1. **Candidats `introuvable_via_loogle`** : Ces lemmes ont été inférés de manière récurrente par les LLMs mais sont introuvables via Loogle. Ce sont des candidats pour une formalisation artisanale et une PR crédible (après vérification manuelle dans Mathlib).",
        "2. **Candidats `existe_sous_autre_nom`** : Le lemme existe déjà dans Mathlib sous un autre nom ou sans le namespace erroné (ex: `Real.sq_abs` -> `sq_abs`). **Ne PAS créer de PR pour ces lemmes** : il s'agit d'un problème de prompting ou de retrieval, pas d'un manque dans Mathlib.",
        "3. **Candidats `probable` & `approchant`** : Le concept ou le nom exact existe déjà dans Mathlib. Ces lemmes servent à enrichir le prompt de contexte ou les alias du `PremiseRetriever`.",
        "",
        "> ⚠️ **RÈGLE STRICTE** : Aucune preuve ni PR n'est générée automatiquement depuis ce rapport. Loogle qui ne trouve pas ne garantit pas à 100 % l'absence du lemme (d'où le statut `introuvable_via_loogle`). La décision et la formalisation restent sous contrôle humain."
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
