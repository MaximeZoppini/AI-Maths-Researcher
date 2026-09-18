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
from agent.prover import (
    ProofSearchEngine,
    get_deepseek_balance,
    is_deepseek_offpeak,
    get_next_offpeak_window_utc,
    get_next_offpeak_window_str
)
from agent.autoformalizer import Autoformalizer
from agent.planner import BlueprintPlanner
from agent.verifier import RemoteProdVerifier
from agent.notifier import TelegramNotifier
from scripts.bounty_report import generate_report
from scripts.dashboard import generate_dashboard

ROOT_DIR = Path(__file__).resolve().parent.parent
QUEUE_PATH = ROOT_DIR / "targets" / "queue.yaml"
REGISTRY_PATH = ROOT_DIR / "targets" / "registry.yaml"
STOP_FILE = ROOT_DIR / "STOP"
PROBLEMS_DIR = ROOT_DIR / "problems"

def safe_write_file(path: Path, content: str):
    try:
        path.write_text(content, encoding="utf-8")
    except PermissionError:
        subprocess.run(["tee", str(path)], input=content, text=True, stdout=subprocess.DEVNULL, check=True)

def git_commit_proof(problem_name: str, cost: float):
    try:
        subprocess.run(["git", "add", "problems/", "targets/queue.yaml", "BOUNTY_REPORT.md", "submissions/"], cwd=str(ROOT_DIR), check=True)
        msg = f"feat(daemon): certifie {problem_name} sans sorry (coût: ${cost:.4f})"
        subprocess.run(["git", "commit", "-m", msg], cwd=str(ROOT_DIR), check=True)
        print(f"📦 Commit Git créé avec succès : '{msg}'")
    except Exception as e:
        print(f"⚠️ Erreur lors du commit Git : {e}")

