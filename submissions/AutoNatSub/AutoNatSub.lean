import Mathlib.Tactic
import Mathlib.Algebra.Ring.Parity

/-- Formalized proof of `AutoNatSub` in Lean 4. -/


theorem add_sub_assoc_nat (n m : ℕ) : (n + m) - m = n := by
  omega
