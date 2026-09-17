import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity

/-- Formalized proof of `algebra_sqineq_unitcircatbpabsamblt1` in Lean 4. -/
theorem algebra_sqineq_unitcircatbpabsamblt1 (a b : ℝ) (h₀ : a ^ 2 + b ^ 2 = 1) :
    a * b + ‖a - b‖ ≤ 1 := by
  have ha2 : a ^ 2 ≤ 1 := by nlinarith [sq_nonneg b]
  have hb2 : b ^ 2 ≤ 1 := by nlinarith [sq_nonneg a]
  have ha_le : a ≤ 1 := by nlinarith [sq_nonneg (a - 1), ha2]
  have ha_ge : -1 ≤ a := by nlinarith [sq_nonneg (a + 1), ha2]
  have hb_le : b ≤ 1 := by nlinarith [sq_nonneg (b - 1), hb2]
  have hb_ge : -1 ≤ b := by nlinarith [sq_nonneg (b + 1), hb2]
  have h1 : a - b ≤ 1 - a * b := by
    have hA : 0 ≤ 1 - a := by linarith
    have hB : 0 ≤ 1 + b := by linarith
    have hprod : 0 ≤ (1 - a) * (1 + b) := mul_nonneg hA hB
    nlinarith [hprod]
  have h2 : -(1 - a * b) ≤ a - b := by
    have hC : 0 ≤ 1 - b := by linarith
    have hD : 0 ≤ 1 + a := by linarith
    have hprod : 0 ≤ (1 - b) * (1 + a) := mul_nonneg hC hD
    nlinarith [hprod]
  have habs : |a - b| ≤ 1 - a * b := abs_le.mpr ⟨h2, h1⟩
  have h_norm : ‖a - b‖ ≤ 1 - a * b := by
    rw [Real.norm_eq_abs]
    exact habs
  linarith
