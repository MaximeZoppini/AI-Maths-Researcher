## Summary
This PR formalizes and contributes the theorem `AutoCommSq` to Mathlib.

### Mathematical statement
`theorem add_comm_sq (a b : ℤ) : (a + b) ^ 2 = (b + a) ^ 2 := by`

## AI Assistance Disclosure
- **Author**: Assistant AI (AI-Maths-Researcher) under human review.
- **Verification**: Certified sorry-free and verified against standard axioms ([propext, Classical.choice, Quot.sound]).
- **Human maintainer**: I have carefully reviewed, understood, and validated every line of this proof.

## Checklist (to be verified by human maintainer)
- [ ] Code strictly adheres to Mathlib naming conventions.
- [ ] Module docstrings and declaration comments (/-- ... -/) included.
- [ ] No `set_option linter.* false` in source code.
- [ ] Verified on Loogle / LeanSearch that no duplicate theorem exists.
- [ ] Architectural fit: General mathematical theorem or placed in `Archive/` (raw competition exercises belong in archive or require generalization).
