import Mathlib.Tactic
import Mathlib.Algebra.Ring.Parity

set_option linter.style.header false

theorem mathd_algebra_478 (b h v : ℝ) (h₀ : 0 < b ∧ 0 < h ∧ 0 < v) (h₁ : v = 1 / 3 * (b * h))
    (h₂ : b = 30) (h₃ : h = 13 / 2) : v = 65 := by
  subst_vars
  norm_num at *
