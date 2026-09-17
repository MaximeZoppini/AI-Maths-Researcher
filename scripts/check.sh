#!/usr/bin/env bash
set -e

echo "=== [1/3] Compilation du package principal Lean 4 ==="
lake build

echo "=== [2/3] Compilation & Vérification des problèmes dans problems/ ==="
shopt -s nullglob
PROBLEM_FILES=(problems/*.lean)
if [ ${#PROBLEM_FILES[@]} -eq 0 ]; then
  echo "ℹ️  Aucun fichier .lean dans problems/ pour le moment."
else
  for f in "${PROBLEM_FILES[@]}"; do
    echo "🔍 Vérification formelle de $f..."
    lake env lean "$f"
  done
fi

echo "=== [3/3] Vérification formelle d'absence de 'sorry' ou 'axiom' dans problems/ ==="
SORRY_MATCHES=$(grep -rnE '\b(sorry|axiom)\b' problems/ --include="*.lean" 2>/dev/null || true)

if [ -n "$SORRY_MATCHES" ]; then
  echo "❌ ÉCHEC : Des occurrences de 'sorry' ou 'axiom' ont été détectées dans problems/ :"
  echo "$SORRY_MATCHES"
  exit 1
fi

echo "✅ Succès : Tous les lemmes et problèmes compilent sans erreur et sans 'sorry' / 'axiom' !"