def run_daemon(
    interval_sec: int = 30,
    min_balance_usd: float = 0.50,
    max_session_cost_usd: float = 5.00,
    daily_budget_usd: float = 0.30,
    prefer_offpeak: bool = False,
    offpeak_only: bool = False,
    run_once: bool = False,
    auto_commit: bool = True,
    send_digest_now: bool = False
):
    print("\n" + "=" * 70)
    print("🤖 AI-Maths-Researcher — Démarrage du Daemon de Production Autonome")
    print(f"Racine du projet : {ROOT_DIR}")
    print(f"File d'attente    : {QUEUE_PATH}")
    print(f"Seuil solde API  : ${min_balance_usd:.2f} USD | Plafond session : ${max_session_cost_usd:.2f} USD")
    print(f"Budget roulant 24h: ${daily_budget_usd:.2f} USD (garantie max ~$9/mois)")
    print(f"Kill-switch file : {STOP_FILE}")
    print(f"Mode Heures Creuses : {'ACTIF (-50%)' if is_deepseek_offpeak() else 'HEURES PLEINES'}")
    if offpeak_only:
        print("Restreint strictement aux Heures Creuses DeepSeek (--offpeak-only actif)")
    print("=" * 70 + "\n")

    db = AttemptsDB()
    verifier = RemoteProdVerifier()
    session_cost = 0.0
    notifier = TelegramNotifier()
    notified_gates = set()
    pending_approvals = set()
    proposed_bounties = set()
    last_digest_day = ""

    # Enregistrer les fiches déjà traitées pour éviter de notifier en boucle au boot
    if REGISTRY_PATH.exists():
        for t in load_targets(REGISTRY_PATH):
            if getattr(t, "bounty_hint", False) and (t.verified or getattr(t, "approval_stage", "none") != "none"):
                proposed_bounties.add(t.name)

    if send_digest_now:
        print("📊 Envoi immédiat du Digest quotidien Telegram demandé via CLI...")
        q_targets = load_targets(QUEUE_PATH) if QUEUE_PATH.exists() else []
        cur_bal = get_deepseek_balance()
        notifier.send_daily_digest(db, q_targets, cur_bal)

    # Génération initiale du dashboard statique
    try:
        generate_dashboard()
    except Exception as e:
        print(f"⚠️ Erreur génération dashboard : {e}")

    while True:
        # Régénération du dashboard à chaque cycle
        try:
            generate_dashboard()
        except Exception:
            pass

        # Envoi automatique du Digest quotidien à 20:00 UTC
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        today_str = now_dt.strftime("%Y-%m-%d")
        if now_dt.hour >= 20 and last_digest_day != today_str:
            print("📊 Envoi automatique du Digest quotidien Telegram (20:00 UTC)...")
            q_targets = load_targets(QUEUE_PATH) if QUEUE_PATH.exists() else []
            cur_bal = get_deepseek_balance()
            notifier.send_daily_digest(db, q_targets, cur_bal)
            last_digest_day = today_str

        # GATE 1: Kill-Switch STOP
        if STOP_FILE.exists():
            msg = "Fichier 'STOP' détecté. Arrêt d'urgence propre du daemon."
            print(f"🛑 GATE 1 DÉCLENCHÉE : {msg}")
            if "stop_file" not in notified_gates:
                notifier.notify_gate_triggered("FICHIER STOP DÉTECTÉ", msg)
                notified_gates.add("stop_file")
            break

        # GATE 2: Solde API DeepSeek
        balance = get_deepseek_balance()
        if balance is not None:
            print(f"💳 Solde DeepSeek en direct : ${balance:.2f} USD")
            if balance < min_balance_usd:
                msg = f"Solde insuffisant (${balance:.2f} < ${min_balance_usd:.2f} USD). Arrêt de sécurité."
                print(f"🛑 GATE 2 DÉCLENCHÉE : {msg}")
                if "low_balance" not in notified_gates:
                    notifier.notify_gate_triggered("SOLDE API INSUFFISANT", msg)
                    notified_gates.add("low_balance")
                break
        else:
            print("ℹ️ Solde DeepSeek non accessible ou clé API absente.")

        # GATE 3: Plafond de coût de la session
        if session_cost >= max_session_cost_usd:
            msg = f"Plafond session de ${max_session_cost_usd:.2f} USD atteint. Arrêt propre."
            print(f"🛑 GATE 3 DÉCLENCHÉE : {msg}")
            if "session_cost" not in notified_gates:
                notifier.notify_gate_triggered("PLAFOND SESSION ATTEINT", msg)
                notified_gates.add("session_cost")
            break

        # Watcher whitelisté (throttlé 24h par défaut)
        try:
            from agent.watcher import check_watchlist
            new_watched = check_watchlist()
            if new_watched:
                print(f"👀 Watcher : {len(new_watched)} nouvelle(s) cible(s) en attente de validation ajoutée(s) au registre.")
                # Notification sonore pour les cibles avec signal bounty potentiel (TÂCHE 13.2)
                for nw in new_watched:
                    if getattr(nw, "bounty_hint", False) and nw.name not in proposed_bounties:
                        print(f"💰 [Signal Bounty] Envoi proposition sonore Telegram pour '{nw.name}'...")
                        notifier.notify_bounty_proposal(
                            target_name=nw.name,
                            title=nw.submission or nw.name,
                            repo=nw.source_url or "repo",
                            url=nw.source_url or ""
                        )
                        proposed_bounties.add(nw.name)
                notifier.notify_watcher_new_targets(new_watched)
        except Exception as e:
            print(f"⚠️ Erreur watcher : {e}")

        # Traitement des commandes Telegram entrantes (/status, /approve, /confirm, /reject, /deny)
        reg_targets = load_targets(REGISTRY_PATH) if REGISTRY_PATH.exists() else []
        queue_targets = load_targets(QUEUE_PATH) if QUEUE_PATH.exists() else []

        pending_approve_names = [t.name for t in reg_targets if getattr(t, "bounty_hint", False) and not t.verified and getattr(t, "approval_stage", "none") == "none"]
        for p in pending_approvals:
            if p not in pending_approve_names:
                pending_approve_names.append(p)

        pending_confirm_names = [t.name for t in queue_targets if getattr(t, "approval_stage", "none") == "approved" and getattr(t, "round_trip_translation", None)]

        action_info = notifier.poll_approvals(
            pending_approvals=pending_approve_names,
            pending_confirms=pending_confirm_names
        )
        if action_info:
            act = action_info.get("action")
            tgt_name = action_info.get("target_name")
            if act == "approve" and tgt_name:
                print(f"🎉 Approbation reçue de Telegram pour '{tgt_name}' ! (verified: true, autoformalisation débloquée en heures creuses).")
                for rt in reg_targets:
                    if rt.name == tgt_name:
                        rt.verified = True
                        rt.offpeak_only = True
                        rt.approval_stage = "approved"
                        rt.budget_unlocked = True
                        rt.approved_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                save_targets(REGISTRY_PATH, reg_targets)

                # Assurer la présence de la cible dans queue.yaml
                q_names = [t.name for t in queue_targets]
                if tgt_name not in q_names:
                    matched = [rt for rt in reg_targets if rt.name == tgt_name]
                    if matched:
                        queue_targets.append(matched[0])
                        save_targets(QUEUE_PATH, queue_targets)
                else:
                    for qt in queue_targets:
                        if qt.name == tgt_name:
                            qt.verified = True
                            qt.offpeak_only = True
                            qt.approval_stage = "approved"
                            qt.budget_unlocked = True
                            qt.approved_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    save_targets(QUEUE_PATH, queue_targets)
                pending_approvals.discard(tgt_name)

            elif act == "confirm" and tgt_name:
                print(f"🎉 Confirmation reçue de Telegram pour '{tgt_name}' ! Recherche de preuve débloquée en heures creuses.")
                for qt in queue_targets:
                    if qt.name == tgt_name:
                        qt.approval_stage = "confirmed"
                        qt.confirmed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                save_targets(QUEUE_PATH, queue_targets)
                for rt in reg_targets:
                    if rt.name == tgt_name:
                        rt.approval_stage = "confirmed"
                        rt.confirmed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                save_targets(REGISTRY_PATH, reg_targets)

            elif act == "reject" and tgt_name:
                print(f"❌ Rejet reçu pour l'énoncé de '{tgt_name}'.")
                queue_targets = [qt for qt in queue_targets if qt.name != tgt_name]
                save_targets(QUEUE_PATH, queue_targets)
                for rt in reg_targets:
                    if rt.name == tgt_name:
                        rt.approval_stage = "rejected"
                save_targets(REGISTRY_PATH, reg_targets)

            elif act == "deny" and tgt_name:
                print(f"❌ Refus/archivage reçu pour '{tgt_name}'.")
                pending_approvals.discard(tgt_name)
                queue_targets = [qt for qt in queue_targets if qt.name != tgt_name]
                save_targets(QUEUE_PATH, queue_targets)
                for rt in reg_targets:
                    if rt.name == tgt_name:
                        rt.verified = False
                        rt.approval_stage = "denied"
                save_targets(REGISTRY_PATH, reg_targets)

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
            print("   RÈGLE ABSOLUE : Seul l'utilisateur valide une cible (via YAML ou /approve). Le daemon ne les traite pas.")

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
        print(f"Type : {current_target.kind} | Classe : {current_target.difficulty_class} | Valeur : ${current_target.value_usd} | Étape : {current_target.approval_stage}")
        print("-" * 70)

        # RÈGLE HEURES CREUSES DEEPSEEK (TÂCHE 13.3)
        # Toute cible offpeak_only ou avec value_usd > 0, ou si le flag global --offpeak-only est activé
        is_offpeak_needed = current_target.offpeak_only or (current_target.value_usd > 0) or offpeak_only
        if is_offpeak_needed and not is_deepseek_offpeak():
            next_win = get_next_offpeak_window_str()
            print(f"⏳ [Offpeak Gate] Cible '{current_target.name}' différée jusqu'aux heures creuses DeepSeek (-50%). Prochaine ouverture à {next_win}.")
            if run_once:
                print("🏁 Mode --once : fin d'exécution du daemon (cible différée hors heures creuses).")
                break
            print(f"En attente de la fenêtre creuse ({interval_sec}s)...")
            time.sleep(interval_sec)
            continue

        # PHASE 1 : AUTOFORMALISATION (TÂCHE 13.2)
        # Déclenchée si la cible a été approuvée (approval_stage == 'approved') mais pas encore confirmée
        if current_target.approval_stage == "approved":
            if current_target.round_trip_translation:
                print(f"⏳ Cible '{current_target.name}' formalisée en attente de confirmation Telegram (/confirm_{current_target.name} ou /reject_{current_target.name}).")
                if run_once:
                    print("🏁 Mode --once : fin d'exécution du daemon (énoncé en attente de confirmation).")
                    break
                time.sleep(interval_sec)
                continue

            print(f"\n📝 [Autoformalisation] Début de formalisation vérifiée pour '{current_target.name}'...")
            problem_text = current_target.natural_language
            if not problem_text:
                lines = [l.strip("- ") for l in current_target.statement.splitlines() if "Titre:" in l or ("Source:" not in l and "En attente" not in l)]
                problem_text = "\n".join(lines).strip() or current_target.submission or current_target.name

            autoform = Autoformalizer()
            res = autoform.formalize_problem(problem_text, theorem_name=current_target.name)
            if res.is_valid:
                print(f"🏆 Énoncé formalisé avec succès pour '{current_target.name}' (Score: {res.round_trip_score*100:.1f}%).")
                current_target.statement = res.lean_statement + " := by\n  sorry"
                current_target.round_trip_translation = res.round_trip_translation
                current_target.round_trip_score = res.round_trip_score
                save_targets(QUEUE_PATH, queue)

                reg_all = load_targets(REGISTRY_PATH)
                for rt in reg_all:
                    if rt.name == current_target.name:
                        rt.statement = current_target.statement
                        rt.round_trip_translation = res.round_trip_translation
                        rt.round_trip_score = res.round_trip_score
                        rt.approval_stage = "approved"
                save_targets(REGISTRY_PATH, reg_all)

                print(f"🔔 Envoi de l'énoncé formalisé sur Telegram pour confirmation (/confirm_{current_target.name})...")
                notifier.notify_formalization_result(
                    target_name=current_target.name,
                    lean_stmt=res.lean_statement,
                    back_translation=res.round_trip_translation,
                    score=res.round_trip_score
                )
            else:
                print(f"❌ Échec de l'autoformalisation pour '{current_target.name}' : {res.error_message}")

            if run_once:
                print("🏁 Mode --once : fin d'exécution du daemon après tentative d'autoformalisation.")
                break
            time.sleep(interval_sec)
            continue

        # Si cible non-benchmark et statement non-Lean alors que pas approved/confirmed -> sauter
        if current_target.kind != "benchmark" and not current_target.statement.strip().startswith(("theorem", "lemma")) and current_target.approval_stage not in ("approved", "confirmed"):
            print(f"ℹ️ Cible '{current_target.name}' sans énoncé Lean et non approuvée. Sautée.")
            if run_once:
                break
            time.sleep(interval_sec)
            continue

        # Calcul de p_success empirique et configuration de recherche
        class_stats = db.get_success_rates_by_class()
        cls_data = class_stats.get(current_target.difficulty_class)
        p_succ = cls_data["p_success"] if cls_data else 0.20
        config = config_for(current_target, p_succ)
        config.min_balance_threshold_usd = min_balance_usd

        # GATE BUDGET 24H & AUTORISATION HUMAINE PAR TELEGRAM (TÂCHE 11)
        rolling_24h_cost = db.get_rolling_cost_usd(24)
        est_cost = min(config.budget_usd, 0.03 * config.max_attempts * (2 if config.enable_escalation else 1))
        remaining_budget = max(0.0, daily_budget_usd - rolling_24h_cost)
        ev = (p_succ * current_target.value_usd) - est_cost if current_target.value_usd > 0 else (p_succ * 1.0) - est_cost

        # Règle Tâche 11 : Demande d'autorisation si prime > 0, EV positive et coût estimé > budget 24h restant
        if current_target.value_usd > 0 and not current_target.budget_unlocked and ev > 0 and est_cost > remaining_budget:
            if current_target.name not in pending_approvals:
                print(f"🔔 Demande d'autorisation Telegram envoyée pour '{current_target.name}' (prime ${current_target.value_usd:.2f}, coût est. ${est_cost:.2f} > reste ${remaining_budget:.2f}).")
                notifier.request_budget_approval(current_target.name, current_target.value_usd, p_succ, est_cost)
                pending_approvals.add(current_target.name)

            action_info = notifier.poll_approvals([current_target.name])
            if action_info and action_info.get("action") == "approve":
                print(f"🎉 Approbation reçue de Telegram pour '{current_target.name}' ! Déblocage du budget.")
                current_target.budget_unlocked = True
                save_targets(QUEUE_PATH, queue)
                pending_approvals.discard(current_target.name)
            elif action_info and action_info.get("action") == "deny":
                print(f"❌ Refus reçu de Telegram pour '{current_target.name}'. Cible renvoyée en fin de file.")
                pending_approvals.discard(current_target.name)
                remaining = queue[1:] + [current_target]
                save_targets(QUEUE_PATH, remaining)
                if run_once:
                    break
                time.sleep(interval_sec)
                continue
            else:
                print(f"⏳ Cible '{current_target.name}' en attente de réponse Telegram (/approve_{current_target.name} ou /deny_{current_target.name}).")
                if run_once:
                    break
                time.sleep(interval_sec)
                continue

        # Si le budget 24h est atteint et que la cible n'a pas été débloquée par l'humain : mise en veille
        if not current_target.budget_unlocked and rolling_24h_cost >= daily_budget_usd:
            msg = f"Dépense sur 24h (${rolling_24h_cost:.4f} USD) >= plafond quotidien (${daily_budget_usd:.2f} USD). Mise en veille pour borner la dépense à ~$9/mois max."
            print(f"🛑 GATE BUDGET 24H DÉCLENCHÉE : {msg}")
            if "daily_budget" not in notified_gates:
                notifier.notify_gate_triggered("PLAFOND 24H ATTEINT", msg)
                notified_gates.add("daily_budget")
            if run_once:
                print("🏁 Mode --once : fin d'exécution du daemon (budget 24h atteint).")
                break
            print(f"En attente de la prochaine fenêtre budgétaire ({interval_sec}s)...")
            time.sleep(interval_sec)
            continue
        else:
            notified_gates.discard("daily_budget")

        engine = ProofSearchEngine(config=config)
        planner = BlueprintPlanner(config=config) if current_target.kind in ("bounty", "mathlib") else None

        cost_before = db.get_summary()["total_cost_usd"]

        # Exécution de la recherche de preuve
        success, proof_code = engine.prove_theorem(
            theorem_decl=current_target.statement,
            problem_name=current_target.name,
            difficulty_class=current_target.difficulty_class
        )

        # Règle Tâche 9 : Blueprint seulement si p_success >= 0.15 OU cible à valeur financière réelle ; JAMAIS sur IMO benchmark.
        should_blueprint = (
            planner is not None
            and current_target.difficulty_class != "imo"
            and (p_succ >= 0.15 or current_target.value_usd > 0)
        )

        if not success and should_blueprint:
            print(f"  🔄 Repli sur décomposition Blueprint pour {current_target.name}...")
            success, proof_code = planner.prove_with_blueprint(
                theorem_decl=current_target.statement,
                problem_name=current_target.name
            )
        elif not success and planner and not should_blueprint:
            print(f"  ℹ️ Repli Blueprint ignoré pour '{current_target.name}' (classe '{current_target.difficulty_class}', p_success {p_succ*100:.1f}%, non-bounty). Évite les sous-lemmes orphelins coûteux.")

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

                # Génération automatique du package de soumission PR prêt pour revue humaine
                try:
                    from scripts.submission_kit import generate_submission
                    sub_dir = generate_submission(current_target.name, docstring=f"Formal proof of `{current_target.name}` in Lean 4.")
                    print(f"📦 Kit de soumission PR prêt dans {sub_dir}")
                except Exception as e:
                    print(f"⚠️ Erreur génération kit de soumission pour {current_target.name}: {e}")

                # Retirer la cible de la file
                remaining = queue[1:]
                save_targets(QUEUE_PATH, remaining)
                print(f"🗑️ Cible '{current_target.name}' retirée de la file ({len(remaining)} restantes).")

                # Mise à jour des rapports officiels
                generate_report()
                db.backup()

                # Notification Telegram Preuve Certifiée (Silencieuse)
                iterations = 1
                try:
                    with db.conn:
                        c = db.conn.cursor()
                        c.execute("SELECT iteration FROM attempts WHERE problem_name = ? AND success = 1 ORDER BY id DESC LIMIT 1", (current_target.name,))
                        row = c.fetchone()
                        if row:
                            iterations = row[0]
                except Exception:
                    pass

                notifier.notify_proof_certified(
                    name=current_target.name,
                    difficulty_class=current_target.difficulty_class,
                    cost=item_cost,
                    iterations=iterations
                )

                try:
                    generate_dashboard()
                except Exception:
                    pass

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
    parser.add_argument("--daily-budget", type=float, default=0.30, help="Plafond quotidien glissant de dépense API USD (default: 0.30)")
    parser.add_argument("--prefer-offpeak", action="store_true", help="Reporter les tâches Reasoner lourdes en heures creuses DeepSeek (-50%%)")
    parser.add_argument("--offpeak-only", action="store_true", help="Restreindre TOUTE dépense LLM du daemon aux heures creuses DeepSeek (-50%%)")
    parser.add_argument("--once", action="store_true", help="Traiter un problème de la file puis s'arrêter")
    parser.add_argument("--no-commit", action="store_true", help="Désactiver le commit git automatique")
    parser.add_argument("--digest", action="store_true", help="Envoyer immédiatement le digest quotidien Telegram au démarrage")
    args = parser.parse_args()

    run_daemon(
        interval_sec=args.interval,
        min_balance_usd=args.min_balance,
        max_session_cost_usd=args.max_cost,
        daily_budget_usd=args.daily_budget,
        prefer_offpeak=args.prefer_offpeak,
        offpeak_only=args.offpeak_only,
        run_once=args.once,
        auto_commit=not args.no_commit,
        send_digest_now=args.digest
    )

if __name__ == "__main__":
    main()
