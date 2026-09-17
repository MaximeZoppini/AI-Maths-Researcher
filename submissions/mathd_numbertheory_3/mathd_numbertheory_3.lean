import Mathlib.Data.Nat.ModEq
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Tactic.NormNum

/-- Formalized proof of `mathd_numbertheory_3` in Lean 4. -/

theorem mathd_numbertheory_3 : (∑ x ∈ Finset.range 10, (x + 1) ^ 2) % 10 = 5 := by
  norm_num [Finset.sum_range_succ]
