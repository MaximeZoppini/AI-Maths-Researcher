import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Tactic

/-- Formalized proof of `aime_1983_p1` in Lean 4. -/

theorem aime_1983_p1 (x y z w : ℕ) (ht : 1 < x ∧ 1 < y ∧ 1 < z) (hw : 0 ≤ w)
    (h0 : Real.log w / Real.log x = 24) (h1 : Real.log w / Real.log y = 40)
    (h2 : Real.log w / Real.log (x * y * z) = 12) : Real.log w / Real.log z = 60 := by
  have hx1 : 1 < x := ht.1
  have hy1 : 1 < y := ht.2.1
  have hz1 : 1 < z := ht.2.2
  have hx0 : (0 : ℝ) < x := by exact_mod_cast (lt_trans Nat.zero_lt_one hx1)
  have hy0 : (0 : ℝ) < y := by exact_mod_cast (lt_trans Nat.zero_lt_one hy1)
  have hz0 : (0 : ℝ) < z := by exact_mod_cast (lt_trans Nat.zero_lt_one hz1)
  have hxlog : Real.log (x : ℝ) ≠ 0 :=
    ne_of_gt (Real.log_pos (by exact_mod_cast hx1))
  have hylog : Real.log (y : ℝ) ≠ 0 :=
    ne_of_gt (Real.log_pos (by exact_mod_cast hy1))
  have hzlog : Real.log (z : ℝ) ≠ 0 :=
    ne_of_gt (Real.log_pos (by exact_mod_cast hz1))
  have hxy : Real.log ((x : ℝ) * y * z) = Real.log x + Real.log y + Real.log z := by
    rw [Real.log_mul (mul_ne_zero (ne_of_gt hx0) (ne_of_gt hy0)) (ne_of_gt hz0),
        Real.log_mul (ne_of_gt hx0) (ne_of_gt hy0)]
  have h2' : Real.log w / (Real.log x + Real.log y + Real.log z) = 12 := by
    rwa [hxy] at h2
  have h0' : Real.log w = 24 * Real.log x := by
    field_simp [hxlog] at h0
    linarith
  have h1' : Real.log w = 40 * Real.log y := by
    field_simp [hylog] at h1
    linarith
  have hsum_ne : Real.log x + Real.log y + Real.log z ≠ 0 := by
    have hxpos : 0 < Real.log x := Real.log_pos (by exact_mod_cast hx1)
    have hypos : 0 < Real.log y := Real.log_pos (by exact_mod_cast hy1)
    have hzpos : 0 < Real.log z := Real.log_pos (by exact_mod_cast hz1)
    positivity
  have h2'' : Real.log w = 12 * (Real.log x + Real.log y + Real.log z) := by
    field_simp [hsum_ne] at h2'
    linarith
  have hx_eq : 24 * Real.log x = 40 * Real.log y := by linarith
  have hx_eq' : Real.log x = (5 / 3) * Real.log y := by linarith
  have hz_eq : 24 * Real.log x = 12 * (Real.log x + Real.log y + Real.log z) := by linarith
  have hz_eq' : Real.log z = Real.log x - Real.log y := by linarith
  have hz_eq'' : Real.log z = (2 / 3) * Real.log y := by linarith
  have hw_eq : Real.log w = 40 * Real.log y := h1'
  have hfinal : Real.log w / Real.log z = 60 := by
    rw [hw_eq, hz_eq'']
    field_simp [hylog]
    ring
  exact hfinal
