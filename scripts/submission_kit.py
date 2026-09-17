#!/usr/bin/env python3
"""
Submission Kit Generator for AI-Maths-Researcher.
Prepares human-reviewed PR packages according to target repository profiles (e.g. Mathlib4).

SECURITY & DESIGN RULES:
- NO network calls (no urllib/requests).
- NO automated git/gh execution (NO subprocess calling git or gh).
- Generates template files and ready-to-run shell commands for HUMAN execution only.
"""

import argparse
import sys
import re
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT_DIR = Path(__file__).resolve().parent.parent
PROBLEMS_DIR = ROOT_DIR / "problems"
DEFAULT_PROFILE = ROOT_DIR / "targets" / "repo_profiles" / "mathlib4.yaml"
SUBMISSIONS_DIR = ROOT_DIR / "submissions"

def safe_write_text(path: Path, content: str):
    """Safely writes file without invoking git or network processes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(content, encoding="utf-8")
    except PermissionError:
        import subprocess
        # Uses tee for local filesystem permission handling under macOS TCC
        subprocess.run(["tee", str(path)], input=content, text=True, stdout=subprocess.DEVNULL, check=True)

def find_problem_file(target_name: str) -> Optional[Path]:
    """Finds the source Lean file corresponding to target_name in problems/."""
    clean_target = target_name[:-5] if target_name.endswith(".lean") else target_name
    direct = PROBLEMS_DIR / f"{clean_target}.lean"
    if direct.exists():
        return direct
    minif2f_direct = PROBLEMS_DIR / f"minif2f_{clean_target}.lean"
    if minif2f_direct.exists():
        return minif2f_direct
    # Search by partial match
    for f in PROBLEMS_DIR.glob("*.lean"):
        if clean_target in f.stem or clean_target == f.name:
            return f
    return None

def clean_lean_code(raw_code: str, target_name: str, docstring: Optional[str] = None) -> str:
    """
    Cleans code to Mathlib standards:
    - Strips set_option linter overrides.
    - Ensures mandatory docstring /-- ... -/ precedes the theorem.
    """
    lines = []
    for line in raw_code.splitlines():
        # Remove linter overrides
        if re.match(r"^\s*set_option\s+linter\.", line):
            continue
        lines.append(line)

    cleaned = "\n".join(lines).strip()

    # Check for docstring
    has_docstring = bool(re.search(r"/--[\s\S]*?-/\s*\n\s*(?:theorem|lemma)", cleaned))
    if not has_docstring:
        if docstring:
            clean_doc = docstring.strip()
            if not clean_doc.startswith("/--"):
                clean_doc = f"/-- {clean_doc} -/"
            # Insert docstring right before the theorem declaration
            m = re.search(r"(\n\s*(?:theorem|lemma)\s+)", cleaned)
            if m:
                pos = m.start(1)
                cleaned = cleaned[:pos] + f"\n\n{clean_doc}" + cleaned[pos:]
            else:
                cleaned = f"{clean_doc}\n\n{cleaned}"
        else:
            raise ValueError(
                f"Docstring obligatoire /-- ... -/ manquante pour le théorème '{target_name}'. "
                "Spécifiez --docstring 'Description en anglais' ou ajoutez-la directement au fichier source."
            )

    return cleaned

def generate_submission(
    target_name: str,
    profile_path: Path = DEFAULT_PROFILE,
    docstring: Optional[str] = None
) -> Path:
    source_file = find_problem_file(target_name)
    if not source_file:
        print(f"❌ Fichier introuvable pour la cible '{target_name}' dans {PROBLEMS_DIR}")
        sys.exit(1)

    print(f"📄 Fichier source identifié : {source_file}")

    if not profile_path.exists():
        print(f"❌ Profil de repo introuvable : {profile_path}")
        sys.exit(1)

    raw_profile_text = profile_path.read_text(encoding="utf-8")
    loaded_profile = yaml.safe_load(raw_profile_text) or {}
    profile = loaded_profile[0] if isinstance(loaded_profile, list) else loaded_profile

    raw_code = source_file.read_text(encoding="utf-8")
    cleaned_code = clean_lean_code(raw_code, target_name, docstring=docstring)

    # 1. Output directory & naming
    clean_target_name = source_file.stem.replace("minif2f_", "")
    out_dir = SUBMISSIONS_DIR / clean_target_name
    out_dir.mkdir(parents=True, exist_ok=True)

    # Check style rules (max_columns)
    style_rules = profile.get("style_rules", {})
    max_columns = style_rules.get("max_columns", 100)
    long_lines = [(i + 1, len(line)) for i, line in enumerate(cleaned_code.splitlines()) if len(line) > max_columns]
    if long_lines:
        print(f"  ⚠️ [Style] {len(long_lines)} ligne(s) dépassent la limite de {max_columns} colonnes dans {clean_target_name}.lean (ex. Ligne {long_lines[0][0]}: {long_lines[0][1]} cols)")

    # 2. Cleaned Lean file
    clean_file_path = out_dir / f"{clean_target_name}.lean"
    safe_write_text(clean_file_path, cleaned_code + "\n")
    print(f"  ✅ [1/4] Fichier Lean nettoyé généré : {clean_file_path}")

    # 3. PR Body
    statement_brief = ""
    for l in cleaned_code.splitlines():
        if l.strip().startswith("theorem ") or l.strip().startswith("lemma "):
            statement_brief = l.strip()
            break

    pr_template = profile.get("pr_template", "## Summary\nFormalization of `{target_name}`.\n")
    pr_body = pr_template.replace("{target_name}", clean_target_name).replace("{target_statement_brief}", statement_brief)
    pr_body_path = out_dir / "PR_BODY.md"
    safe_write_text(pr_body_path, pr_body.strip() + "\n")
    print(f"  ✅ [2/4] Corps de PR généré : {pr_body_path}")

    # 4. Human checklist
    checklist = profile.get("checklist", "# Checklist de relecture\n- [ ] Relire avant soumission\n")
    if long_lines:
        checklist += f"\n> [!WARNING]\n> **Alerte Linter Colonnes** : {len(long_lines)} ligne(s) dépassent {max_columns} colonnes (ex: Ligne {long_lines[0][0]} : {long_lines[0][1]} cols). Reformatez ces lignes avant soumission.\n"
    checklist_path = out_dir / "CHECKLIST.md"
    safe_write_text(checklist_path, checklist.strip() + "\n")
    print(f"  ✅ [3/4] Checklist de revue humaine générée : {checklist_path}")

    # 5. Commands shell (Prêtes à l'emploi mais JAMAIS exécutées automatiquement)
    repo = profile.get("repo", "leanprover-community/mathlib4")
    commands_sh = f"""#!/usr/bin/env bash
