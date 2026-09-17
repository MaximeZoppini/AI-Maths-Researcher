#!/usr/bin/env bash
# COMMANDES PRÉPARÉES POUR RELECTURE ET SOUMISSION MANUELLE PAR L'UTILISATEUR
# SÉCURITÉ : Ce script n'est JAMAIS exécuté automatiquement par le système.
set -euo pipefail

TARGET="Problem2_ModThreeSquare"
REPO="leanprover-community/mathlib4"
BRANCH="feat/${TARGET}"

echo "🚀 Préparation de la branche pour ${TARGET}..."
# 1. Fork et clonage (si pas déjà fait)
# gh repo fork "${REPO}" --clone=false || true

# 2. Création de la branche locale
git checkout -b "${BRANCH}"

# 3. Copie du fichier nettoyé
cp "Problem2_ModThreeSquare.lean" Mathlib/

# 4. Commit et push
git add "Mathlib/Problem2_ModThreeSquare.lean"
git commit -m "feat(Mathlib): add ${TARGET}"
git push -u origin "${BRANCH}"

# 5. Création de la Pull Request
gh pr create --repo "${REPO}" --title "feat(Mathlib): add ${TARGET}" --body-file "PR_BODY.md"
