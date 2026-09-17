import Mathlib.Tactic

set_option linter.style.header false

/-- Problem 2: No square of an integer is of the form 3k + 2. -/
theorem sq_ne_three_mul_add_two (a k : ℤ) : a ^ 2 ≠ 3 * k + 2 := by
  intro h
  set q := a / 3
  have hmod : a % 3 = 0 ∨ a % 3 = 1 ∨ a % 3 = 2 := by omega
  have hdiv : a = 3 * q + (a % 3) := by omega
  rcases hmod with h0 | h1 | h2
  · rw [h0] at hdiv
    have hsq : a ^ 2 = 3 * (3 * q ^ 2) := by
      calc a ^ 2 = (3 * q + 0) ^ 2 := by rw [hdiv]
      _ = 3 * (3 * q ^ 2) := by ring
    rw [hsq] at h
    omega
  · rw [h1] at hdiv
    have hsq : a ^ 2 = 3 * (3 * q ^ 2 + 2 * q) + 1 := by
      calc a ^ 2 = (3 * q + 1) ^ 2 := by rw [hdiv]
      _ = 3 * (3 * q ^ 2 + 2 * q) + 1 := by ring
    rw [hsq] at h
    omega
  · rw [h2] at hdiv
    have hsq : a ^ 2 = 3 * (3 * q ^ 2 + 4 * q + 1) + 1 := by
      calc a ^ 2 = (3 * q + 2) ^ 2 := by rw [hdiv]
      _ = 3 * (3 * q ^ 2 + 4 * q + 1) + 1 := by ring
    rw [hsq] at h
    omega
