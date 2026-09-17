import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
theorem mathd_algebra_33 (x y z : ℝ) (h₀ : x ≠ 0) (h₁ : 2 * x = 5 * y) (h₂ : 7 * y = 10 * z) :
    z / x = 7 / 25 := by
  have hx : x ≠ 0 := h₀
  have hy : y ≠ 0 := by
    intro hy
    rw [hy, mul_zero] at h₁
    have : x = 0 := by linarith
    exact hx this
  have hz : z ≠ 0 := by
    intro hz
    rw [hz, mul_zero] at h₂
    have : y = 0 := by linarith
    exact hy this
  have hxy : y = (2/5) * x := by linarith
  have hyz : z = (7/10) * y := by linarith
  rw [hyz, hxy]
  field_simp
  ring
