import Mathlib.Tactic
import Mathlib.Algebra.Ring.Parity

/-- Formalized proof of `AutoNatCancel` in Lean 4. -/


theorem nat_add_sub_cancel (n m : ℕ) : (n + m) - m = n := by
  omega
