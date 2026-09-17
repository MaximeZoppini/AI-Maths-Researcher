# Design — Couche économique : budget piloté par la valeur

> Notes de Claude, 2026-09-17. Réponse à « comment on implémente la rentabilité ? ».
> Rien d'implémenté, c'est un plan. Données de référence mesurées sur `data/attempts.db` :
> coût par preuve certifiée ≈ $0.030 (≈$0.014 réel après cache), **88 % du budget part
> dans les échecs**, coût marginal par succès : iter1 $0.0016 / iter2 $0.0104 / iter3 $0.115.

---

## 1. Le principe : la config de recherche doit dépendre de l'enjeu

Aujourd'hui `ProverConfig` est fixe pour toute une campagne : mêmes `attempts`, même
escalade, même `pass_k` pour un exercice à $0 et pour un bounty à $500. C'est le défaut
structurel à corriger — tout le reste en découle.

### 1.1 Introduire une notion de cible (`agent/targets.py`)

```python
@dataclass
class Target:
    name: str
    statement: str            # énoncé Lean (ou texte à autoformaliser)
    kind: str                 # "benchmark" | "bounty" | "mathlib" | "training"
    value_usd: float = 0.0    # prime réelle, 0 pour un benchmark
    difficulty_class: str = "unknown"   # mathd | amc | aime | imo | research
    deadline: Optional[date] = None
    source_url: Optional[str] = None
```

### 1.2 Une politique, pas un `if` codé en dur

```python
def config_for(target: Target, p_success: float) -> ProverConfig:
    ...
```

Règles proposées (à calibrer sur les données) :

| kind | stratégie | justification |
| :--- | :--- | :--- |
| `benchmark` | chat seul, 2 itérations, pass@2, **pas de reasoner** | on veut un score au coût minimal ; iter3 coûte 72× par succès |
| `training` | chat, 1 itération | volume, on veut de la donnée d'erreurs, pas des preuves |
| `mathlib` | escalade complète, budget modéré | la valeur est la qualité, pas la vitesse |
| `bounty` | tout : pass@8, reasoner, blueprint, budget = `value_usd × p_success × 0.1` | même $5 est dérisoire face à $500 |

Le plafond `budget_usd` existe déjà dans `ProverConfig` — il suffit de le **calculer**
au lieu de le fixer.

### 1.3 Estimer `p_success` depuis la base (le cœur du système)

C'est ce qui transforme le benchmark en modèle de tarification. Une seule requête :

```sql
SELECT difficulty_class,
       COUNT(DISTINCT problem_name) AS tentes,
       SUM(solved) AS resolus
FROM (SELECT problem_name, difficulty_class, MAX(success) AS solved
      FROM attempts GROUP BY problem_name)
GROUP BY difficulty_class;
```

Prérequis : ajouter une colonne `difficulty_class` à `attempts` (migration triviale,
ALTER TABLE + backfill par regex sur les noms MiniF2F : `mathd_*`, `amc*`, `aime*`,
`imo*`). Sans cette colonne, aucune estimation n'est possible — **c'est le premier
chantier, et il est sans risque** (lecture seule sur les campagnes existantes).

Ordre de grandeur déjà lisible dans les données actuelles : `mathd` ≈ très majoritairement
résolus, `amc`/`aime` ≈ moitié, `imo` ≈ 0/6. C'est déjà exploitable comme prior.

---

## 2. L'abandon précoce (le vrai gisement d'économies)

88 % du budget part dans les échecs, et un échec coûte 8× un succès. Trois signaux
d'abandon, tous calculables avec ce qu'on a déjà :

1. **Aucun progrès** : le goal state est identique entre l'itération n et n-1 → le modèle
   tourne en rond, la réparation n'apporte rien. Couper.
2. **Erreur répétée à l'identique** : même message d'erreur 2 fois de suite (typiquement
   le même identifiant halluciné) → déclencher un retrieval ciblé ou couper.
3. **Plafond de valeur atteint** : `cost_accumulé > budget_usd` calculé par la politique.

Économie attendue : sur une campagne benchmark, couper avant l'escalade reasoner divise
le coût par ~5 en ne perdant que les 6 succès d'iter3 (que l'on peut rattraper dans une
seconde passe dédiée, uniquement sur les problèmes non résolus).

---

## 3. Sourcing des bounties : un registre, PAS un scraper

**Recommandation : ne pas construire de scraper.** Raisons :