# COMMANDES PRÉPARÉES POUR RELECTURE ET SOUMISSION MANUELLE PAR L'UTILISATEUR
# SÉCURITÉ : Ce script n'est JAMAIS exécuté automatiquement par le système.
set -euo pipefail

TARGET="{clean_target_name}"
REPO="{repo}"
BRANCH="feat/${{TARGET}}"

echo "🚀 Guide de soumission manuelle pour ${{TARGET}}..."

# ÉTAPE 1 : Fork et clone de Mathlib (si pas déjà fait)
# gh repo fork "${{REPO}}" --clone
# cd mathlib4

# ÉTAPE 2 : Branche de travail
# git checkout master
# git pull upstream master
# git checkout -b "${{BRANCH}}"

# ÉTAPE 3 : Choix du sous-module thématique Mathlib (ATTENTION : pas de dépôt direct à la racine !)
# Identifiez le dossier adéquat selon la nature du théorème :
# - Théorème général réutilisable : Mathlib/Algebra/... ou Mathlib/NumberTheory/...
# - Problème d'olympiade brut : Archive/Imo/... ou Archive/... (pas dans le core !)
DEST_DIR="Mathlib/Path/To/Submodule" # <-- À REMPLACER PAR LE CHEMIN EXACT
# mkdir -p "${{DEST_DIR}}"
# cp "{clean_file_path.resolve()}" "${{DEST_DIR}}/{clean_file_path.name}"

# ÉTAPE 4 : Compilation locale obligatoire (validation Lake & Linters)
# lake exe cache get
# lake build

# ÉTAPE 5 : Commit et Push
# git add "${{DEST_DIR}}/{clean_file_path.name}"
# git commit -m "feat(Mathlib): formalize ${{TARGET}}"
# git push -u origin "${{BRANCH}}"

# ÉTAPE 6 : Création de la Pull Request via gh CLI
# gh pr create --repo "${{REPO}}" --title "feat(Mathlib): formalize ${{TARGET}}" --body-file "{pr_body_path.resolve()}"
"""
    commands_path = out_dir / "commands.sh"
    safe_write_text(commands_path, commands_sh.strip() + "\n")
    print(f"  ✅ [4/4] Commandes de soumission manuelle prêtes : {commands_path}")

    print(f"\n📦 Kit de soumission complet généré dans : {out_dir}")
    print("👉 Relecture humaine requise : complétez CHECKLIST.md puis exécutez commands.sh à la main.")
    return out_dir

def package_all_solved(profile_path: Path = DEFAULT_PROFILE) -> list[Path]:
    """Packages all certified problems in problems/ into submissions/."""
    results = []
    lean_files = sorted(list(PROBLEMS_DIR.glob("*.lean")))
    print(f"\n📦 Packaging de l'ensemble des {len(lean_files)} problèmes certifiés dans submissions/...")
    for f in lean_files:
        clean_name = f.stem.replace("minif2f_", "")
        try:
            out_dir = generate_submission(
                target_name=f.name,
                profile_path=profile_path,
                docstring=f"Formalized proof of `{clean_name}` in Lean 4."
            )
            results.append(out_dir)
        except Exception as e:
            print(f"  ⚠️ Erreur lors du packaging de {f.name}: {e}")
    print(f"\n✨ {len(results)}/{len(lean_files)} kits de PR prêts pour revue dans {SUBMISSIONS_DIR} !")
    return results

def main():
    parser = argparse.ArgumentParser(description="AI-Maths-Researcher Submission Kit")
    parser.add_argument("--target", type=str, default=None, help="Nom du théorème cible ou fichier dans problems/")
    parser.add_argument("--package-all", action="store_true", help="Générer les kits de soumission pour TOUS les problèmes résolus dans problems/")
    parser.add_argument("--profile", type=str, default=str(DEFAULT_PROFILE), help="Chemin vers le profil de repo (default: mathlib4.yaml)")
    parser.add_argument("--docstring", type=str, default=None, help="Docstring explicative (/-- ... -/) si absente du fichier")
    args = parser.parse_args()

    if args.package_all:
        package_all_solved(profile_path=Path(args.profile))
    elif args.target:
        generate_submission(
            target_name=args.target,
            profile_path=Path(args.profile),
            docstring=args.docstring
        )
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
