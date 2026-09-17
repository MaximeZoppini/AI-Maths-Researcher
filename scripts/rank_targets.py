#!/usr/bin/env python3
"""
Target Evaluation & Ranking Script for AI-Maths-Researcher.
Calculates Expected Value (EV = p_success * value_usd - estimated_cost)
using empirical SQLite success rates to prioritize targets.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.db import AttemptsDB
from agent.targets import load_targets, save_targets, config_for

def rank_targets(
    registry_path: Path = Path("targets/registry.yaml"),
    push_queue: bool = False,
    queue_path: Path = Path("targets/queue.yaml")
):
    targets = load_targets(registry_path)
    if not targets:
        print(f"⚠️ Aucune cible trouvée dans {registry_path}")
        return

    verified_targets = [t for t in targets if t.verified]
    unverified_count = len(targets) - len(verified_targets)
    if unverified_count > 0:
        print(f"ℹ️ {unverified_count} cible(s) non vérifiée(s) ignorée(s) (verified: false requiert validation humaine).")

    if not verified_targets:
        print("⚠️ Aucune cible vérifiée (verified: true) à classer.")
        return

    db = AttemptsDB()
    class_stats = db.get_success_rates_by_class()

    ranked = []
    for t in verified_targets:
        # 1. p_success empirique par classe
        cls_data = class_stats.get(t.difficulty_class)
        if cls_data and cls_data.get("attempted", 0) >= 3:
            p_succ = cls_data["p_success"]
        else:
            # Prior par défaut selon la classe
            p_priors = {
                "mathd": 0.80,
                "amc": 0.35,
                "aime": 0.25,
                "olympiad_other": 0.35,
                "imo": 0.05,
                "research": 0.02,
                "unknown": 0.15
            }
            p_succ = p_priors.get(t.difficulty_class, 0.10)

        # 2. Coût estimé basé sur la config de recherche
        cfg = config_for(t, p_succ)
        est_cost = min(cfg.budget_usd, 0.03 * cfg.max_attempts * (2 if cfg.enable_escalation else 1))

        # 3. Espérance de gain (EV)
        if t.value_usd > 0:
            ev = (p_succ * t.value_usd) - est_cost
        else:
            ev = (p_succ * 1.0) - est_cost

        ranked.append({
            "target": t,
            "p_success": p_succ,
            "est_cost": est_cost,
            "ev": ev
        })

    # Trier par EV décroissante
    ranked.sort(key=lambda x: x["ev"], reverse=True)

    print("\n" + "=" * 88)
    print("🎯 AI-Maths-Researcher — Classement Économique des Cibles (EV Ranking)")
    print("=" * 88)
    print(f"{'Rang':<5} {'Nom':<34} {'Type':<11} {'Classe':<12} {'Valeur':<9} {'p_succ':<8} {'Coût':<8} {'EV':<9}")
    print("-" * 88)

    for idx, item in enumerate(ranked, 1):
        t = item["target"]
        val_str = f"${t.value_usd:.0f}" if t.value_usd > 0 else "$0"
        p_str = f"{item['p_success']*100:.1f}%"
        cost_str = f"${item['est_cost']:.3f}"
        ev_str = f"${item['ev']:+.2f}" if t.value_usd > 0 else f"{item['ev']:+.3f} pts"
        print(f"{idx:<5} {t.name:<34} {t.kind:<11} {t.difficulty_class:<12} {val_str:<9} {p_str:<8} {cost_str:<8} {ev_str:<9}")

    print("=" * 88 + "\n")

    if push_queue:
        ordered_targets = [item["target"] for item in ranked]
        save_targets(queue_path, ordered_targets)
        print(f"✅ File d'attente mise à jour avec succès : {queue_path} ({len(ordered_targets)} cibles ordonnées par EV)")

def main():
    parser = argparse.ArgumentParser(description="Rank targets by Expected Value (EV)")
    parser.add_argument("--registry", type=str, default="targets/registry.yaml", help="Chemin vers le registre des cibles")
    parser.add_argument("--push-queue", action="store_true", help="Injecter automatiquement les cibles triées dans targets/queue.yaml")
    parser.add_argument("--queue", type=str, default="targets/queue.yaml", help="Chemin vers la file d'attente")
    args = parser.parse_args()

    rank_targets(
        registry_path=Path(args.registry),
        push_queue=args.push_queue,
        queue_path=Path(args.queue)
    )

if __name__ == "__main__":
    main()
