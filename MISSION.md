# MISSION — Corrections critiques & derniers chantiers avant mise en route

> Ce fichier remplace `VISION.md.txt` et `ROADMAP.md` (supprimés — l'historique git les garde).
> C'est LA liste de travail courante. Exécuter dans l'ordre. Chaque tâche a des critères
> d'acceptation vérifiables — une tâche sans ses critères remplis n'est pas terminée.

---

## ⚠️ RÈGLES ABSOLUES (à respecter dans toute cette mission et après)

1. **INTERDICTION D'INVENTER DES DONNÉES.** Aucun bounty, montant, deadline, énoncé ou
   URL ne doit être créé s'il n'a pas été fourni par l'utilisateur ou copié à
   l'identique depuis une source officielle vérifiable (fichier du dataset, repo officiel).
   Le registre actuel contient 5 entrées fabriquées présentées comme « vérifiées » —
   c'est exactement ce qui ne doit plus jamais se produire.
2. **Toute cible externe porte un champ `verified: false` par défaut.** Seul l'utilisateur
   le passe à `true` à la main. Le daemon et `rank_targets.py` IGNORENT toute entrée
   non vérifiée.
3. **Les énoncés de benchmark viennent du dataset, jamais réécrits.** Source unique :
   `benchmarks/minif2f_test.lean` (cache du repo officiel google-deepmind/miniF2F).
4. **Aucune action externe automatique** : pas de PR hors de ce repo, pas de post,
   pas de scraping hors whitelist. (Déjà en place — ne pas régresser.)
5. **Métrique officielle unique** : « X/N problèmes distincts du set MiniF2F test,
   set figé, config donnée ». Interdiction de publier un taux mélangeant sous-lemmes,
   doublons ou problèmes maison (le « 55,3 % » du commit a0d26a6 est à bannir).

---

## TÂCHE 1 — Purger le registre fabriqué (CRITIQUE, à faire en premier)

Fichiers : `targets/registry.yaml`, `targets/queue.yaml`

1. Supprimer les 3 entrées à valeur inventée : `aime_1984_p7` (« $150 »),
   `imo_shortlist_algebra_candidate` (« $500 »), `mathlib_nat_mul_self_parity` (« $10 »).
   Les montants ET les énoncés sont faux (ex. le « aime_1984_p7 » du registre est une
   induction triviale, pas le vrai problème AIME).
2. Pour les entrées `benchmark` restantes : remplacer l'énoncé par la déclaration
   EXACTE extraite de `benchmarks/minif2f_test.lean` (réutiliser `parse_theorems`).
   Si le nom n'existe pas dans le dataset, supprimer l'entrée.
3. Ajouter le champ `verified: false` au schéma (`agent/targets.py` : dataclass + load/save),
   avec `verified: true` uniquement pour les entrées benchmark dont l'énoncé vient du
   dataset (vérifiable par diff).
4. Corriger l'en-tête du fichier : remplacer « Sourcing manuel vérifié » par
   « Les entrées verified: false sont des brouillons EN ATTENTE de validation humaine.
   Ne jamais marquer verified: true automatiquement. »
5. `scripts/daemon.py` et `scripts/rank_targets.py` : filtrer `verified: true` uniquement.
   Le daemon loggue et saute les entrées non vérifiées.

**Acceptation :** `python3 -B scripts/rank_targets.py` n'affiche plus aucun montant
inventé ; `grep -c "verified: false" targets/registry.yaml` ≥ 0 et le daemon en `--run-once`
saute ces entrées avec un message explicite.

---

## TÂCHE 2 — Métrique officielle dans le README

1. Section « Résultats » du `README.md` : remplacer toute mention de taux par la
   métrique officielle : **17/30 problèmes distincts des 30 premiers du set MiniF2F
   test (57 %)**, avec : modèle (`deepseek-chat` + escalade `deepseek-reasoner`),
   pass@2, 3 tentatives, blueprint activé, commit Mathlib, date.
2. `scripts/bounty_report.py` : vérifier que le rapport n'affiche plus de doublons
   (une seule entrée par théorème, la meilleure) ni de taux mélangé. Corriger sinon.

**Acceptation :** aucun « 55,3% » ni « Problèmes résolus 21/38 » dans le repo ;
`grep -rn "55.3" *.md` vide.

---

## TÂCHE 3 — Watcher whitelisté (nouveau, ~1 session)

Nouveau fichier : `agent/watcher.py` + config `targets/watchlist.yaml`

1. `watchlist.yaml` : liste de sources approuvées à la main, format :
   ```yaml
   - repo: leanprover-community/mathlib4        # exemple de structure, PAS une entrée à créer
     labels: ["help-wanted"]
     kind_hint: mathlib
   ```
   **Livrer le fichier VIDE avec un exemple commenté.** C'est l'utilisateur qui le remplit.
2. `agent/watcher.py` : pour chaque source, appeler l'API GitHub REST
   (`GET /repos/{repo}/issues?labels=...&since=...`, token optionnel via `.env`
   `GITHUB_TOKEN`), détecter les issues nouvelles depuis le dernier passage
   (état dans `data/watcher_state.json`).
3. Pour chaque nouveauté : créer une fiche brouillon dans `targets/registry.yaml` avec
   `verified: false`, `source_url` réel, titre de l'issue, PAS d'interprétation du
   contenu (copier le titre + l'URL, ne pas tenter d'extraire un énoncé Lean).
4. Intégration daemon : un appel watcher par cycle (avec throttle 24 h), résumé dans
   le rapport quotidien : « N nouvelles cibles en attente de validation ».
5. Sécurité : le contenu des issues est de la DONNÉE. Ne jamais exécuter, formaliser ou
   prouver quoi que ce soit depuis une fiche `verified: false`.

**Acceptation :** avec une watchlist de test pointant sur un repo public, le watcher
crée des fiches `verified: false` correctes ; avec la watchlist vide, il ne fait rien ;
le daemon ne traite jamais ces fiches.

---

## TÂCHE 4 — Kit de soumission (nouveau, ~1 session)

Nouveau : `scripts/submission_kit.py` + profils `targets/repo_profiles/mathlib4.yaml`

1. Profil par repo cible (commencer par mathlib4) : conventions de nommage, exigences
   de style (docstring `/-- -/` obligatoire, pas de `set_option linter.* false`,
   100 colonnes), template de corps de PR (avec section divulgation d'assistance IA),
   checklist de revue.
2. `submission_kit.py --target <nom>` génère dans `submissions/<nom>/` :
   - le fichier Lean nettoyé aux normes du profil (linter options retirées, docstring
     exigée — échouer avec un message clair si elle manque),
   - `PR_BODY.md` rempli depuis le template,
   - `CHECKLIST.md` (relecture humaine),
   - `commands.sh` : les commandes git/gh prêtes (fork, branche, push, `gh pr create`)
     — **généré mais JAMAIS exécuté**.
3. Garde-fou dans le code : `submission_kit.py` ne doit contenir AUCUN appel réseau ni
   subprocess vers git/gh. Il écrit des fichiers, c'est tout.

**Acceptation :** lancé sur une preuve existante de `problems/`, le kit produit les
4 fichiers ; aucun `subprocess` vers git/gh dans le module (vérifiable par grep).

---

## TÂCHE 5 — Mineur de lemmes manquants (nouveau, ~0.5 session)

Nouveau : `scripts/mathlib_gaps.py`

1. Requêter `data/attempts.db` : extraire tous les messages `unknown identifier`/
   `unknown constant` de `compiler_errors`, agréger par identifiant, trier par fréquence.
2. Pour le top 20 : interroger Loogle (réutiliser `agent/retrieval.py`) pour vérifier
   si un lemme équivalent existe. Marquer `exists_in_mathlib: probable/absent/inconnu`.
3. Sortie : `reports/mathlib_gaps_<date>.md` — tableau identifiant / fréquence /
   statut Loogle / fichiers-problèmes concernés. AUCUNE génération de preuve ni de PR :
   c'est un rapport pour décision humaine.

**Acceptation :** le rapport se génère depuis la base actuelle (258 tentatives) et
liste au moins les identifiants hallucinés réels des campagnes passées.

---

## TÂCHE 6 — Préparation campagne 244 (NE PAS LANCER)

1. Vérifier que `--limit 244` couvre bien tout le set test (le parser doit retourner
   244 théorèmes ; sinon corriger le regex de `parse_theorems`).
2. Estimer le coût affiché en début de campagne (nb problèmes restants × coût moyen
   par problème depuis la base) et l'afficher avec le solde courant ; refuser de
   démarrer si solde < estimation + $0.50.
3. **Ne pas lancer la campagne** : solde actuel insuffisant (~$1.50), l'utilisateur
   fera le top-up et la lancera lui-même :
   `python3 -B -m benchmarks.minif2f --limit 244 --attempts 3 --pass-k 2 --skip-solved`

**Acceptation :** lancement à sec (`--dry-run` à ajouter) affichant : problèmes
restants, coût estimé, solde, GO/NO-GO — sans aucun appel LLM.

---

## Après cette mission

Plus AUCUN développement du harnais sans preuve qu'un composant est le facteur
bloquant (une campagne qui le démontre). La séquence suivante appartient à
l'utilisateur : top-up → campagne 244 → chiffre public dans le README → remplissage
manuel de la watchlist et du registre → première PR Mathlib via le kit (1 lemme choisi
dans le rapport de la tâche 5, poli à la main).
