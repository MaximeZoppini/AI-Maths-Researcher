import Mathlib.Tactic.NormNum

set_option linter.style.header false

/-- Test theorem demonstrating Mathlib tactic verification -/
theorem two_plus_two : 2 + 2 = 4 := by
  norm_num
