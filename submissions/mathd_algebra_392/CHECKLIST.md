# Checklist de relecture humaine obligatoire avant toute soumission PR
- [ ] 1. Vérification Loogle : confirmer qu'aucun lemme équivalent n'existe déjà dans Mathlib.
- [ ] 2. Conventions de nommage : le nom est-il en snake_case descriptif des objets mathématiques ?
- [ ] 3. Docstring : la docstring `/-- ... -/` décrit-elle clairement l'énoncé en anglais mathématique ?
- [ ] 4. Linter & Style : aucun override de linter (`set_option linter.* false`), lignes de moins de 100 colonnes.
- [ ] 5. Compréhension humaine : le contributeur humain comprend-il et peut-il défendre chaque étape de la preuve en revue Zulip ?
- [ ] 6. Licence : la contribution est-elle conforme à la licence Apache 2.0 ?
