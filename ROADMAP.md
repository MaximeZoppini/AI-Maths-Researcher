# ROADMAP — De la machine qui marche au système qui rapporte

> Suite opérationnelle de `VISION.md.txt`. Rédigé le 2026-09-17, après la campagne 5.8.
> État de départ vérifié : **17/30 MiniF2F certifiés (57 %)**, 258 tentatives tracées,
> $0.98 dépensé, audit `#print axioms` propre en prod.
> Principe directeur : **on arrête de construire des features, on fait tourner et on livre.**

---

## Étape A — Derniers travaux programme (1-2 sessions, puis stop)

Le harnais est fini à 90 %. Il reste exactement 5 choses, toutes petites :

1. **Abandon précoce** — couper la boucle quand le goal state est identique entre deux
   itérations ou que la même erreur revient deux fois. 88 % du budget part dans les
   échecs ; c'est le seul correctif de coût qui compte. (détail : `notes/economics_design.md` §2)
2. **Colonne `difficulty_class`** en base + backfill regex (`mathd_*`/`amc*`/`aime*`/`imo*`)
   + fonction `p_success(classe)`. C'est le modèle de tarification qui permet de décider
   quoi attaquer. (détail : §1.3 du même doc)
3. **Parallélisme au niveau problèmes** — 4-8 workers threads (98 % du temps = attente
   API), un seul thread écrivain SQLite (ou WAL + `check_same_thread=False`), pool de
   2-3 REPL sous verrou. Campagne 244 : 8 h → ~1-2 h.
4. **Garde-fou budget** — lire le solde via l'API DeepSeek (`GET /user/balance`) avant
   chaque campagne et à intervalle ; arrêt propre sous un seuil ($0.50). Plafond de coût
   par campagne dans la config. Corriger au passage le calcul de coût (tenir compte des
   `prompt_cache_hit_tokens` du champ `usage` — on surestime de 2× actuellement).
