import Mathlib.Data.Nat.Digits.Div
import Mathlib.Tactic

/-- Formalized proof of `mathd_numbertheory_430` in Lean 4. -/

theorem mathd_numbertheory_430 (a b c : ℕ) (h₀ : 1 ≤ a ∧ a ≤ 9) (h₁ : 1 ≤ b ∧ b ≤ 9)
    (h₂ : 1 ≤ c ∧ c ≤ 9) (h₃ : a ≠ b) (h₄ : a ≠ c) (h₅ : b ≠ c) (h₆ : a + b = c)
    (h₇ : 10 * a + a - b = 2 * c) (h₈ : c * b = 10 * a + a + a) : a + b + c = 8 := by
  have ha1 : 1 ≤ a := h₀.1
  have ha9 : a ≤ 9 := h₀.2
  have hb1 : 1 ≤ b := h₁.1
  have hb9 : b ≤ 9 := h₁.2
  have hc1 : 1 ≤ c := h₂.1
  have hc9 : c ≤ 9 := h₂.2
  have hc_eq : c = a + b := h₆.symm
  subst c
  have h7' : 10 * a + a - b = 2 * (a + b) := h₇
  have h8' : (a + b) * b = 10 * a + a + a := h₈
  have h7'' : 11 * a - b = 2 * a + 2 * b := by
    calc
      11 * a - b = 10 * a + a - b := by ring
      _ = 2 * (a + b) := h7'
      _ = 2 * a + 2 * b := by ring
  have hb_le : b ≤ 11 * a := by omega
  have h7''' : 11 * a = 2 * a + 3 * b := by omega
  have h9a : 9 * a = 3 * b := by omega
  have h3a : 3 * a = b := by omega
  subst b
  have h8'' : (a + 3 * a) * (3 * a) = 10 * a + a + a := h8'
  have h8''' : 4 * a * (3 * a) = 12 * a := by
    calc
      4 * a * (3 * a) = 12 * a ^ 2 := by ring
      _ = 12 * a := by
        have : a ^ 2 = a := by
          have h : 12 * a ^ 2 = 12 * a := by
            calc
              12 * a ^ 2 = (a + 3 * a) * (3 * a) := by ring
              _ = 10 * a + a + a := h8''
              _ = 12 * a := by ring
          exact Nat.mul_left_cancel (by norm_num : 0 < 12) h
        rw [this]
  have ha_eq : a = 1 := by
    have h : 12 * a ^ 2 = 12 * a := by
      calc
        12 * a ^ 2 = (a + 3 * a) * (3 * a) := by ring
        _ = 10 * a + a + a := h8''
        _ = 12 * a := by ring
    have h' : a ^ 2 = a := Nat.mul_left_cancel (by norm_num : 0 < 12) h
    nlinarith [ha1]
  subst a
  norm_num
