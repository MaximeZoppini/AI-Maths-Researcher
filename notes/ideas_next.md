# Idées pour la suite (post-campagne MiniF2F 244)

> Notes de Claude, 2026-09-17, pendant que la campagne 5.8 tourne. Rien d'urgent,
> à trier ensemble après les résultats. Classées par ratio impact/effort.

## ⚠️ À vérifier dès la fin de la campagne (avant tout le reste)

### 1. `DB_PATH` est un chemin RELATIF → les données se dispersent selon le cwd
`agent/db.py:13` : `DB_PATH = Path("data/attempts.db")`. Si un process tourne avec un
autre répertoire courant, il écrit **ailleurs**. Indice concret : `/tmp/ai_maths_data/`
contient un `attempts.db`, un `BOUNTY_REPORT.md` et un `test.db` modifiés APRÈS la
migration vers `data/` — il y a probablement des campagnes écrites dans deux bases.
- Fix : ancrer sur le projet — `DB_PATH = Path(__file__).resolve().parent.parent / "data" / "attempts.db"`.
- Puis fusionner l'ancienne base `/tmp/ai_maths_data/attempts.db` dans `data/` (INSERT
  SELECT, dédup sur timestamp+problem_name) pour ne pas perdre l'historique des
  premières campagnes.

### 2. `check.sh` compile TOUT `problems/` à chaque audit
Chaque succès MiniF2F ajoute un fichier. À 100+ preuves, l'audit prod va durer des
heures et le timer systemd de 60 s va se marcher dessus. Séparer : `problems/` (curaté,
bounties) vs `solutions/minif2f/` (archive de campagne, compilée une fois, pas à chaque sync).

## Gains rapides et gratuits

### 3. Pré-passe "automation gratuite" avant tout appel LLM
Avant d'appeler DeepSeek, tirer dans le REPL la cascade `omega` / `norm_num` /
`nlinarith` / `aesop` / `decide` / `exact?` directement sur l'énoncé. Une part
non négligeable de MiniF2F tombe à l'automation pure : $0, ~1 s, et ça réserve le
budget LLM aux problèmes qui en valent la peine. (Le `_fallback_tactic_generator`
existe déjà dans prover.py mais n'est utilisé QUE sans clé API — en faire l'étape 0
systématique.)

### 4. Cache de preuves : ne jamais re-prouver un énoncé déjà certifié
`mathd_algebra_478` a été re-prouvé 5 fois (5 appels API pour rien). Avant la boucle :
lookup en base sur le hash de l'énoncé normalisé → si preuve certifiée existante, la
resservir. Utile aussi pour les lemmes de blueprint qui reviennent d'un problème à l'autre.

### 5. Reproductibilité des campagnes
Chaque ligne en base et chaque rapport devraient porter : version exacte du modèle
(l'API renvoie `model` dans la réponse), commit Mathlib, commit du repo, config
(attempts, blueprint on/off). Sinon deux campagnes ne sont pas comparables — et un
chiffre public doit être reproductible.

## Le cerveau (après les résultats de la 244)

### 6. Taxonomie d'erreurs → routage de stratégie
Classer chaque échec en base : `unknown_identifier` / `type_mismatch` / `timeout` /
`unsolved_goals` / `syntax`. Puis router : identifiant inconnu → retrieval ciblé et
retry chat ; unsolved goals profonds → reasoner ; timeout tactique → interdire la
tactique dans le prompt suivant. Aujourd'hui la réparation est aveugle au type d'erreur.
La base contient déjà tout ce qu'il faut pour construire cette taxonomie a posteriori.

### 7. Few-shot minés dans notre propre base
Extraire les paires (erreur → correction gagnante) des campagnes et injecter les 2-3
plus proches dans le prompt de réparation. Le système apprend de ses campagnes sans
fine-tuning.

### 8. Parallélisme au niveau PROBLÈMES, pas seulement pass@k
La campagne est séquentielle : 244 problèmes × reasoner lent = des heures. N REPL
(3-4) en pool + N problèmes en parallèle = campagne divisée par N. Attention à la RAM
du LXC (chaque REPL avec Mathlib chargé pèse plusieurs Go).

### 9. Worker "spécialiste Lean" dans l'escalade
Étage 3 après chat → reasoner : un modèle spécialisé (DeepSeek-Prover-V2, Kimina-Prover)
via endpoint tiers (poids ouverts). Ces modèles dominent miniF2F (>80 %) ; le harnais
actuel (REPL + juge prod) peut les brancher sans rien changer d'autre que `LLMProvider`.

## Vers les bounties réels

### 10. Sourcing automatique des cibles
Un scraper hebdo : Zulip Lean #bounties, issues GitHub taguées bounty, annonces de
prix de formalisation → fiche dans `notes/bounties/` avec énoncé, deadline, montant,
faisabilité estimée. Aujourd'hui le sourcing (étape 1 du pipeline) est 100 % manuel.

### 11. Hygiène Mathlib pour les futures PRs
Passer les preuves candidates au linter Mathlib (`#lint`), noms conformes aux
conventions, pas de `set_option linter... false`. Une PR Mathlib se juge autant sur
le style que sur la validité. Objectif concret : la première PR Mathlib d'ici fin
octobre, sourcée depuis un lemme manquant détecté par le retrieval.

### 12. PutnamBench comme mesure du plafond
Après la 244 : PutnamBench (658 problèmes Putnam). Attendu réaliste : 5-15 % en
escalade complète. C'est le chiffre qui dira si on est au niveau des bounties sérieux
ou pas encore — et c'est OK s'il est bas, il est bas pour tout le monde.
