import Mathlib.Tactic
import Mathlib.Algebra.Ring.Parity

/-- Formalized proof of `AutoCommSq` in Lean 4. -/


theorem add_comm_sq (a b : ℤ) : (a + b) ^ 2 = (b + a) ^ 2 := by
  ring
