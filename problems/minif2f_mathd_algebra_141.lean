import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
theorem mathd_algebra_141 (a b : ℝ) (h₁ : a * b = 180) (h₂ : 2 * (a + b) = 54) :
    a ^ 2 + b ^ 2 = 369 := by
  have hsum : a + b = 27 := by linarith
  have hsq : (a + b) ^ 2 = a ^ 2 + 2 * a * b + b ^ 2 := by ring
  rw [hsum] at hsq
  nlinarith
