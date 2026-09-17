import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity

/-- Formalized proof of `mathd_numbertheory_237` in Lean 4. -/
theorem mathd_numbertheory_237 : (∑ k ∈ Finset.range 101, k) % 6 = 4 := by
  norm_num [Finset.sum_range_id]
