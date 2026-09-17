#!/usr/bin/env python3
"""
Audit formel des axiomes mathématiques Lean 4 pour AI-Maths-Researcher.
Vérifie qu'aucun théorème ne dépend de 'sorryAx' ou d'axiomes non autorisés.
Seuls les axiomes standards de Lean 4 sont admis :
- propext (extensionalité propositionnelle)
- Classical.choice (axiome du choix)
- Quot.sound (quotients)
"""

import sys
import os
import re
import subprocess
import tempfile
from pathlib import Path

ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}

def audit_file(filepath: Path) -> bool:
    print(f"\n🔬 Audit des axiomes pour {filepath.name}...")
    content = filepath.read_text(encoding="utf-8")
    theorems = re.findall(r"\b(?:theorem|lemma)\s+([a-zA-Z0-9_']+)", content)
    
    if not theorems:
        print(f"ℹ️  Aucun théorème/lemme déclaré dans {filepath.name}.")
        return True

    # Créer un fichier temporaire avec #print axioms pour chaque théorème
    audit_content = content + "\n\n-- Automated Formal Axiom Audit\n"
    for thm in theorems:
        audit_content += f"#print axioms {thm}\n"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".lean", dir=filepath.parent, delete=False) as tmp:
        tmp.write(audit_content)
        tmp_path = Path(tmp.name)

    try:
        res = subprocess.run(["lake", "env", "lean", str(tmp_path)], capture_output=True, text=True)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    combined = res.stdout + "\n" + res.stderr
    if res.returncode != 0 or "error:" in combined:
        print(f"❌ Erreur de compilation dans {filepath.name} :\n{combined.strip()}")
        return False

    # Analyser les axiomes pour chaque théorème
    all_ok = True
    for thm in theorems:
        pattern = rf"'{re.escape(thm)}' depends on axioms:\s*\[(.*?)\]"
        match = re.search(pattern, combined)
        if not match:
            print(f"⚠️  Impossible d'extraire les axiomes pour '{thm}'.")
            all_ok = False
            continue

        raw_axioms = [ax.strip() for ax in match.group(1).split(",") if ax.strip()]
        used_axioms = set(raw_axioms)

        if "sorryAx" in used_axioms:
            print(f"❌ REJET : '{thm}' dépend de 'sorry' / 'sorryAx' !")
            all_ok = False
            continue

        unauthorized = used_axioms - ALLOWED_AXIOMS
        if unauthorized:
            print(f"❌ REJET : '{thm}' utilise des axiomes non autorisés : {unauthorized}")
            all_ok = False
            continue

        print(f"  ✅ '{thm}' : Axiomes certifiés valides -> [{', '.join(sorted(used_axioms))}]")

    return all_ok

def main():
    target_dir = Path("problems")
    lean_files = sorted(target_dir.glob("*.lean"))

    if not lean_files:
        print("ℹ️  Aucun fichier .lean à auditer dans problems/.")
        sys.exit(0)

    success = True
    for f in lean_files:
        if not audit_file(f):
            success = False

    print("\n" + "="*50)
    if success:
        print("✨ AUDIT RÉUSSI : 100% des théorèmes sont certifiés 'Sorry-Free' et 'Axiom-Clean' !")
        sys.exit(0)
    else:
        print("❌ ÉCHEC DE L'AUDIT : Des théorèmes contiennent des axiomes invalides ou 'sorry' !")
        sys.exit(1)

if __name__ == "__main__":
    main()
