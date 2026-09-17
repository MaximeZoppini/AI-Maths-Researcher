# Justin Sun Prize & Mathematical Formalization Bounties

## Objectif
Résoudre et formaliser des problèmes mathématiques ouverts ou de haut niveau en **Lean 4 + Mathlib** en vue de soumissions aux primes mathématiques (Justin Sun Prize, Bounties Lean/Epoch AI/IMO Grand Challenge).

## Pipeline de Recherche & Formalisation
1. **Sélection de problème :** Documenter l'énoncé et la stratégie dans `notes/<nom_probleme>.md`.
2. **Ébauche formelle :** Déclarer la conjecture dans `problems/<nom_probleme>.lean`.
3. **Résolution & Preuve :**
   - Écriture des lemmes intermédiaires.
   - Utilisation des tactiques Mathlib (`ring`, `linarith`, `norm_num`, `aesop`, `omega`, `polyrith`, `exact?`, `apply?`).
4. **Validation Prod :**
   - Exécution via `./scripts/deploy_prod.sh`.
   - Le conteneur Proxmox `lean-lab` compile avec `lake env lean` et valide l'absence stricte de `sorry` et d'`axiom`.