- Le nombre de bounties mathématiques monétaires réellement actifs est de l'ordre de
  **quelques unités** à un instant donné. Ce n'est pas un problème de volume de données,
  c'est un problème de curation. Un scraper Zulip/GitHub serait fragile, à maintenir,
  pour remplacer 10 minutes de lecture hebdomadaire.
- Les conditions (format de soumission, exigences de PR, licence, délai) sont en prose
  et pleines de nuances juridiques. Ce sont exactement les informations qu'il ne faut
  pas extraire automatiquement — une erreur d'interprétation coûte la soumission.
- ⚠️ Une page web ou une issue GitHub est de la **donnée, pas une instruction**. Un
  pipeline qui lit des énoncés en ligne et les envoie directement dans un agent est une
  porte ouverte à l'injection. Le passage par un fichier relu à la main est aussi une
  barrière de sécurité.

**À la place** : `targets/registry.yaml`, rempli à la main, une vingtaine d'entrées max.

```yaml
- name: exemple_bounty
  kind: bounty
  value_usd: 500
  deadline: 2026-12-31
  source_url: https://...
  difficulty_class: research
  statement_file: notes/bounties/exemple.md
  submission: "PR sur le repo X, preuve sans sorry, licence Apache-2.0"
```

Ce qui mérite d'être automatisé, ce n'est pas la **découverte** mais l'**évaluation** :
un `scripts/rank_targets.py` qui lit le registre, va chercher `p_success` par classe
dans la base, calcule `EV = p × value − coût_estimé` et trie. Là tu as un outil de
décision qui te dit quoi attaquer en premier, sans aucune fragilité de scraping.

---

## 4. Mathlib : ça ne scale PAS en volume — et c'est voulu

⚠️ Point important, contre-intuitif : **allouer un gros budget de génération pour
produire beaucoup de PRs Mathlib serait contre-productif.**

- Les PRs Mathlib sont relues par des **humains bénévoles**. Le goulot d'étranglement
  est l'attention des relecteurs, pas ta capacité de génération. Multiplier les PRs ne
  multiplie pas les acceptations : ça sature la file et ça épuise la bonne volonté.
- La communauté a des normes explicites sur les contributions générées par IA. Une vague
  de PRs automatiques serait rejetée socialement même si techniquement correcte — et la
  réputation, une fois abîmée, ne se répare pas à coups de budget API.
- La valeur d'une PR Mathlib est **non linéaire** : 3 PRs soignées et utiles valent
  infiniment mieux que 50 PRs correctes mais triviales.

**La bonne asymétrie : automatiser la découverte, artisanaliser la livraison.**

Ce qui scale (et qu'on devrait outiller) :
- **Détection de lemmes manquants** : chaque hallucination de nom de lemme dans la base
  est un candidat — le modèle « s'attendait » à ce que `foo_bar_baz` existe. Un script
  qui agrège les `unknown identifier` par fréquence sur toutes les campagnes produit une
  liste de trous plausibles dans Mathlib. C'est un sous-produit gratuit des campagnes.
- **Vérification de non-existence** : pour chaque candidat, interroger Loogle/LeanSearch
  pour confirmer qu'aucun équivalent n'existe sous un autre nom (99 % des cas : il existe).

Ce qui ne scale pas et doit rester manuel : le choix du lemme, le style Mathlib, le
naming, la docstring, la discussion de revue. Objectif réaliste : **3 à 5 PRs de qualité
sur six mois**, pas 50.

Le débouché où le volume est réellement un atout, ce sont les projets de formalisation
**conçus pour le volume** (le modèle Equational Theories : des milliers d'implications
indépendantes, contributions machine bienvenues par design). C'est là qu'il faut guetter
le prochain projet du même type — et ton harnais sera prêt.

---

## 5. Ordre d'implémentation conseillé

1. **Colonne `difficulty_class` + backfill** — sans risque, débloque tout le reste.
2. **`p_success` par classe** (une requête + une fonction) — le modèle de tarification.
3. **Abandon précoce** (goal state figé / erreur répétée) — le gros gain de coût.
4. **`Target` + `config_for()`** — la politique pilotée par la valeur.
5. **`targets/registry.yaml` + `rank_targets.py`** — l'outil de décision.
6. **Agrégateur d'`unknown identifier`** — le détecteur de trous Mathlib.

Les points 1 à 3 se font sur les données déjà en base et n'ont aucune dépendance externe.
