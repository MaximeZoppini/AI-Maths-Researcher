import Mathlib.Tactic

theorem mathd_algebra_398 (a b c : ℝ) (h₀ : 0 < a ∧ 0 < b ∧ 0 < c) (h₁ : 9 * b = 20 * c)
    (h₂ : 7 * a = 4 * b) : 63 * a = 80 * c := by
  have hb : b = (20 * c) / 9 := by linarith
  have ha : a = (4 * b) / 7 := by linarith
  rw [ha, hb]
  ring
