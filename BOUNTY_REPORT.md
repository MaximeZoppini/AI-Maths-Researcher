# 🏆 AI-Maths-Researcher — Rapport Officiel de Certification & Bounties

> **Généré le** : `2026-09-17 13:07:16 UTC`  
> **Infra de Vérification** : LXC Container 200 (Proxmox 100.90.108.89)  
> **Lean 4 / Mathlib** : `v4.34.0` | **Axiomes Admis** : `[propext, Classical.choice, Quot.sound]` (Strict Zero-Sorry)

---

## 1. Synthèse Exécutive

| Métrique | Valeur |
| :--- | :--- |
| **Problèmes Uniques Résolus** | **13 / 25** (52.0%) |
| **Sous-Lemmes Décomposés & Résolus** | **2 / 10** |
| **Nombre Total de Tentatives** | **121** |
| **Temps Moyen par Tentative (REPL)** | **807.5 ms** |
| **Coût Total Consommé (API LLM)** | **$0.0423** |

---

## 2. Répartition par Modèle

| Modèle | Essais | Succès | Taux | Latence Moy. | Coût Total |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `deepseek-chat` | 114 | 20 | 17.5% | 853.4 ms | $0.0423 |
| `gemini-2.5-flash` | 7 | 2 | 28.6% | 60.5 ms | $0.0000 |

---

## 3. Registre des Preuves Formelles Certifiées ('Axiom-Clean')

### 🎯 Théorème : `AutoNatCancel`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `gemini-2.5-flash` | **Itération** : 2 | **Latence REPL** : 45.1 ms | **Coût** : $0.00000
- **Timestamp** : `2026-09-17T11:49:08.874625+00:00`

```lean
import Mathlib.Tactic
import Mathlib.Algebra.Ring.Parity

set_option linter.style.header false

theorem nat_add_sub_cancel (n m : ℕ) : (n + m) - m = n := by
  omega
```

### 🎯 Théorème : `aime_1983_p1`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 2 | **Latence REPL** : 2099.2 ms | **Coût** : $0.00056
- **Timestamp** : `2026-09-17T12:50:27.605746+00:00`

```lean
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Tactic

theorem aime_1983_p1 (x y z w : ℕ) (ht : 1 < x ∧ 1 < y ∧ 1 < z) (hw : 0 ≤ w)
    (h0 : Real.log w / Real.log x = 24) (h1 : Real.log w / Real.log y = 40)
    (h2 : Real.log w / Real.log (x * y * z) = 12) : Real.log w / Real.log z = 60 := by
  have hx1 : 1 < x := ht.1
  have hy1 : 1 < y := ht.2.1
  have hz1 : 1 < z := ht.2.2
  have hx0 : (0 : ℝ) < x := by exact_mod_cast (lt_trans Nat.zero_lt_one hx1)
  have hy0 : (0 : ℝ) < y := by exact_mod_cast (lt_trans Nat.zero_lt_one hy1)
  have hz0 : (0 : ℝ) < z := by exact_mod_cast (lt_trans Nat.zero_lt_one hz1)
  have hxlog : Real.log (x : ℝ) ≠ 0 :=
    ne_of_gt (Real.log_pos (by exact_mod_cast hx1))
  have hylog : Real.log (y : ℝ) ≠ 0 :=
    ne_of_gt (Real.log_pos (by exact_mod_cast hy1))
  have hzlog : Real.log (z : ℝ) ≠ 0 :=
    ne_of_gt (Real.log_pos (by exact_mod_cast hz1))
  have hxy : Real.log ((x : ℝ) * y * z) = Real.log x + Real.log y + Real.log z := by
    rw [Real.log_mul (mul_ne_zero (ne_of_gt hx0) (ne_of_gt hy0)) (ne_of_gt hz0),
        Real.log_mul (ne_of_gt hx0) (ne_of_gt hy0)]
  have h2' : Real.log w / (Real.log x + Real.log y + Real.log z) = 12 := by
    rwa [hxy] at h2
  have h0' : Real.log w = 24 * Real.log x := by
    field_simp [hxlog] at h0
    linarith
  have h1' : Real.log w = 40 * Real.log y := by
    field_simp [hylog] at h1
    linarith
  have hsum_ne : Real.log x + Real.log y + Real.log z ≠ 0 := by
    have hxpos : 0 < Real.log x := Real.log_pos (by exact_mod_cast hx1)
    have hypos : 0 < Real.log y := Real.log_pos (by exact_mod_cast hy1)
    have hzpos : 0 < Real.log z := Real.log_pos (by exact_mod_cast hz1)
    positivity
  have h2'' : Real.log w = 12 * (Real.log x + Real.log y + Real.log z) := by
    field_simp [hsum_ne] at h2'
    linarith
  have hx_eq : 24 * Real.log x = 40 * Real.log y := by linarith
  have hx_eq' : Real.log x = (5 / 3) * Real.log y := by linarith
  have hz_eq : 24 * Real.log x = 12 * (Real.log x + Real.log y + Real.log z) := by linarith
  have hz_eq' : Real.log z = Real.log x - Real.log y := by linarith
  have hz_eq'' : Real.log z = (2 / 3) * Real.log y := by linarith
  have hw_eq : Real.log w = 40 * Real.log y := h1'
  have hfinal : Real.log w / Real.log z = 60 := by
    rw [hw_eq, hz_eq'']
    field_simp [hylog]
    ring
  exact hfinal
```

