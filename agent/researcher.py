#!/usr/bin/env python3
"""
AI-Maths-Researcher Agent CLI
Automates mathematical formalization, proof verification on prod infrastructure, and bounty submission tracking.
"""

import argparse
import sys
import os
import subprocess
from pathlib import Path
from agent.verifier import RemoteProdVerifier
from agent.prover import ProofSearchEngine, ProverConfig
from agent.db import AttemptsDB

def main():
    parser = argparse.ArgumentParser(description="AI-Maths-Researcher Agent")
    parser.add_argument("--verify", type=str, help="Verify a specific Lean file against prod Mathlib")
    parser.add_argument("--check-all", action="store_true", help="Run full formal check.sh on prod infrastructure")
    parser.add_argument("--solve", type=str, help="Autonomous proof search for a given theorem statement")
    parser.add_argument("--name", type=str, default="CandidateProblem", help="Problem name for --solve")
    parser.add_argument("--attempts", type=int, default=5, help="Max repair iterations for --solve")
    parser.add_argument("--stats", action="store_true", help="Display proof attempts metrics and stats")
    parser.add_argument("--deploy", action="store_true", help="Commit, push to GitHub, and trigger prod sync")
    parser.add_argument("--message", "-m", type=str, default="chore: automated proof update from AI agent", help="Commit message for deploy")

    args = parser.parse_args()

    if args.stats:
        from agent.stats import main as print_stats
        print_stats()
        sys.exit(0)

    elif args.verify:
        lean_path = Path(args.verify)
        if not lean_path.exists():
            print(f"❌ File not found: {lean_path}")
            sys.exit(1)
        
        print(f"🔬 Envoi et vérification formelle de {lean_path.name} sur l'infrastructure de prod...")
        code = lean_path.read_text(encoding="utf-8")
        verifier = RemoteProdVerifier()
        result = verifier.verify_file_content(code, temp_name=lean_path.name)
        
        if result.success:
            print(f"✅ SUCCÈS : {lean_path.name} est formellement vérifié sans sorry ni axiom !")
            print(result.stdout)
            sys.exit(0)
        else:
            print(f"❌ ÉCHEC de vérification formelle :")
            if result.has_sorry_axiom:
                print("⚠️  Le code contient 'sorry' ou 'sorryAx'.")
            if result.unauthorized_axioms:
                print(f"⚠️  Axiomes non autorisés : {result.unauthorized_axioms}")
            if result.error_message:
                print(f"Erreurs du compilateur :\n{result.error_message}")
            if result.unsolved_goals:
                print(f"Objectifs non résolus :\n" + "\n".join(result.unsolved_goals))
            sys.exit(1)

    elif args.solve:
        engine = ProofSearchEngine(config=ProverConfig(max_attempts=args.attempts))
        success, verified_code = engine.prove_theorem(args.solve, problem_name=args.name)
        if success:
            out_file = Path("problems") / f"{args.name}.lean"
            out_file.write_text(verified_code + "\n", encoding="utf-8")
            print(f"\n💾 Preuve enregistrée dans {out_file} !")
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.check_all:
        verifier = RemoteProdVerifier()
        print("🔍 Exécution du check complet sur la prod...")
        success, output = verifier.run_prod_check()
        print(output)
        sys.exit(0 if success else 1)

    elif args.deploy:
        print("🚀 Déploiement automatique vers GitHub et sync Prod...")
        subprocess.run(["git", "add", "."], check=True)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
        if status.strip():
            subprocess.run(["git", "commit", "-m", args.message], check=True)
        
        proc = subprocess.run(["./scripts/deploy_prod.sh"], check=False)
        sys.exit(proc.returncode)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
