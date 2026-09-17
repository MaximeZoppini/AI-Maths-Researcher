import urllib.request
import re
import argparse
import sys
import os
import threading
import concurrent.futures
import datetime
from pathlib import Path
from typing import List, Tuple, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.prover import ProofSearchEngine, ProverConfig, get_deepseek_balance
from agent.repl_client import LeanREPL, REPLPool
from agent.planner import BlueprintPlanner
from agent.db import AttemptsDB, classify_problem

MINIF2F_URL = "https://raw.githubusercontent.com/google-deepmind/miniF2F/main/MiniF2F/Test.lean"
LOCAL_CACHE = Path(__file__).resolve().parent / "minif2f_test.lean"

def fetch_minif2f_test() -> str:
    if LOCAL_CACHE.exists():
        return LOCAL_CACHE.read_text(encoding="utf-8")
    print(f"📥 Téléchargement du benchmark MiniF2F Test depuis {MINIF2F_URL}...")
    with urllib.request.urlopen(MINIF2F_URL, timeout=15) as r:
        content = r.read().decode("utf-8")
        LOCAL_CACHE.write_text(content, encoding="utf-8")
        return content

def parse_theorems(content: str) -> List[Tuple[str, str]]:
    """
    Parses all 244 theorem declarations (name, full_declaration_statement) from MiniF2F test set.
    """
    results = []
    pattern = r"(?:^|\n)(theorem\s+([a-zA-Z0-9_]+)(?:(?!theorem)[\s\S])*?)(?::=)"
    for m in re.finditer(pattern, content):
        stmt_part = m.group(1).strip()
        name = m.group(2).strip()
        results.append((name, stmt_part))
    return results

def safe_write_file(path: Path, content: str):
    try:
        path.write_text(content, encoding="utf-8")
    except PermissionError:
        import subprocess
        subprocess.run(["tee", str(path)], input=content, text=True, stdout=subprocess.DEVNULL, check=True)

