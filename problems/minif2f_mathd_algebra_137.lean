import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
theorem mathd_algebra_137 (x : ℕ) (h₀ : ↑x + (4 : ℝ) / (100 : ℝ) * ↑x = 598) : x = 575 := by
  have h₁ : (↑x : ℝ) * (1 + 4 / 100) = 598 := by
    linarith
  have h₂ : (↑x : ℝ) * (104 / 100) = 598 := by
    norm_num at h₁ ⊢
    linarith
  have h₃ : (↑x : ℝ) = 575 := by
    have h : (104 / 100 : ℝ) ≠ 0 := by norm_num
    field_simp at h₂
    linarith
  exact_mod_cast h₃
