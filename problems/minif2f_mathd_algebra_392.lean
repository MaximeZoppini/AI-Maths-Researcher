import Mathlib.Algebra.Group.Int.Even
import Mathlib.Tactic

theorem mathd_algebra_392 (n : ℕ) (h₀ : Even n)
    (h₁ : (↑n - 2) ^ 2 + ↑n ^ 2 + (↑n + 2) ^ 2 = (12296 : ℤ)) :
    (↑n - 2) * ↑n * (↑n + 2) / 8 = (32736 : ℤ) := by
  have h2 : (n : ℤ) ^ 2 = 4096 := by
    have : (↑n - 2 : ℤ) ^ 2 + ↑n ^ 2 + (↑n + 2) ^ 2 = 3 * ↑n ^ 2 + 8 := by ring
    rw [this] at h₁
    linarith
  have hn : (n : ℤ) = 64 := by
    have hpos : (0 : ℤ) ≤ (n : ℤ) := by exact_mod_cast Nat.zero_le n
    nlinarith [sq_nonneg ((n : ℤ) - 64), sq_nonneg ((n : ℤ) + 64)]
  have hn' : n = 64 := by exact_mod_cast hn
  subst hn'
  norm_num
