# AI-Maths-Researcher

Environnement autonome de formalisation mathématique en **Lean 4 + Mathlib** et agent de recherche automatisé pour les primes mathématiques (Justin Sun Prize, Epoch AI, Olympiades, etc.).

---

## 🏗 Architecture Hybride Local / Prod

- **Local (Ce repo sur votre machine) :** Développement de l'agent, rédaction des problèmes (`problems/`), prise de notes de recherche (`notes/`), pilotage IA.
- **Prod (Conteneur LXC Dédié Proxmox `lean-lab`) :** Environnement d'exécution isolé, compilation Lean 4 avec cache Mathlib (8 900+ modules précompilés), validation stricte sans `sorry`/`axiom`.

---

## 📦 Versions & Dépendances
- **Lean 4 :** `v4.34.0`
- **Mathlib4 :** Commit `5ed2965256430c3649e86755f9576b54eca72435`
- **Lake :** `5.0.0`
- **Python :** `3.13+`

---

## 📊 Résultats & Métrique Officielle

- **Métrique Officielle MiniF2F Test** : **17/30 problèmes distincts des 30 premiers du set MiniF2F test (57 %)**.
- **Protocole & Configuration de référence** :
  - **Modèle de base** : `deepseek-chat` (itérations 1-2) avec escalade sur `deepseek-reasoner` (itérations 3+).
  - **Sampling** : `pass@2` à températures étagées (0.1 et 0.4).
  - **Tentatives max** : 3 tentatives par problème.
  - **Décomposition** : `BlueprintPlanner` activé (plan NL + décomposition en lemmes formels).
  - **Environnement** : Lean 4 `v4.34.0`, Mathlib4 commit `5ed2965256430c3649e86755f9576b54eca72435`.
  - **Certification** : Audit formel `#print axioms` sans sorry sur conteneur LXC 200.
  - **Date** : 2026-09-17.

---

## 🧮 Problèmes Résolus & Vérifiés en Prod (`problems/`)

Tous les problèmes ci-dessous sont **formellement prouvés, sans `sorry` ni `axiom`**, et validés directement par le compilateur Lean 4 sur l'infrastructure de production :

### 1. Théorie des nombres élémentaire (`problems/Problem1_EvenSquare.lean`)
- **Énoncé :** Pour tout entier $n \in \mathbb{Z}$, si $n^2$ est pair, alors $n$ est pair.
- **Preuve formelle :** Raisonnement par contraposée (`contrapose!`). Si $n$ est impair, $n = 2k + 1$, alors $n^2 = 2(2k^2 + 2k) + 1$, ce qui est impair (`ring` + `Int.not_even_iff_odd`).

### 2. Arithmétique Modulaire / Résidus quadratiques (`problems/Problem2_ModThreeSquare.lean`)
- **Énoncé :** Aucun carré d'entier n'est congru à $2 \pmod 3$ ($\forall a, k \in \mathbb{Z},\; a^2 \neq 3k + 2$).
- **Preuve formelle :** Division euclidienne par 3 ($a = 3q + r$ avec $r \in \{0, 1, 2\}$). Décomposition par cas sur le reste, développement algébrique du carré via `ring`, et réfutation immédiate par la tactique `omega`.

### 3. Inégalités Classiques (`problems/Problem3_Inequalities.lean`)
- **Énoncé 3a (AM-GM à 2 variables) :** $\forall a, b \in \mathbb{R},\; 2ab \le a^2 + b^2$.
  - **Preuve :** Équivalent à $0 \le (a - b)^2$ via `sq_nonneg` et `linarith`.
- **Énoncé 3b (Inégalité de Cauchy-Schwarz en dimension 2) :** $\forall a_1, a_2, b_1, b_2 \in \mathbb{R},\; (a_1 b_1 + a_2 b_2)^2 \le (a_1^2 + a_2^2)(b_1^2 + b_2^2)$.
  - **Preuve :** Identité algébrique de Lagrange $(a_1^2 + a_2^2)(b_1^2 + b_2^2) - (a_1 b_1 + a_2 b_2)^2 = (a_1 b_2 - a_2 b_1)^2$ via `ring`, puis clôture par positivité du carré et `linarith`.

---

## 🔄 Pipeline Autonome de Bout en Bout (End-to-End)

Le système implémente une chaîne complète du problème brut jusqu'au kit de Pull Request prêt à relire :

```
1. Détection / Benchmark (Watcher GitHub API / Cibles vérifiées / MiniF2F 244)
                  ↓
2. Résolution IA & REPL (DeepSeek Chat/Reasoner + BlueprintPlanner + Loogle)
                  ↓
3. Certification Prod LXC (Compilation Lake + audit strict #print axioms zero-sorry)
                  ↓
4. Packaging PR Automatique (submissions/<nom>/ : code nettoyé, PR_BODY.md, CHECKLIST.md, commands.sh)
                  ↓
5. Revue Humaine & Validation (L'opérateur coche la checklist et exécute commands.sh)
```

---

## 🚀 Commandes & Utilisation de l'Agent

### 1. Vérifier un problème spécifique sur la prod
Envoie le code au compilateur Lean 4 de l'infrastructure Proxmox et renvoie le diagnostic exact en quelques secondes :
```bash
python3 -m agent.researcher --verify problems/Problem1_EvenSquare.lean
python3 -m agent.researcher --verify problems/Problem2_ModThreeSquare.lean
python3 -m agent.researcher --verify problems/Problem3_Inequalities.lean
```

### 2. Audit formel global en Prod (Garantie Anti-Sorry / Anti-Axiom)
Compile tout le projet et valide l'absence stricte de `sorry` ou `axiom` sur l'ensemble des 25 théorèmes :
```bash
python3 -m agent.researcher --check-all
```

