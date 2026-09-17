#!/usr/bin/env bash
# Script exécuté périodiquement sur le conteneur LXC (prod) pour synchroniser et valider automatiquement
set -e

source /home/lean/.profile 2>/dev/null || true
cd /home/lean/projects/sun-formal

# Vérifier la présence de nouveaux commits
git fetch origin main >/dev/null 2>&1 || exit 0
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔄 Nouveaux commits détectés sur GitHub ($LOCAL -> $REMOTE)"
    git reset --hard origin/main
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔨 lake build en cours..."
    lake build
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔍 Exécution de check.sh..."
    ./scripts/check.sh
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Synchronisation et validation terminées avec succès !"
fi
