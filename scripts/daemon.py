#!/usr/bin/env python3
"""
Autonomous Production Daemon for AI-Maths-Researcher.
Safely processes theorem formalization queue with strict economic and verification gates:
- Gate 1: Kill-switch 'STOP' file
- Gate 2: DeepSeek API minimum balance ($0.50 threshold)
- Gate 3: Anchored absolute SQLite DB path
- Gate 4: Zero-Sorry #print axioms verification on LXC 200
- Gate 5: Security isolation (No external web scraping, no automatic external PRs)
"""

import argparse
import sys
import time
import os
import subprocess
import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.db import AttemptsDB
from agent.targets import Target, load_targets, save_targets, config_for
from agent.prover import ProofSearchEngine, get_deepseek_balance
from agent.planner import BlueprintPlanner
from agent.verifier import RemoteProdVerifier
from scripts.bounty_report import generate_report

ROOT_DIR = Path(__file__).resolve().parent.parent
QUEUE_PATH = ROOT_DIR / "targets" / "queue.yaml"
REGISTRY_PATH = ROOT_DIR / "targets" / "registry.yaml"
STOP_FILE = ROOT_DIR / "STOP"
PROBLEMS_DIR = ROOT_DIR / "problems"

def safe_write_file(path: Path, content: str):
    try:
        path.write_text(content, encoding="utf-8")
    except PermissionError:
        subprocess.run(["sh", "-c", f"cat > '{path}'"], input=content, text=True, check=True)

def git_commit_proof(problem_name: str, cost: float):
    try:
        subprocess.run(["git", "add", "problems/", "targets/queue.yaml", "BOUNTY_REPORT.md", "data/backups/"], cwd=str(ROOT_DIR), check=True)
        msg = f"feat(daemon): certifie {problem_name} sans sorry (coût: ${cost:.4f})"
        subprocess.run(["git", "commit", "-m", msg], cwd=str(ROOT_DIR), check=True)
        print(f"📦 Commit Git créé avec succès : '{msg}'")
    except Exception as e:
        print(f"⚠️ Erreur lors du commit Git : {e}")

