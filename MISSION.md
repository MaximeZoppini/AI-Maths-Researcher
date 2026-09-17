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

## 🔴 AUDIT POST-MISSION (2026-09-17) — 2 correctifs avant mise en route

### TÂCHE 7 — BLOQUANT : remplacer le parseur YAML maison par PyYAML

`agent/targets.py` : `parse_simple_yaml` est cassé. Quand une entrée contient
`statement: |`, toutes les clés suivantes (indentées de 2 espaces) sont absorbées
dans le bloc multiligne. Conséquences mesurées :
- `registry.yaml` : `verified: true` n'est JAMAIS lu → `load_targets` retourne
  `verified=False` pour 5 entrées sur 5, `rank_targets` et le daemon ignorent tout,
  y compris les cibles valides. Le système est inerte.
- Les métadonnées (`kind`, `value_usd`, `source_url`…) se retrouvent DANS le texte
  de l'énoncé (vérifié : `statement` de `mathd_algebra_392` contient
  `kind: benchmark\nvalue_usd: 0.0…`).
- Le parseur fait `line.strip()` sur chaque ligne → l'indentation Lean des énoncés
  est détruite (un `sorry` désindenté après `by` n'est plus valide).

**Fix :** PyYAML 6.0.3 est installé sur la machine. Supprimer `parse_simple_yaml`
et `dump_simple_yaml`, utiliser `yaml.safe_load` / `yaml.safe_dump`
(`default_flow_style=False, allow_unicode=True`, style `|` pour `statement`).
Ne PAS réécrire un parseur à la main.

**Acceptation :** `load_targets(registry)` retourne `verified=True` pour les 2 entrées
benchmark ; `statement` ne contient aucune clé de métadonnée ; l'indentation Lean est
préservée à l'octet près (round-trip load→save→load identique) ;
`python3 -B scripts/rank_targets.py` classe les 2 cibles vérifiées.

### TÂCHE 8 — Fiabiliser le rapport mathlib_gaps (conclusions trompeuses)

`scripts/mathlib_gaps.py` marque « absent » 14 identifiants sur 14 — faux. Vérifié :
`Real.sq_abs` est marqué absent alors que le lemme existe sous le nom `sq_abs`
(la requête Loogle sur le nom exact échoue, donc tout nom mal préfixé passe pour
un trou Mathlib). Un rapport qui dit « cible prioritaire pour PR » sur un lemme
existant conduit à une PR refusée.

**Fix :**
1. Filtrer les noms d'hypothèses locales (`hy1`, `hc2`… : minuscule + court +
   sans namespace) qui ne sont pas des candidats.
2. Pour chaque identifiant : requêter Loogle sur le nom exact PUIS sur le dernier
   segment (`Real.sq_abs` → `sq_abs`). Si le segment matche : statut
   `existe_sous_autre_nom` avec le nom trouvé (info précieuse : c'est un correctif
   de prompt/retrieval, pas un trou Mathlib).
3. Renommer le statut `absent` en `introuvable_via_loogle` — Loogle qui ne trouve
   pas ≠ le lemme n'existe pas. Ajuster la légende du rapport.

**Acceptation :** `Real.sq_abs` → `existe_sous_autre_nom (sq_abs)` ; `hy1`/`hc2`
absents du rapport ; regénérer `reports/mathlib_gaps_*.md` et supprimer les anciens
rapports trompeurs.

---

## 💰 TÂCHE 9 — Réduction de la consommation API (audit du 2026-09-17 soir) — ✅ TERMINÉE

Constat mesuré sur `data/attempts.db` (258 tentatives, $0.98 dépensés au total) :
- `deepseek-reasoner` = **90 % de la dépense** ($0.886) pour 32 appels ; ses ÉCHECS
  seuls = **79 % du budget total** ($0.774 sur 25 tentatives ratées).
- Les échecs du reasoner divaguent jusqu'à ~13 200 tokens de sortie en moyenne
  (proche du plafond 16 384) ; ses succès n'en consomment que ~6 400.
- La classe `imo` a englouti **$0.451 (46 % du budget) pour ZÉRO théorème principal
  certifié** (2 sous-lemmes orphelins seulement, inutilisables sans le théorème final).

Correctifs implémentés et validés :

1. **Plafond quotidien absolu dans le daemon (la garantie 24/24) [✅ IMPLÉMENTÉ] :** Nouvelle gate :
   `SELECT SUM(cost_usd) FROM attempts WHERE timestamp > now-24h` ≥ `--daily-budget`
   (défaut **$0.30/jour**) → le daemon se met en veille jusqu'à la fenêtre suivante,
   loggue et notifie. Coût pire-cas ainsi borné à ~$9/mois quoi qu'il arrive.
