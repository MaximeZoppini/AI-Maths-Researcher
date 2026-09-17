import Mathlib.Algebra.Ring.Parity
import Mathlib.Tactic.Ring
import Mathlib.Tactic.Contrapose

set_option linter.style.header false

/-- Problem 1: If n^2 is even, then n is even (for integers). -/
theorem even_of_even_sq {n : ℤ} (h : Even (n ^ 2)) : Even n := by
  contrapose! h
  rcases Int.not_even_iff_odd.mp h with ⟨k, rfl⟩
  rw [Int.not_even_iff_odd]
  use 2 * k ^ 2 + 2 * k
  ring