### 🎯 Théorème : `amc12b_2020_p2`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 69.5 ms | **Coût** : $0.00006
- **Timestamp** : `2026-09-17T12:55:20.482965+00:00`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
theorem amc12b_2020_p2 :
    (100 ^ 2 - 7 ^ 2 : ℝ) / (70 ^ 2 - 11 ^ 2) * ((70 - 11) * (70 + 11) / ((100 - 7) * (100 + 7))) =
      1 := by
  norm_num
```

### 🎯 Théorème : `mathd_algebra_141`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 333.7 ms | **Coût** : $0.00007
- **Timestamp** : `2026-09-17T12:51:26.548918+00:00`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
theorem mathd_algebra_141 (a b : ℝ) (h₁ : a * b = 180) (h₂ : 2 * (a + b) = 54) :
    a ^ 2 + b ^ 2 = 369 := by
  have hsum : a + b = 27 := by linarith
  have hsq : (a + b) ^ 2 = a ^ 2 + 2 * a * b + b ^ 2 := by ring
  rw [hsum] at hsq
  nlinarith
```

### 🎯 Théorème : `mathd_algebra_209`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 3 | **Latence REPL** : 42.3 ms | **Coût** : $0.00021
- **Timestamp** : `2026-09-17T12:52:42.809695+00:00`

```lean
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
```

### 🎯 Théorème : `mathd_algebra_33`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 353.0 ms | **Coût** : $0.00010
- **Timestamp** : `2026-09-17T12:54:19.482033+00:00`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
theorem mathd_algebra_33 (x y z : ℝ) (h₀ : x ≠ 0) (h₁ : 2 * x = 5 * y) (h₂ : 7 * y = 10 * z) :
    z / x = 7 / 25 := by
  have hx : x ≠ 0 := h₀
  have hy : y ≠ 0 := by
    intro hy
    rw [hy, mul_zero] at h₁
    have : x = 0 := by linarith
    exact hx this
  have hz : z ≠ 0 := by
    intro hz
    rw [hz, mul_zero] at h₂
    have : y = 0 := by linarith
    exact hy this
  have hxy : y = (2/5) * x := by linarith
  have hyz : z = (7/10) * y := by linarith
  rw [hyz, hxy]
  field_simp
  ring
```

### 🎯 Théorème : `mathd_algebra_419`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 39.6 ms | **Coût** : $0.00006
- **Timestamp** : `2026-09-17T12:56:55.382997+00:00`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
theorem mathd_algebra_419 (a b : ℝ) (h₀ : a = -1) (h₁ : b = 5) : -a - b ^ 2 + 3 * (a * b) = -39 := by
  subst h₀
  subst h₁
  norm_num
```

### 🎯 Théorème : `mathd_algebra_478`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `gemini-2.5-flash` | **Itération** : 1 | **Latence REPL** : 59.9 ms | **Coût** : $0.00000
- **Timestamp** : `2026-09-17T11:51:20.614446+00:00`

```lean
import Mathlib.Tactic
import Mathlib.Algebra.Ring.Parity

set_option linter.style.header false

theorem mathd_algebra_478 (b h v : ℝ) (h₀ : 0 < b ∧ 0 < h ∧ 0 < v) (h₁ : v = 1 / 3 * (b * h))
    (h₂ : b = 30) (h₃ : h = 13 / 2) : v = 65 := by
  subst_vars
  norm_num at *
```

### 🎯 Théorème : `mathd_numbertheory_1124_mathd_numbertheory_1124_step1`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 159.7 ms | **Coût** : $0.00010
- **Timestamp** : `2026-09-17T12:53:08.812634+00:00`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
import Mathlib.Data.Nat.Factorial.Basic

