import Mathlib.Tactic

set_option linter.style.header false

/-- Problem 3a: Two-variable AM-GM algebraic inequality: 2ab ≤ a² + b² -/
theorem am_gm_two_real (a b : ℝ) : 2 * a * b ≤ a ^ 2 + b ^ 2 := by
  have h : 0 ≤ (a - b) ^ 2 := sq_nonneg (a - b)
  have h_exp : (a - b) ^ 2 = a ^ 2 - 2 * a * b + b ^ 2 := by ring
  linarith

/-- Problem 3b: 2D Cauchy-Schwarz Inequality: (a₁b₁ + a₂b₂)² ≤ (a₁² + a₂²)(b₁² + b₂²) -/
theorem cauchy_schwarz_2d (a₁ a₂ b₁ b₂ : ℝ) :
    (a₁ * b₁ + a₂ * b₂) ^ 2 ≤ (a₁ ^ 2 + a₂ ^ 2) * (b₁ ^ 2 + b₂ ^ 2) := by
  have h : 0 ≤ (a₁ * b₂ - a₂ * b₁) ^ 2 := sq_nonneg (a₁ * b₂ - a₂ * b₁)
  have h_id : (a₁ ^ 2 + a₂ ^ 2) * (b₁ ^ 2 + b₂ ^ 2) - (a₁ * b₁ + a₂ * b₂) ^ 2 = (a₁ * b₂ - a₂ * b₁) ^ 2 := by ring
  linarith
