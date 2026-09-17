import Mathlib.Algebra.Ring.Parity


/-- Problem 0: The sum of two even integers is even. -/
theorem even_add_even {a b : ℤ} (ha : Even a) (hb : Even b) : Even (a + b) := by
  exact Even.add ha hb
