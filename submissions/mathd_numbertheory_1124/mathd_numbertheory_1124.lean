import Mathlib.Tactic

/-- Formalized proof of `mathd_numbertheory_1124` in Lean 4. -/

theorem mathd_numbertheory_1124 (n : ℕ) (h₀ : n ≤ 9) (h₁ : 18 ∣ 374 * 10 + n) : n = 4 := by
  rcases h₁ with ⟨k, hk⟩
  norm_num at hk
  omega
