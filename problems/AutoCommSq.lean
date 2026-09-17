import Mathlib.Tactic
import Mathlib.Algebra.Ring.Parity

set_option linter.style.header false

theorem add_comm_sq (a b : ℤ) : (a + b) ^ 2 = (b + a) ^ 2 := by
  ring
