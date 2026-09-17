import Mathlib.Data.Rat.Lemmas
import Mathlib.Tactic

theorem mathd_algebra_459 (a b c d : ℚ) (h₀ : 3 * a = b + c + d) (h₁ : 4 * b = a + c + d)
    (h₂ : 2 * c = a + b + d) (h₃ : 8 * a + 10 * b + 6 * c = 24) : ↑d.den + d.num = 28 := by
  have ha : a = 1 := by linarith
  have hb : b = 4 / 5 := by linarith
  have hc : c = 4 / 3 := by linarith
  have hd : d = 13 / 15 := by linarith
  rw [hd]
  norm_num