### 3. Déploiement & Synchronisation Automatique
Pousse les modifications locales vers GitHub et déclenche instantanément le `git pull` + compilation sur le conteneur LXC Proxmox :
```bash
./scripts/deploy_prod.sh
# ou via l'agent
python3 -m agent.researcher --deploy -m "feat: add new formal proof"
```
> **Note :** Un timer systemd (`lean-sync.timer`) tourne également en tâche de fond sur le conteneur pour synchroniser automatiquement les commits GitHub toutes les 60 secondes.

### 4. Benchmark MiniF2F & Analyse Pré-Vol (Pre-Flight)
Vérification des 244 théorèmes officiels avec estimation du coût API et packaging automatique des succès dans `submissions/` :
```bash
# Simulation sans appel API ni coût (vérification budget & tokens)
python3 -B -m benchmarks.minif2f --limit 244 --skip-solved --dry-run

# Lancement complet (requiert solde API suffisant)
python3 -B -m benchmarks.minif2f --limit 244 --attempts 3 --pass-k 2 --skip-solved
```

### 5. Kits de Soumission PR Mathlib (Zéro Action Réseau Auto)
Génère le dossier `submissions/<cible>/` avec code conforme, corps de PR, checklist et script de commandes manuelles :
```bash
# Packager une cible individuelle
python3 -B scripts/submission_kit.py --target mathd_algebra_137

# Packager en lot TOUS les problèmes résolus dans problems/
python3 -B scripts/submission_kit.py --package-all
```

### 6. Analyse des Manques Mathlib & Lemmes Hallucinés
Analyse les erreurs compilateur de `data/attempts.db` et interroge Loogle pour identifier les lemmes manquants (rapport décisionnel fiable avec détection des namespaces erronés) :
```bash
python3 -B scripts/mathlib_gaps.py
```

### 7. Daemon de Veille & Résolution Autonome
Surveillance périodique, détection d'issues GitHub (watchlist), filtrage strict des cibles `verified: true`, résolution et packaging PR automatique :
```bash
# Exécution d'un cycle unique de travail
python3 -B scripts/daemon.py --once

# Classement économique des cibles vérifiées par ratio rentabilité / faisabilité
python3 -B scripts/rank_targets.py
```

### 8. Génération du Rapport Officiel de Certification
Agrège les preuves certifiées 'axiom-clean' et statistiques dans `BOUNTY_REPORT.md` :
```bash
python3 -B scripts/bounty_report.py
```

---

## 📁 Arborescence du Projet
- `problems/` : Fichiers `.lean` pour chaque problème résolu ou conjecture ouverte (certifiés en prod).
- `notes/` : Énoncés en langage naturel, pistes de recherche, sources et bounties.
- `benchmarks/` :
  - `minif2f.py` : Moteur de benchmark MiniF2F (244 théorèmes) avec pré-vol budgétaire.
  - `minif2f_test.lean` : Cache officiel des 244 théorèmes MiniF2F test.
- `agent/` :
  - `verifier.py` : Connecteur SSH direct avec l'infrastructure Lean 4 / Mathlib.
  - `deepseek_prover.py` : Moteur de formalisation itératif avec feedback compilateur.
  - `planner.py` : `BlueprintPlanner` décomposant un énoncé en lemmes intermédiaires.
  - `retrieval.py` & `loogle.py` : Recherche de lemmes Mathlib via l'API Loogle.
  - `targets.py` : Gestion des cibles, du registre et de la file avec garde-fous `verified`.
  - `watcher.py` : Veille API GitHub sur liste blanche pour repérer les nouveaux besoins.
  - `researcher.py` : Interface CLI d'audit et de déploiement.
- `scripts/` :
  - `daemon.py` : Daemon autonome de veille et de cycle de preuve.
  - `submission_kit.py` : Générateur de kit de PR (zéro commande réseau auto).
  - `mathlib_gaps.py` : Mineur de lemmes manquants depuis la base des tentatives.
  - `rank_targets.py` : Algorithme de ranking des cibles vérifiées.
  - `bounty_report.py` : Générateur de rapport de certification `BOUNTY_REPORT.md`.
  - `deploy_prod.sh` : Script de déploiement synchrone PC -> GitHub -> Prod Proxmox.
  - `check.sh` / `auto_pull_and_check.sh` : Scripts d'audit formel sur le conteneur LXC.
- `targets/` :
  - `registry.yaml` & `queue.yaml` : Registres des cibles (toute entrée externe `verified: false` par défaut).
  - `watchlist.yaml` : Dépôts surveillés par le watcher.
  - `repo_profiles/` : Profils de conventions et gabarits de PR (`mathlib4.yaml`).
- `reports/` : Rapports générés (manques Mathlib, audits).
- `submissions/` : Kits de soumission prêts pour relecture humaine.
- `SunFormal/` : Package racine Lean 4.

---

## 🛡️ Garde-Fous & Principes Opérationnels

1. **Intégrité Absolue des Données** : Aucun montant, URL ou énoncé inventé. Toute cible externe créée automatiquement porte la mention `verified: false` et est ignorée par le daemon tant qu'un humain ne l'a pas validée.
2. **Certification Zéro-Sorry Formelle** : Chaque preuve acceptée subit une vérification stricte `#print axioms` en environnement conteneurisé LXC Proxmox isolé.
3. **Zéro Action Réseau Non Supervisée** : Le kit de soumission génère les branches et templates de PR en local, mais n'exécute aucun appel `git push` ou `gh pr create` sans action explicite de l'opérateur.