open scoped Nat
open scoped Real

set_option linter.style.header false

lemma mathd_numbertheory_1124_step1 (n : ℕ) (h : 18 ∣ 374 * 10 + n) :
    18 ∣ 14 + n := by
  have h' : 18 ∣ 3740 + n := by
    simpa using h
  have hmod : (3740 + n) % 18 = 0 := Nat.mod_eq_zero_of_dvd h'
  have h3740 : 3740 % 18 = 14 := by norm_num
  have : (14 + n) % 18 = 0 := by
    omega
  exact Nat.dvd_of_mod_eq_zero this
```

### 🎯 Théorème : `mathd_numbertheory_1124_mathd_numbertheory_1124_step2`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 400.8 ms | **Coût** : $0.00022
- **Timestamp** : `2026-09-17T12:53:18.699852+00:00`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
import Mathlib.Data.Nat.Factorial.Basic

open scoped Nat
open scoped Real

set_option linter.style.header false

open scoped Nat
open scoped Real


lemma mathd_numbertheory_1124_step1 (n : ℕ) (h : 18 ∣ 374 * 10 + n) :
    18 ∣ 14 + n := by
  have h' : 18 ∣ 3740 + n := by
    simpa using h
  have hmod : (3740 + n) % 18 = 0 := Nat.mod_eq_zero_of_dvd h'
  have h3740 : 3740 % 18 = 14 := by norm_num
  have : (14 + n) % 18 = 0 := by
    omega
  exact Nat.dvd_of_mod_eq_zero this

lemma mathd_numbertheory_1124_step2 (n : ℕ) (h₀ : n ≤ 9) (h : 18 ∣ 14 + n) :
    n = 4 := by
  have hle : 14 + n ≤ 23 := by omega
  have hge : 14 ≤ 14 + n := by omega
  rcases h with ⟨k, hk⟩
  have hkpos : k ≥ 1 := by
    by_contra hk0
    interval_cases k <;> omega
  have hklt : k ≤ 1 := by
    nlinarith
  have hk1 : k = 1 := by omega
  omega
```

### 🎯 Théorème : `mathd_numbertheory_237`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 1191.0 ms | **Coût** : $0.00011
- **Timestamp** : `2026-09-17T12:54:09.486196+00:00`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
theorem mathd_numbertheory_237 : (∑ k ∈ Finset.range 101, k) % 6 = 4 := by
  norm_num [Finset.sum_range_id]
```

### 🎯 Théorème : `mathd_numbertheory_299`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 47.1 ms | **Coût** : $0.00009
- **Timestamp** : `2026-09-17T12:55:11.256340+00:00`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
theorem mathd_numbertheory_299 : 1 * 3 * 5 * 7 * 9 * 11 * 13 % 10 = 5 := by
  norm_num
```

### 🎯 Théorème : `mathd_numbertheory_3`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 60.8 ms | **Coût** : $0.00012
- **Timestamp** : `2026-09-17T12:51:36.060966+00:00`

```lean
import Mathlib.Data.Nat.ModEq
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Tactic.NormNum

theorem mathd_numbertheory_3 : (∑ x ∈ Finset.range 10, (x + 1) ^ 2) % 10 = 5 := by
  norm_num [Finset.sum_range_succ]
```

### 🎯 Théorème : `mean_calc`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 250.3 ms | **Coût** : $0.00009
- **Timestamp** : `2026-09-17T12:46:29.257791+00:00`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
import Mathlib.Data.Nat.Factorial.Basic

open scoped Nat
open scoped Real

set_option linter.style.header false

open scoped Nat
open scoped Real


lemma solve_y_from_mean_aux (x y : ℝ) (h₁ : (x + y) / 2 = 10) (h₂ : x = 4) : y = 16 := by
  rw [h₂] at h₁
  linarith

theorem solve_y_from_mean (x y : ℝ) (h₁ : (x + y) / 2 = 10) (h₂ : x = 4) : y = 16 := by
  rw [h₂] at h₁
  linarith
```

### 🎯 Théorème : `mean_calc_solve_y_from_mean_aux`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 116.6 ms | **Coût** : $0.00008
- **Timestamp** : `2026-09-17T12:46:23.990819+00:00`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
import Mathlib.Data.Nat.Factorial.Basic

open scoped Nat
open scoped Real

set_option linter.style.header false

lemma solve_y_from_mean_aux (x y : ℝ) (h₁ : (x + y) / 2 = 10) (h₂ : x = 4) : y = 16 := by
  rw [h₂] at h₁
  linarith
```
