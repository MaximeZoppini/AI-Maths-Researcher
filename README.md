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

## 🚀 Commandes & Utilisation de l'Agent

### 1. Vérifier un problème spécifique sur la prod
Envoie le code au compilateur Lean 4 de l'infrastructure Proxmox et renvoie le diagnostic exact en quelques secondes :
```bash
python3 -m agent.researcher --verify problems/Problem1_EvenSquare.lean
python3 -m agent.researcher --verify problems/Problem2_ModThreeSquare.lean
python3 -m agent.researcher --verify problems/Problem3_Inequalities.lean
```

### 2. Audit formel global en Prod (Garantie Anti-Sorry / Anti-Axiom)
Compile tout le projet et valide l'absence stricte de `sorry` ou `axiom` :
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

---

## 📁 Arborescence du Projet
- `problems/` : Fichiers `.lean` pour chaque problème résolu ou conjecture ouverte.
- `notes/` : Énoncés en langage naturel, pistes de recherche, sources et bounties.
- `agent/` :
  - `verifier.py` : Connecteur SSH direct avec l'infrastructure Lean 4 / Mathlib.
  - `researcher.py` : Interface CLI de recherche, validation et déploiement.
- `scripts/` :
  - `check.sh` : Script de build et d'audit d'axiomes.
  - `deploy_prod.sh` : Script de déploiement synchrone PC -> GitHub -> Prod Proxmox.
  - `auto_pull_and_check.sh` : Script exécuté par le timer systemd en prod.
- `SunFormal/` : Package racine Lean 4.
