import Mathlib.Tactic
import Mathlib.Algebra.Ring.Parity

set_option linter.style.header false

theorem add_sub_assoc_nat (n m : ℕ) : (n + m) - m = n := by
  omega