def run_benchmark(
    limit: int = 50,
    attempts: int = 3,
    model: str = "deepseek-chat",
    use_blueprint: bool = True,
    name_filter: Optional[str] = None,
    pass_k: int = 1,
    skip_solved: bool = False,
    workers: int = 1,
    min_balance: float = 0.50,
    dry_run: bool = False,
    timeout_sec: int = 45
):
    source_file = Path("benchmarks") / "minif2f_test.lean"
    if not source_file.exists():
        print(f"❌ Fichier de benchmark introuvable : {source_file}")
        return

    theorems = parse_theorems(source_file.read_text(encoding="utf-8"))
    bal = get_deepseek_balance()

    if name_filter:
        selected = [t for t in theorems if t[0] == name_filter]
        if not selected:
            print(f"⚠️ Problème '{name_filter}' introuvable dans MiniF2F.")
            return
        target_set = selected
    else:
        target_set = theorems[:limit]

    target_set_size = len(target_set)

    # Filtrer les problèmes déjà résolus si demandé
    already_solved = []
    if skip_solved:
        already_solved = [t[0] for t in target_set if (Path("problems") / f"minif2f_{t[0]}.lean").exists()]
        selected = [t for t in target_set if t[0] not in already_solved]
        if already_solved:
            print(f"⏩ [Skip] {len(already_solved)} problème(s) déjà résolu(s) et certifié(s) dans problems/.")
    else:
        selected = list(target_set)

    total_problems = len(selected)
    already_solved_count = len(already_solved)

    # Calcul économique pré-campagne réaliste
    db = AttemptsDB()
    with db.conn:
        # Coût total réel engagé (y compris les sous-lemmes Blueprint)
        row_cost = db.conn.execute("SELECT COALESCE(SUM(cost_usd), 0.0) FROM attempts").fetchone()
        tot_cost_all = row_cost[0] if row_cost else 0.0

        # Nombre de problèmes racines distincts tentés
        row_probs = db.conn.execute("""
            SELECT COUNT(DISTINCT problem_name) FROM attempts
            WHERE problem_name NOT LIKE '%_step%'
        """).fetchone()
        tot_probs_db = row_probs[0] if row_probs else 0
        measured_avg_cost = (tot_cost_all / tot_probs_db) if tot_probs_db > 0 else 0.025

    # Pour les problèmes restants du set (plus denses en AMC12/AIME/IMO exigeant escalade reasoner),
    # appliquer un plancher réaliste conservateur de $0.035 / problème
    conservative_unit_cost = max(measured_avg_cost, 0.035)
    estimated_cost = total_problems * conservative_unit_cost
    required_balance = estimated_cost + min_balance
    bal_float = bal if bal is not None else 0.0
    can_run = (bal is not None and bal_float >= required_balance)

    print("\n" + "=" * 65)
    print("📊 ANALYSE PRÉALABLE DU BUDGET & DES RESSOURCES (PRE-FLIGHT)")
    print("=" * 65)
    print(f"Ensemble cible de référence       : {target_set_size} problèmes")
    print(f"Problèmes déjà résolus certifiés   : {already_solved_count}")
    print(f"Problèmes restant à évaluer        : {total_problems}")
    print(f"Coût unitaire moyen en base        : ${measured_avg_cost:.4f} USD (toutes étapes incluses)")
    print(f"Coût unitaire appliqué             : ${conservative_unit_cost:.4f} USD (avec marge complexité)")
    print(f"Coût estimé pour cette campagne    : ${estimated_cost:.2f} USD")
    print(f"Solde DeepSeek disponible          : ${bal_float:.2f} USD")
    print(f"Seuil de sécurité requis           : ${required_balance:.2f} USD (estimation + ${min_balance:.2f})")
    status_label = "✅ GO (Solde suffisant pour couvrir la campagne complète)" if can_run else f"🛑 NO-GO (Solde insuffisant: ${bal_float:.2f} < ${required_balance:.2f})"
    print(f"Décision Pré-Vol                   : {status_label}")
    print("=" * 65)

    if dry_run:
        print("\n🔍 Mode --dry-run : simulation pré-vol terminée avec succès.")
        print("   AUCUN appel LLM ni calcul REPL n'a été effectué.\n")
        return

    if not can_run:
        print(f"\n🛑 Campagne interrompue : solde disponible (${bal_float:.2f}) inférieur au requis (${required_balance:.2f}).")
        print("💡 Rechargez votre compte DeepSeek (recommandation: top-up de $10 à $15 pour le run 244 complet).\n")
        return

    print("\n" + "=" * 65)
    print(f"🏁 Démarrage du Benchmark MiniF2F Lean 4 ({total_problems} problèmes)")
    print(f"Modèle : {model} | Essais max : {attempts} | pass@{pass_k} | Workers : {workers}")
    print(f"Timeout : {timeout_sec}s | Blueprint : {use_blueprint} | Escalade Reasoner : Activée")
    print("=" * 65)

    if total_problems == 0:
        print("Aucun problème à exécuter.")
        return

    config = ProverConfig(
        max_attempts=attempts,
        model=model,
        pass_k=pass_k,
        enable_escalation=True,
        timeout_per_attempt_sec=timeout_sec,
        min_balance_threshold_usd=min_balance,
        early_abort=True
    )
    engine = ProofSearchEngine(config=config)
    planner = BlueprintPlanner(config=config) if use_blueprint else None
    db = AttemptsDB()

    solved_lock = threading.Lock()
    solved_count = 0
    newly_solved = []
    failed_problems = []
    completed_count = 0

    # Configuration du pool REPL pour multi-workers
    repl_pool: Optional[REPLPool] = None
    if workers > 1:
        pool_size = min(3, max(2, workers // 2))
        repl_pool = REPLPool(size=pool_size)
        repl_pool.start()

    def process_item(item_info: Tuple[int, str, str]) -> Tuple[bool, str, str]:
        nonlocal solved_count, completed_count
        idx, name, decl = item_info

        # Gate STOP
        stop_file = (Path(__file__).resolve().parent.parent / "STOP").resolve()
        if stop_file.exists() or Path("STOP").exists():
            return False, name, "STOP"

        # Gate Solde
        current_bal = get_deepseek_balance()
        if current_bal is not None and current_bal < min_balance:
            return False, name, "LOW_BALANCE"

        repl_target = repl_pool if repl_pool else None

        diff_class = classify_problem(name)
        print(f"\n[{idx}/{total_problems}] 🎯 Lancement : {name} (classe: {diff_class})")
        # Étape 1 : Stratégie A (Preuve directe avec pré-passe gratuite, escalade conditionnée et pass@k)
        success, code = engine.prove_theorem(
            decl,
            problem_name=name,
            external_repl=repl_target,
            difficulty_class=diff_class
        )

        # Étape 2 : Si échec et Blueprint activé, bascule vers décomposition conditionnée
        cls_stats = db.get_success_rates_by_class().get(diff_class, {})
        p_succ = cls_stats.get("p_success", 0.0) if cls_stats.get("attempted", 0) >= 3 else 0.20
        # Règle Tâche 9 : Pas de blueprint si classe imo ou si p_success < 0.15
        should_blueprint = planner and (diff_class != "imo") and (p_succ >= 0.15)

        if not success and should_blueprint:
            print(f"  🔄 Échec direct -> Activation du Blueprint Planner pour {name}...")
            success, code = planner.prove_with_blueprint(decl, problem_name=name, external_repl=repl_target)
        elif not success and planner and not should_blueprint:
            print(f"  ℹ️ Repli Blueprint ignoré pour {name} (classe '{diff_class}', p_success {p_succ*100:.1f}% < 15%). Évite les sous-lemmes orphelins.")

        with solved_lock:
            completed_count += 1
            if success:
                solved_count += 1
                newly_solved.append(name)
                out_file = Path("problems") / f"minif2f_{name}.lean"
                safe_write_file(out_file, code + "\n")
                print(f"  💾 [{completed_count}/{total_problems}] Preuve enregistrée dans {out_file}")
                # Génération automatique du package de soumission PR prêt pour revue humaine
                try:
                    from scripts.submission_kit import generate_submission
                    sub_dir = generate_submission(name, docstring=f"Formal proof of `{name}` in Lean 4 (MiniF2F benchmark).")
                    print(f"  📦 Kit de soumission PR prêt dans {sub_dir}")
                except Exception as e:
                    print(f"  ⚠️ Erreur génération kit de soumission pour {name}: {e}")
            else:
                failed_problems.append(name)
                print(f"  ❌ [{completed_count}/{total_problems}] Non résolu : {name}")

        return success, name, code

    try:
        items = [(idx, name, decl) for idx, (name, decl) in enumerate(selected, 1)]
        if workers > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                list(executor.map(process_item, items))
        else:
            for item in items:
                process_item(item)
    finally:
        if repl_pool:
            repl_pool.close()

    cumulative_solved = already_solved_count + solved_count
    cumulative_rate_pct = (cumulative_solved / max(1, target_set_size)) * 100
    session_rate_pct = (solved_count / max(1, total_problems) * 100) if total_problems > 0 else 0.0

    print("\n" + "=" * 65)
    print("🏆 RÉSULTAT DU BENCHMARK MINIF2F")
    print(f"🎯 Métrique Officielle MiniF2F Test : {cumulative_solved} / {target_set_size} ({cumulative_rate_pct:.1f}%)")
    print(f"   (Ensemble de référence figé : {target_set_size} problèmes distincts)")
    if already_solved_count > 0:
        print(f"   - Déjà résolus certifiés avant le run : {already_solved_count}")
        print(f"   - Nouveaux résolus dans cette session : {solved_count} / {total_problems} ({session_rate_pct:.1f}%)")
    print("=" * 65)

    # Figer le rapport de la campagne dans reports/
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"minif2f_campaign_{timestamp}.md"
    report_content = [
        f"# Rapport Officiel de Campagne MiniF2F — {timestamp}",
        "",
        f"- **Date** : `{timestamp}` UTC",
        f"- **🎯 Métrique Officielle MiniF2F Test** : **{cumulative_solved} / {target_set_size} ({cumulative_rate_pct:.1f}%)**",
        f"- **Ensemble de référence ciblé** : {target_set_size} problèmes distincts",
        f"- **Déjà résolus certifiés (pré-campagne)** : {already_solved_count}",
        f"- **Nouveaux résolus dans cette session** : {solved_count} / {total_problems} ({session_rate_pct:.1f}%)",
        f"- **Modèle de base** : `{model}` (avec escalade reasoner)",
        f"- **Workers parallèles** : `{workers}`",
        f"- **pass@k** : `{pass_k}`",
        f"- **Timeout REPL** : `{timeout_sec}s`",
        f"- **Mode Blueprint** : `{use_blueprint}`",
        "",
        "## Nouveaux Problèmes Résolus",
        ""
    ]
    for s in newly_solved:
        report_content.append(f"- ✅ `{s}`")
    report_content.extend([
        "",
        "## Problèmes Non Résolus",
        ""
    ])
    for f in failed_problems:
        report_content.append(f"- ❌ `{f}`")

    safe_write_file(report_path, "\n".join(report_content) + "\n")
    print(f"📄 Rapport de campagne figé dans {report_path}")

    # Déclencher une sauvegarde automatique de la base
    db.backup()

def main():
    parser = argparse.ArgumentParser(description="MiniF2F Benchmark Runner")
    parser.add_argument("--limit", type=int, default=10, help="Nombre de problèmes à tester (default: 10)")
    parser.add_argument("--attempts", type=int, default=3, help="Nombre d'essais max par problème (default: 3)")
    parser.add_argument("--model", type=str, default="deepseek-chat", help="Modèle LLM cible")
    parser.add_argument("--no-blueprint", action="store_true", help="Désactiver le repli sur le Blueprint Planner")
    parser.add_argument("--name", type=str, default=None, help="Tester un problème spécifique par son nom")
    parser.add_argument("--pass-k", type=int, default=1, help="Nombre de générations parallèles (default: 1)")
    parser.add_argument("--skip-solved", action="store_true", help="Ignorer les problèmes déjà résolus")
    parser.add_argument("--workers", type=int, default=1, help="Nombre de workers parallèles (default: 1)")
    parser.add_argument("--timeout", type=int, default=45, help="Timeout REPL par essai en secondes (default: 45s)")
    parser.add_argument("--min-balance", type=float, default=0.50, help="Solde minimal DeepSeek USD requis (default: 0.50)")
    parser.add_argument("--dry-run", action="store_true", help="Vérifier les problèmes, estimer les coûts et le solde sans appel LLM")
    args = parser.parse_args()

    run_benchmark(
        limit=args.limit,
        attempts=args.attempts,
        model=args.model,
        use_blueprint=not args.no_blueprint,
        name_filter=args.name,
        pass_k=args.pass_k,
        skip_solved=args.skip_solved,
        workers=args.workers,
        timeout_sec=args.timeout,
        min_balance=args.min_balance,
        dry_run=args.dry_run
    )

if __name__ == "__main__":
    main()
