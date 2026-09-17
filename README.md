# AI-Maths-Researcher

Environnement autonome de formalisation mathématique en **Lean 4 + Mathlib** et agent de recherche automatisé pour les primes mathématiques (Justin Sun Prize, Epoch AI, etc.).

## 🏗 Architecture Hybride Local / Prod

- **Local (Ce repo sur votre machine) :** Développement de l'agent, rédaction des problèmes (`problems/`), prise de notes (`notes/`), orchestration d'IA.
- **Prod (Conteneur LXC Dédié Proxmox `lean-lab`) :** Environnement d'exécution isolé, validation formelle avec le compilateur Lean 4, Mathlib pré-compilée, vérification d'absence de `sorry`/`axiom`.

## 📦 Versions & Dépendances
- **Lean 4 :** `v4.34.0`
- **Mathlib4 :** Commit `5ed2965256430c3649e86755f9576b54eca72435`
- **Lake :** `5.0.0`

## 🚀 Utilisation

### Compilation & Vérification locale / prod
```bash
# Compiler le projet
lake build

# Vérifier qu'aucun sorry ou axiome non justifié n'est présent dans problems/
./scripts/check.sh
```

### Déploiement & Synchronisation Prod
Pour synchroniser automatiquement vos modifications avec le conteneur Proxmox ("prod") et exécuter la validation formelle en direct :
```bash
./scripts/deploy_prod.sh
```

## 📁 Arborescence
- `problems/` : Fichiers `.lean` pour chaque conjecture ou problème formalisé.
- `notes/` : Énoncés de problèmes, notes de recherche, liens vers les bounties et documentation.
- `scripts/` : Outils de vérification (`check.sh`), synchronisation vers l'infrastructure (`deploy_prod.sh`).
- `SunFormal/` : Modules Lean de base et tests du projet.
