import Mathlib.Tactic
import Mathlib.Data.ZMod.Basic

theorem numbertheory_x5neqy2p4 (x y : ℤ) : x ^ 5 ≠ y ^ 2 + 4 := by
  intro h
  have hmod : (x : ZMod 11)^5 = (y : ZMod 11)^2 + 4 := by
    have h' := congrArg (fun z : ℤ => (z : ZMod 11)) h
    push_cast at h'
    exact h'
  have hno : ∀ a b : ZMod 11, a^5 ≠ b^2 + 4 := by
    decide
  exact hno (x : ZMod 11) (y : ZMod 11) hmod
