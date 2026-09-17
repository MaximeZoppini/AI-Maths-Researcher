## Summary
This PR formalizes and contributes the theorem `aime_1983_p1` to Mathlib.

### Mathematical statement
`theorem aime_1983_p1 (x y z w : ℕ) (ht : 1 < x ∧ 1 < y ∧ 1 < z) (hw : 0 ≤ w)`

## AI Assistance Disclosure
- **Author**: Assistant AI (AI-Maths-Researcher) under human review.
- **Verification**: Certified sorry-free and verified against standard axioms ([propext, Classical.choice, Quot.sound]).
- **Human maintainer**: I have carefully reviewed, understood, and validated every line of this proof.

## Checklist
- [x] Code strictly adheres to Mathlib naming conventions.
- [x] Module docstrings and declaration comments (/-- ... -/) included.
- [x] No `set_option linter.* false` in source code.
- [x] Verified on Loogle / LeanSearch that no duplicate theorem exists.
