#!/usr/bin/env bash
set -e

PROXMOX_HOST="100.90.108.89"
CONTAINER_ID="200"
BRANCH="${1:-main}"

echo "=================================================="
echo "🚀 DÉPLOIEMENT & SYNCHRONISATION PROD (LXC $CONTAINER_ID)"
echo "=================================================="

# 1. Vérifier et pousser sur GitHub si besoin
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
echo "📌 Branche locale actuelle : $CURRENT_BRANCH"

echo "⬆️  Push des commits vers GitHub origin/$CURRENT_BRANCH..."
git push origin "$CURRENT_BRANCH"

# 2. Exécution du pull et du check en prod sur le conteneur LXC
echo "🔄 Déclenchement du pull & vérification sur l'infra de prod..."
ssh "root@$PROXMOX_HOST" "pct exec $CONTAINER_ID -- su - lean -c '
  source ~/.profile
  cd ~/projects/sun-formal
  echo \"📥 [Prod] git pull origin $CURRENT_BRANCH...\"
  git fetch origin $CURRENT_BRANCH
  git reset --hard origin/$CURRENT_BRANCH
  echo \"🔨 [Prod] lake build...\"
  lake build
  echo \"🔍 [Prod] Exécution de check.sh...\"
  ./scripts/check.sh
'"

echo "=================================================="
echo "✨ Déploiement et validation prod terminés avec succès !"
echo "=================================================="
