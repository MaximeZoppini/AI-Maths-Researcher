import Mathlib.Tactic
import Mathlib.Algebra.Ring.Parity

set_option linter.style.header false

theorem nat_add_sub_cancel (n m : ℕ) : (n + m) - m = n := by
  omega
