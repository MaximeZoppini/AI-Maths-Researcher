import Mathlib.Tactic
import Mathlib.Data.Real.Basic

theorem mathd_algebra_209 (σ : ℝ ≃ ℝ) (h₀ : σ.symm 2 = 10) (h₁ : σ.symm 10 = 1)
    (h₂ : σ.symm 1 = 2) : σ (σ 10) = 1 := by
  have h3 : σ 10 = 2 := by
    have := σ.symm_apply_eq.mp h₀
    exact this.symm
  have h4 : σ 2 = 1 := by
    have := σ.symm_apply_eq.mp h₂
    exact this.symm
  rw [h3, h4]
