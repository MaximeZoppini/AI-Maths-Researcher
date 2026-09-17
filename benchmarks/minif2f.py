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
from agent.db import AttemptsDB

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
    Parses theorem declarations (name, full_declaration_statement).
    """
    pattern = r"(theorem\s+([a-zA-Z0-9_]+)[\s\S]*?:=\s*by\s*\n\s*sorry)"
    matches = re.findall(pattern, content)
    
    results = []
    for full, name in matches:
        stmt_part = full.split(":=")[0].strip()
        results.append((name, stmt_part))
    return results

def safe_write_file(path: Path, content: str):
    try:
        path.write_text(content, encoding="utf-8")
    except PermissionError:
        import subprocess
        subprocess.run(["sh", "-c", f"cat > '{path}'"], input=content, text=True, check=True)

def run_benchmark(
    limit: int = 50,
    attempts: int = 3,
    model: str = "deepseek-chat",
    use_blueprint: bool = True,
    name_filter: Optional[str] = None,
    pass_k: int = 1,
    skip_solved: bool = False,
    workers: int = 1,
    min_balance: float = 0.50
):
    # 0. Garde-fou Solde API initial
    bal = get_deepseek_balance()
    if bal is not None:
        print(f"💳 Solde DeepSeek vérifié : ${bal:.2f} USD")
        if bal < min_balance:
            print(f"🛑 Solde insuffisant (${bal:.2f} < seuil minimal ${min_balance:.2f}). Campagne annulée.")
            return
    else:
        print("ℹ️ Clé DeepSeek non configurée ou solde non consultable.")

    content = fetch_minif2f_test()
    theorems = parse_theorems(content)
    
    if name_filter:
        selected = [t for t in theorems if t[0] == name_filter]
        if not selected:
            print(f"⚠️ Problème '{name_filter}' introuvable dans MiniF2F.")
            return
    else:
        selected = theorems[:limit]

    # Filtrer les problèmes déjà résolus si demandé
    if skip_solved:
        filtered = []
        for name, decl in selected:
            out_file = Path("problems") / f"minif2f_{name}.lean"
            if out_file.exists():
                print(f"⏩ [Skip] '{name}' déjà résolu et certifié ({out_file.name}).")
            else:
                filtered.append((name, decl))
        selected = filtered

    total_problems = len(selected)
    print("\n" + "=" * 65)
    print(f"🏁 Démarrage du Benchmark MiniF2F Lean 4 ({total_problems} problèmes)")
    print(f"Modèle : {model} | Essais max : {attempts} | pass@{pass_k} | Workers : {workers}")
    print(f"Blueprint : {use_blueprint} | Escalade Reasoner : Activée | Seuil Budget : ${min_balance:.2f}")
    print("=" * 65)

    if total_problems == 0:
        print("Aucun problème à exécuter.")
        return

    config = ProverConfig(
        max_attempts=attempts,
        model=model,
        pass_k=pass_k,
        enable_escalation=True,
        timeout_per_attempt_sec=25,
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

        print(f"\n[{idx}/{total_problems}] 🎯 Lancement : {name}")
        # Étape 1 : Stratégie A (Preuve directe avec escalade raisonnée et pass@k)
        success, code = engine.prove_theorem(decl, problem_name=name, external_repl=repl_target)
        
        # Étape 2 : Si échec et Blueprint activé, bascule vers décomposition
        if not success and planner:
            print(f"  🔄 Échec direct -> Activation du Blueprint Planner pour {name}...")
            success, code = planner.prove_with_blueprint(decl, problem_name=name, external_repl=repl_target)

        with solved_lock:
            completed_count += 1
            if success:
                solved_count += 1
                newly_solved.append(name)
                out_file = Path("problems") / f"minif2f_{name}.lean"
                safe_write_file(out_file, code + "\n")
                print(f"  💾 [{completed_count}/{total_problems}] Preuve enregistrée dans {out_file}")
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

    rate_pct = (solved_count / max(1, total_problems)) * 100
    print("\n" + "=" * 65)
    print("🏆 RÉSULTAT DE LA CAMPAGNE MINIF2F")
    print(f"🎯 Métrique Officielle MiniF2F Test : {solved_count} / {total_problems} ({rate_pct:.1f}%)")
    print(f"   (Évaluation sur set figé de problèmes distincts)")
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
        f"- **Métrique Officielle** : **{solved_count} / {total_problems} ({rate_pct:.1f}%)**",
        f"- **Modèle de base** : `{model}` (avec escalade reasoner)",
        f"- **Workers parallèles** : `{workers}`",
        f"- **pass@k** : `{pass_k}`",
        f"- **Mode Blueprint** : `{use_blueprint}`",
        f"- **Problèmes évalués** : {total_problems}",
        f"- **Résolus certifiés** : {solved_count}",
        "",
        "## Problèmes Résolus",
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
    parser.add_argument("--min-balance", type=float, default=0.50, help="Solde minimal DeepSeek USD requis (default: 0.50)")
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
        min_balance=args.min_balance
    )

if __name__ == "__main__":
    main()
