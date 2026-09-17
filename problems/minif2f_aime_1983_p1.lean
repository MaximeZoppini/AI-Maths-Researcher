import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Tactic

theorem aime_1983_p1 (x y z w : ℕ) (ht : 1 < x ∧ 1 < y ∧ 1 < z) (hw : 0 ≤ w)
    (h0 : Real.log w / Real.log x = 24) (h1 : Real.log w / Real.log y = 40)
    (h2 : Real.log w / Real.log (x * y * z) = 12) : Real.log w / Real.log z = 60 := by
  have hx1 : 1 < x := ht.1
  have hy1 : 1 < y := ht.2.1
  have hz1 : 1 < z := ht.2.2
  have hx0 : (0 : ℝ) < x := by exact_mod_cast (lt_trans zero_lt_one hx1)
  have hy0 : (0 : ℝ) < y := by exact_mod_cast (lt_trans zero_lt_one hy1)
  have hz0 : (0 : ℝ) < z := by exact_mod_cast (lt_trans zero_lt_one hz1)
  have hlx : Real.log x ≠ 0 := ne_of_gt (Real.log_pos (by exact_mod_cast hx1))
  have hly : Real.log y ≠ 0 := ne_of_gt (Real.log_pos (by exact_mod_cast hy1))
  have hlz : Real.log z ≠ 0 := ne_of_gt (Real.log_pos (by exact_mod_cast hz1))
  have hxylog : Real.log ((x : ℝ) * y * z) = Real.log x + Real.log y + Real.log z := by
    rw [Real.log_mul (mul_ne_zero (ne_of_gt hx0) (ne_of_gt hy0)) (ne_of_gt hz0)]
    rw [Real.log_mul (ne_of_gt hx0) (ne_of_gt hy0)]
  have h2' : Real.log w / (Real.log x + Real.log y + Real.log z) = 12 := by
    rw [← hxylog]
    exact h2
  have hsum_ne : Real.log x + Real.log y + Real.log z ≠ 0 := by
    intro h
    rw [h] at h2'
    norm_num at h2'
  have e0 : Real.log w = 24 * Real.log x := by
    field_simp [hlx] at h0
    linarith
  have e1 : Real.log w = 40 * Real.log y := by
    field_simp [hly] at h1
    linarith
  have e2 : Real.log w = 12 * (Real.log x + Real.log y + Real.log z) := by
    field_simp [hsum_ne] at h2'
    linarith
  have hxy : 24 * Real.log x = 40 * Real.log y := by linarith
  have hly_eq : Real.log y = (24 / 40) * Real.log x := by
    field_simp at hxy
    linarith
  have hz_eq : Real.log z = (Real.log w - 12 * Real.log x - 12 * Real.log y) / 12 := by
    linarith
  rw [e0] at hz_eq
  rw [hly_eq] at hz_eq
  have hz_val : Real.log z = (24 * Real.log x - 12 * Real.log x - 12 * ((24 / 40) * Real.log x)) / 12 := by
    linarith
  have hz_simpl : Real.log z = (12 * Real.log x - 12 * (24 / 40) * Real.log x) / 12 := by
    linarith
  have hz_final : Real.log z = (12 - 12 * (24 / 40)) / 12 * Real.log x := by
    rw [hz_simpl]
    ring
  have hcoef : (12 - 12 * (24 / 40)) / 12 = (2 / 5 : ℝ) := by norm_num
  rw [hcoef] at hz_final
  have hz_eq2 : Real.log z = (2 / 5) * Real.log x := hz_final
  rw [e0, hz_eq2]
  field_simp [hlx]
  norm_num
