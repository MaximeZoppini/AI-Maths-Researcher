# Checklist de relecture humaine obligatoire avant toute soumission PR
> [!IMPORTANT]
> **Politique d'admissibilité Mathlib** : Mathlib n'accepte PAS de problèmes d'olympiades/concours bruts dans son noyau (`Mathlib/*`). Les énoncés de type Olympiade doivent soit être généralisés en lemmes réutilisables dans la théorie correspondante, soit être dirigés vers le dossier `Archive/` dédié aux exercices récréatifs/concours.
- [ ] 1. Vérification Loogle : confirmer qu'aucun lemme équivalent n'existe déjà dans Mathlib.
- [ ] 2. Admissibilité : Lemme généralisé ou destiné à `Archive/` (pas d'exercice brut dans le core).
- [ ] 3. Conventions de nommage : le nom est-il en snake_case descriptif des objets mathématiques ?
- [ ] 4. Docstring : la docstring `/-- ... -/` décrit-elle clairement l'énoncé en anglais mathématique ?
- [ ] 5. Linter & Style : aucun override de linter (`set_option linter.* false`), lignes de moins de 100 colonnes.
- [ ] 6. Compréhension humaine : le contributeur humain comprend-il et peut-il défendre chaque étape de la preuve en revue Zulip ?
- [ ] 7. Licence : la contribution est-elle conforme à la licence Apache 2.0 ?

> [!WARNING]
> **Alerte Linter Colonnes** : 1 ligne(s) dépassent 100 colonnes (ex: Ligne 14 : 114 cols). Reformatez ces lignes avant soumission.