def run_daemon(
    interval_sec: int = 30,
    min_balance_usd: float = 0.50,
    max_session_cost_usd: float = 5.00,
    run_once: bool = False,
    auto_commit: bool = True
):
    print("\n" + "=" * 70)
    print("🤖 AI-Maths-Researcher — Démarrage du Daemon de Production Autonome")
    print(f"Racine du projet : {ROOT_DIR}")
    print(f"File d'attente    : {QUEUE_PATH}")
    print(f"Seuil solde API  : ${min_balance_usd:.2f} USD | Plafond session : ${max_session_cost_usd:.2f} USD")
    print(f"Kill-switch file : {STOP_FILE}")
    print("=" * 70 + "\n")

    db = AttemptsDB()
    verifier = RemoteProdVerifier()
    session_cost = 0.0

    while True:
        # GATE 1: Kill-Switch STOP
        if STOP_FILE.exists():
            print("🛑 GATE 1 DÉCLENCHÉE : Fichier 'STOP' détecté. Arrêt d'urgence propre du daemon.")
            break

        # GATE 2: Solde API DeepSeek
        balance = get_deepseek_balance()
        if balance is not None:
            print(f"💳 Solde DeepSeek en direct : ${balance:.2f} USD")
            if balance < min_balance_usd:
                print(f"🛑 GATE 2 DÉCLENCHÉE : Solde insuffisant (${balance:.2f} < ${min_balance_usd:.2f}). Arrêt de sécurité.")
                break
        else:
            print("ℹ️ Solde DeepSeek non accessible ou clé API absente.")

        # GATE 3: Plafond de coût de la session
        if session_cost >= max_session_cost_usd:
            print(f"🛑 GATE 3 DÉCLENCHÉE : Plafond session de ${max_session_cost_usd:.2f} atteint. Arrêt propre.")
            break

        # Watcher whitelisté (throttlé 24h par défaut)
        try:
            from agent.watcher import check_watchlist
            new_watched = check_watchlist()
            if new_watched:
                print(f"👀 Watcher : {len(new_watched)} nouvelle(s) cible(s) en attente de validation ajoutée(s) au registre.")
        except Exception as e:
            print(f"⚠️ Erreur watcher : {e}")

        # GATE 4: File d'attente non vide
        if not QUEUE_PATH.exists():
            print(f"ℹ️ Aucun fichier de file {QUEUE_PATH}.")
            if run_once:
                break
            time.sleep(interval_sec)
            continue

        queue = load_targets(QUEUE_PATH)
        if not queue:
            print("💤 File d'attente vide.")
            if run_once:
                print("🏁 Mode --once : fin d'exécution du daemon.")
                break
            print(f"En attente de nouvelles cibles ({interval_sec}s)...")
            time.sleep(interval_sec)
            continue

        # Filtrer les cibles vérifiées
        verified_queue = [t for t in queue if t.verified]
        unverified_in_queue = [t for t in queue if not t.verified]
        if unverified_in_queue:
            print(f"⚠️ [Sauté] {len(unverified_in_queue)} cible(s) non vérifiée(s) ignorée(s) (ex: '{unverified_in_queue[0].name}', verified: false).")
            print("   RÈGLE ABSOLUE : Seul l'utilisateur passe 'verified: true' à la main. Le daemon ne les traite pas.")

        if not verified_queue:
            print("💤 Aucune cible vérifiée dans la file d'attente.")
            if run_once:
                print("🏁 Mode --once : fin d'exécution du daemon.")
                break
            print(f"En attente de validation humaine ({interval_sec}s)...")
            time.sleep(interval_sec)
            continue

        # Extraire la première cible vérifiée prioritaire
        current_target = verified_queue[0]
        print("\n" + "-" * 70)
        print(f"🎯 Prise en charge de la cible : '{current_target.name}'")
        print(f"Type : {current_target.kind} | Classe : {current_target.difficulty_class} | Valeur : ${current_target.value_usd}")
        print("-" * 70)

        # Calcul de p_success empirique et configuration de recherche
        class_stats = db.get_success_rates_by_class()
        cls_data = class_stats.get(current_target.difficulty_class)
        p_succ = cls_data["p_success"] if cls_data else 0.20
        config = config_for(current_target, p_succ)
        config.min_balance_threshold_usd = min_balance_usd

        engine = ProofSearchEngine(config=config)
        planner = BlueprintPlanner(config=config) if current_target.kind in ("bounty", "mathlib") else None

        cost_before = db.get_summary()["total_cost_usd"]

        # Exécution de la recherche de preuve
        success, proof_code = engine.prove_theorem(
            theorem_decl=current_target.statement,
            problem_name=current_target.name,
            difficulty_class=current_target.difficulty_class
        )

        if not success and planner:
            print(f"  🔄 Repli sur décomposition Blueprint pour {current_target.name}...")
            success, proof_code = planner.prove_with_blueprint(
                theorem_decl=current_target.statement,
                problem_name=current_target.name
            )

        cost_after = db.get_summary()["total_cost_usd"]
        item_cost = max(0.0, cost_after - cost_before)
        session_cost += item_cost

        # Traitement du résultat
        if success:
            print(f"\n✨ Preuve trouvée pour '{current_target.name}' ! Vérification finale en prod LXC...")
            prod_audit = verifier.verify_file_content(proof_code, temp_name=f"{current_target.name}.lean")

            if prod_audit.success:
                print(f"🏆 CERTIFICATION CONFIRMÉE PAR LE JUGE FINAL (Zero-Sorry, axiomes standards).")
                PROBLEMS_DIR.mkdir(parents=True, exist_ok=True)
                out_path = PROBLEMS_DIR / f"{current_target.name}.lean"
                safe_write_file(out_path, proof_code + "\n")
                print(f"💾 Fichier de preuve enregistré dans {out_path}")

                # Retirer la cible de la file
                remaining = queue[1:]
                save_targets(QUEUE_PATH, remaining)
                print(f"🗑️ Cible '{current_target.name}' retirée de la file ({len(remaining)} restantes).")

                # Mise à jour des rapports officiels
                generate_report()
                db.backup()

                if auto_commit:
                    git_commit_proof(current_target.name, item_cost)
            else:
                print(f"❌ Rejet par le Juge Final : {prod_audit.error_message}")
        else:
            print(f"\n❌ Échec de résolution pour '{current_target.name}'.")
            # En cas d'échec sur benchmark, déplacer en fin de file
            remaining = queue[1:] + [current_target]
            save_targets(QUEUE_PATH, remaining)
            print(f"🔄 Cible reportée en fin de file.")

        # Affichage du résumé d'itération
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print("\n" + "=" * 70)
        print(f"📊 RÉSUMÉ DAEMON [{now_str}]")
        print(f"Cible traitée   : {current_target.name} (Succès: {success})")
        print(f"Coût itération  : ${item_cost:.4f} USD | Coût session : ${session_cost:.4f} USD")
        rem_bal = get_deepseek_balance()
        if rem_bal is not None:
            print(f"Solde restant   : ${rem_bal:.2f} USD")
        print("=" * 70 + "\n")

        if run_once:
            print("🏁 Mode --once : fin d'exécution du daemon.")
            break

        time.sleep(5)

def main():
    parser = argparse.ArgumentParser(description="AI-Maths-Researcher Production Daemon")
    parser.add_argument("--interval", type=int, default=30, help="Intervalle de veille en secondes (default: 30)")
    parser.add_argument("--min-balance", type=float, default=0.50, help="Solde minimal DeepSeek USD (default: 0.50)")
    parser.add_argument("--max-cost", type=float, default=5.00, help="Plafond de dépense total de la session (default: 5.00)")
    parser.add_argument("--once", action="store_true", help="Traiter un problème de la file puis s'arrêter")
    parser.add_argument("--no-commit", action="store_true", help="Désactiver le commit git automatique")
    args = parser.parse_args()

    run_daemon(
        interval_sec=args.interval,
        min_balance_usd=args.min_balance,
        max_session_cost_usd=args.max_cost,
        run_once=args.once,
        auto_commit=not args.no_commit
    )

if __name__ == "__main__":
    main()
