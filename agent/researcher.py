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

def main():
    parser = argparse.ArgumentParser(description="AI-Maths-Researcher Agent")
    parser.add_argument("--verify", type=str, help="Verify a specific Lean file against prod Mathlib")
    parser.add_argument("--check-all", action="store_true", help="Run full formal check.sh on prod infrastructure")
    parser.add_argument("--deploy", action="store_true", help="Commit, push to GitHub, and trigger prod sync")
    parser.add_argument("--message", "-m", type=str, default="chore: automated proof update from AI agent", help="Commit message for deploy")

    args = parser.parse_args()
    verifier = RemoteProdVerifier()

    if args.verify:
        lean_path = Path(args.verify)
        if not lean_path.exists():
            print(f"❌ File not found: {lean_path}")
            sys.exit(1)
        
        print(f"🔬 Envoi et vérification formelle de {lean_path.name} sur l'infrastructure de prod...")
        code = lean_path.read_text(encoding="utf-8")
        result = verifier.verify_file_content(code, temp_name=lean_path.name)
        
        if result.success:
            print(f"✅ SUCCÈS : {lean_path.name} est formellement vérifié sans sorry ni axiom !")
            print(result.stdout)
            sys.exit(0)
        else:
            print(f"❌ ÉCHEC de vérification formelle :")
            if result.has_sorry_or_axiom:
                print("⚠️  Le code contient 'sorry' ou 'axiom'.")
            if result.error_message:
                print(f"Erreurs du compilateur :\n{result.error_message}")
            if result.unsolved_goals:
                print(f"Objectifs non résolus :\n" + "\n".join(result.unsolved_goals))
            sys.exit(1)

    elif args.check_all:
        print("🔍 Exécution du check complet sur la prod...")
        success, output = verifier.run_prod_check()
        print(output)
        sys.exit(0 if success else 1)

    elif args.deploy:
        print("🚀 Déploiement automatique vers GitHub et sync Prod...")
        # Add all, commit, and run deploy_prod.sh
        subprocess.run(["git", "add", "."], check=True)
        # Check if there are changes to commit
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
        if status.strip():
            subprocess.run(["git", "commit", "-m", args.message], check=True)
        
        proc = subprocess.run(["./scripts/deploy_prod.sh"], check=False)
        sys.exit(proc.returncode)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
