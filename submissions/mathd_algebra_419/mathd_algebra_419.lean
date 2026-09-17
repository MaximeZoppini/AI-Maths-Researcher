import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity

/-- Formalized proof of `mathd_algebra_419` in Lean 4. -/
theorem mathd_algebra_419 (a b : ℝ) (h₀ : a = -1) (h₁ : b = 5) : -a - b ^ 2 + 3 * (a * b) = -39 := by
  subst h₀
  subst h₁
  norm_num