5. **Une seule métrique officielle** — le taux sur un set figé de problèmes distincts
   (aujourd'hui : 17/30). Bannir des rapports les chiffres qui mélangent sous-lemmes,
   doublons et problèmes maison (le « 55.3 % » du dernier commit). Un jury vérifiera.

**Règle : après l'étape A, tout nouveau développement du harnais est un refus par défaut.**
Le retrieval amélioré, les modèles spécialisés etc. n'entrent que si une campagne
démontre qu'ils sont le facteur bloquant.

---

## Étape B — La campagne 244 complète (la mesure de référence)

- Prérequis : étape A + top-up **$10-15** (coût réel estimé $4-6).
- `python3 -B -m benchmarks.minif2f --limit 244 --attempts 3 --pass-k 2 --skip-solved`
  (une nuit en séquentiel, 1-2 h si A.3 est fait).
- Livrables : tag git `minif2f-244-v1`, rapport figé dans `reports/`, README mis à jour
  avec le chiffre + méthodo reproductible (modèle, config, commit Mathlib).
- Ce chiffre décide de la suite : ≥45 % → le système est compétitif pour les cibles
  volume ; <35 % → le facteur bloquant est le retrieval ou le modèle, retour ciblé en A.

---

## Étape C — Le mode prod autonome (le daemon)

### Ce que « prod » veut dire ici

Un service sur le LXC (systemd timer, déjà l'habitude de la maison) qui, en continu :
1. lit une **file de cibles** (`targets/queue.yaml`) — remplie à la main ou par le
   backlog des problèmes non résolus,
2. calcule la config via la politique valeur/`p_success` (étape A.2),
3. lance la recherche de preuve, certifie en prod, commit, met à jour les rapports,
4. envoie un résumé quotidien (mail ou webhook Discord/Telegram : résolus, coût, solde),
5. s'arrête seul si : solde API < seuil, fichier `STOP` présent, ou file vide.

### Les portes à franchir AVANT de le lancer (gates)

| Gate | Pourquoi c'est bloquant |
| :--- | :--- |
| A.1 abandon précoce | sans lui, le daemon brûle 88 % du budget dans les échecs, sans surveillance |
| A.4 garde-fou solde | un daemon sans plafond + une clé API = découvert garanti |
| Timeout REPL + watchdog | ✅ déjà fait (Phase 5) — vérifier le auto-restart sur 24 h |
| DB unique ancrée | vérifier que `DB_PATH` est absolu (le daemon aura un cwd différent !) |
| Kill-switch documenté | `touch STOP` + notification testée |

**Estimation réaliste : le daemon est lançable une session après la fin de l'étape A.**
C'est ~150 lignes de Python autour de l'existant, pas un chantier.

### Ce que le daemon ne fait JAMAIS (périmètre de sécurité)

- Il ne **cherche pas** de problèmes sur internet. Il consomme uniquement le registre
  relu à la main. Un agent qui ingère des énoncés du web et les exécute est une porte
  ouverte à l'injection de prompt — et une erreur d'interprétation d'un énoncé mal
  scrapé produit des preuves sans valeur.
- Il ne **soumet rien** à l'extérieur : pas de PR automatique, pas de post automatique.
  Il pousse sur TON repo, c'est tout. La sortie vers le monde passe par un humain.

Autonomie = le **milieu** du pipeline (résolution, certification, reporting).
Les extrémités (sourcing, soumission) restent humaines — par design, pas par flemme.

---

## Étape D — La chaîne de soumission : les exigences réelles

### D.1 Mathlib (la cible crédibilité)

Exigences concrètes d'une PR mathlib4 :
- Fork + branche sur `leanprover-community/mathlib4`, licence Apache 2.0.
- **Style guide strict** : conventions de nommage (snake_case descriptif du contenu
  mathématique), docstrings `/-- -/` obligatoires, 100 colonnes, pas de
  `set_option linter.* false` (nos fichiers actuels en sont pleins — à nettoyer avant
  toute PR), `#lint` propre.
- **Transparence IA** : la communauté a des règles explicites sur les contributions
  assistées par IA — divulguer, et être capable de défendre chaque ligne en revue.
- Revue par des mainteneurs **bénévoles** : délai en semaines, discussion en anglais
  sur Zulip. C'est un processus social autant que technique.
- Workflow : le pipeline propose (agrégateur d'`unknown identifier` → candidats de
  lemmes manquants → vérif Loogle qu'ils n'existent pas), l'humain choisit, polit, soumet.
- Objectif : **3-5 PRs en 6 mois.** Le volume y est contre-productif.

### D.2 Bounties d'écosystème (la cible argent)

- Sourcing : lecture hebdo manuelle (Zulip Lean `#general`/annonces de projets, repos de
  formalisation avec issues à prime). Chaque cible → une fiche dans `targets/registry.yaml`
  avec : énoncé, montant, deadline, **conditions de soumission exactes** (repo cible,
  format, licence, attribution), classe de difficulté.
- `scripts/rank_targets.py` trie par espérance de gain `p_success × montant`.
- Soumission : toujours une PR/message rédigé et relu par l'humain, avec le hash de
  commit du repo prod comme preuve de certification.
- ⚠️ Vigilance sur les prix annoncés sans règlement clair (le « Justin Sun Prize » des
  notes initiales : vérifier existence, règlement et payeur avant d'investir une heure).
- Ce qui n'est **pas** soumissible : FrontierMath (évaluation fermée d'Epoch AI, pas un
  bounty ouvert), les benchmarks académiques (PutnamBench sert à mesurer, pas à gagner).

### D.3 Le déclencheur

L'étape D démarre **dès maintenant en parallèle** — elle ne dépend pas du code :
créer `targets/registry.yaml`, y mettre les 2-3 premières cibles réelles sourcées à la
main, et nettoyer un premier lemme candidat pour Mathlib. Le pipeline technique les
rejoindra quand A+B seront finis.

---

## Séquence récapitulative

```
Semaine 1 : A (5 correctifs) ──→ B (campagne 244, une nuit)
Semaine 2 : C (daemon, gates vérifiées) + D.3 (registre manuel, 1er lemme Mathlib)
Ensuite   : le daemon tourne, l'humain source les cibles et signe les sorties.
            Le code n'évolue plus que sur preuve (une campagne qui démontre un blocage).
```

Le projet change de nature ici : jusqu'à maintenant le livrable était du code ;
à partir de maintenant le livrable est **des preuves certifiées et des chiffres publics**.