2. **Escalade conditionnée au `p_success` de la classe [✅ IMPLÉMENTÉ] :** Ne JAMAIS appeler
   `deepseek-reasoner` si `p_success(difficulty_class) < 0.15` (aujourd'hui : imo),
   SAUF si la cible est un bounty `verified: true` à valeur non nulle.
   Économie rétroactive mesurée : ~45 % du budget pour zéro certification perdue.
3. **`max_tokens` du reasoner : 16384 → 8192 [✅ IMPLÉMENTÉ] :** Les preuves qui réussissent tiennent
   en ~6 400 tokens ; au-delà, le modèle divague puis échoue. Un raisonnement coupé
   à 8k = échec plus rapide ET deux fois moins cher. Économie : ~25-30 %.
4. **Blueprint conditionné [✅ IMPLÉMENTÉ] :** Le repli blueprint après échec direct double la dépense
   sur les problèmes sans espoir ($0.19 de sous-lemmes imo orphelins). Règle : blueprint
   seulement si `p_success(classe) ≥ 0.15` OU cible à valeur ; jamais sur un benchmark
   de classe imo.
5. **Pré-passe d'automation gratuite AVANT tout appel LLM [✅ IMPLÉMENTÉ] :** Cascade REPL :
   `omega` / `norm_num` / `ring` / `linarith` / `nlinarith` / `decide` / `aesop` (~2 s, $0).
   Une grande partie des `mathd` ($0.154 dépensés) tombe gratuitement.
6. **Dégraisser l'historique des prompts [✅ IMPLÉMENTÉ] :** iter3 = 3 358 tokens de prompt (3,6× iter1)
   car on réinjecte le code raté complet des 2 dernières tentatives. Ne garder que :
   dernier code raté + messages d'erreur + goal states (pas l'avant-dernier code).
7. **Prise en compte des heures creuses DeepSeek (-50%) [✅ IMPLÉMENTÉ] :**
   Grille tarifaire vérifiée (week-end entier + nuits UTC). Fonction `is_deepseek_offpeak()`
   et argument `--prefer-offpeak` intégrés dans le daemon.

**Acceptation validée :**
- Test REPL de pré-passe gratuite certifié à $0.00 USD (0 token).
- Blocage strict de l'escalade Reasoner sur classe `imo` validé.
- Gate `--daily-budget 0.30` du daemon testée avec arrêt immédiat si budget 24h dépassé.
- Conditionnement Blueprint sur `imo` actif.

---

## TÂCHE 10 — Migration des identifiants de modèles DeepSeek (découvert à l'audit du soir) — ✅ TERMINÉE

Vérifié le 2026-09-17 via `GET https://api.deepseek.com/models` : l'API ne sert plus
officiellement que **`deepseek-flash`** et **`deepseek-v4-pro`**. Nos appels
`deepseek-chat` / `deepseek-reasoner` fonctionnent via des alias hérités — fragile
(peuvent disparaître sans préavis) et nos constantes de prix dans `prover.py` sont fausses.

Réalisations implémentées & validées :

1. **IDs officiels [✅ IMPLÉMENTÉ] :** Bascule de `LLMProvider` sur `deepseek-flash`
   (remplace chat) et `deepseek-v4-pro` (remplace reasoner). Rétrocompatibilité
   assurée via dictionnaire `DEEPSEEK_MODEL_ALIASES` pour router les anciens noms.
2. **Grille officielle & heures creuses (-50%) [✅ IMPLÉMENTÉ] :** Constantes de coût
   actualisées avec cache hit/miss séparés et intégration dynamique de `is_deepseek_offpeak()`
   (heures creuses les nuits UTC et tout le week-end samedi/dimanche).
3. **Micro-benchmark de non-régression [✅ VALIDÉ] :**
   - `mathd_algebra_141` : Résolu en 1 itération via `deepseek-flash` ($0.00119 USD).
   - `mathd_algebra_33` : Réparation réussie en 2 itérations via `deepseek-flash` ($0.00472 USD).
   - `mathd_algebra_478` : Résolu en 1 itération via `deepseek-flash` ($0.00057 USD).
   - 100 % de succès certifiés sans sorry par le Juge Final.
4. **Plafond tokens & contrôle pro [✅ IMPLÉMENTÉ] :** `max_tokens` maintenu à 8192
   pour `deepseek-v4-pro`, escalade conditionnée à $p_{\text{success}} \ge 15\%$
   ou bounty rémunéré.

**Acceptation validée :** Tous les appels API utilisent les identifiants officiels
de `GET /models` ; calcul de coût actualisé avec réduction -50 % en heures creuses.

---

## Après cette mission

Plus AUCUN développement du harnais sans preuve qu'un composant est le facteur
bloquant (une campagne qui le démontre). La séquence suivante appartient à
l'utilisateur : top-up → campagne 244 → chiffre public dans le README → remplissage
manuel de la watchlist et du registre → première PR Mathlib via le kit (1 lemme choisi
dans le rapport de la tâche 5, poli à la main).
