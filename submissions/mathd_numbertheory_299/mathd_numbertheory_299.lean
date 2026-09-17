import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity

/-- Formalized proof of `mathd_numbertheory_299` in Lean 4. -/
theorem mathd_numbertheory_299 : 1 * 3 * 5 * 7 * 9 * 11 * 13 % 10 = 5 := by
  norm_num
