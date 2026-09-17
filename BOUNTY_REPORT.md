# 🏆 AI-Maths-Researcher — Rapport Officiel de Certification & Bounties

> **Généré le** : `2026-09-17 12:49:20 UTC`  
> **Infra de Vérification** : LXC Container 200 (Proxmox 100.90.108.89)  
> **Lean 4 / Mathlib** : `v4.34.0` | **Axiomes Admis** : `[propext, Classical.choice, Quot.sound]` (Strict Zero-Sorry)

---

## 1. Synthèse Exécutive

| Métrique | Valeur |
| :--- | :--- |
| **Problèmes Résolus & Certifiés** | **6 / 11** (54.5%) |
| **Nombre Total de Tentatives** | **49** |
| **Temps Moyen par Tentative (REPL)** | **583.0 ms** |
| **Coût Total Consommé (API LLM)** | **$0.0143** |

---

## 2. Répartition par Modèle

| Modèle | Essais | Succès | Taux | Latence Moy. | Coût Total |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `deepseek-chat` | 42 | 8 | 19.0% | 670.1 ms | $0.0143 |
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

### 🎯 Théorème : `mathd_algebra_478`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 225.1 ms | **Coût** : $0.00017
- **Timestamp** : `2026-09-17T12:23:28.601148+00:00`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
theorem mathd_algebra_478 (b h v : ℝ) (h₀ : 0 < b ∧ 0 < h ∧ 0 < v) (h₁ : v = 1 / 3 * (b * h))
    (h₂ : b = 30) (h₃ : h = 13 / 2) : v = 65 := by
  rw [h₂, h₃] at h₁
  norm_num at h₁
  linarith
```

### 🎯 Théorème : `mathd_algebra_478`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 126.1 ms | **Coût** : $0.00017
- **Timestamp** : `2026-09-17T12:24:09.955745+00:00`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
theorem mathd_algebra_478 (b h v : ℝ) (h₀ : 0 < b ∧ 0 < h ∧ 0 < v) (h₁ : v = 1 / 3 * (b * h))
    (h₂ : b = 30) (h₃ : h = 13 / 2) : v = 65 := by
  rw [h₂, h₃] at h₁
  norm_num at h₁
  linarith
```

### 🎯 Théorème : `mathd_algebra_478`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 133.6 ms | **Coût** : $0.00017
- **Timestamp** : `2026-09-17T12:25:16.370632+00:00`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
theorem mathd_algebra_478 (b h v : ℝ) (h₀ : 0 < b ∧ 0 < h ∧ 0 < v) (h₁ : v = 1 / 3 * (b * h))
    (h₂ : b = 30) (h₃ : h = 13 / 2) : v = 65 := by
  rw [h₂, h₃] at h₁
  norm_num at h₁
  linarith
```

### 🎯 Théorème : `mathd_algebra_478`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 124.6 ms | **Coût** : $0.00017
- **Timestamp** : `2026-09-17T12:33:40.367288+00:00`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
theorem mathd_algebra_478 (b h v : ℝ) (h₀ : 0 < b ∧ 0 < h ∧ 0 < v) (h₁ : v = 1 / 3 * (b * h))
    (h₂ : b = 30) (h₃ : h = 13 / 2) : v = 65 := by
  rw [h₂, h₃] at h₁
  norm_num at h₁ ⊢
  linarith
```

### 🎯 Théorème : `aime_1983_p1`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 2 | **Latence REPL** : 2399.0 ms | **Coût** : $0.00060
- **Timestamp** : `2026-09-17T12:34:35.495186+00:00`

```lean
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Tactic

theorem aime_1983_p1 (x y z w : ℕ) (ht : 1 < x ∧ 1 < y ∧ 1 < z) (hw : 0 ≤ w)
    (h0 : Real.log w / Real.log x = 24) (h1 : Real.log w / Real.log y = 40)
    (h2 : Real.log w / Real.log (x * y * z) = 12) : Real.log w / Real.log z = 60 := by
  have hx1 : 1 < x := ht.1
  have hy1 : 1 < y := ht.2.1
  have hz1 : 1 < z := ht.2.2
  have hx0 : (0 : ℝ) < x := by exact_mod_cast (lt_trans zero_lt_one hx1)
  have hy0 : (0 : ℝ) < y := by exact_mod_cast (lt_trans zero_lt_one hy1)
  have hz0 : (0 : ℝ) < z := by exact_mod_cast (lt_trans zero_lt_one hz1)
  have hlx : Real.log x ≠ 0 := ne_of_gt (Real.log_pos (by exact_mod_cast hx1))
  have hly : Real.log y ≠ 0 := ne_of_gt (Real.log_pos (by exact_mod_cast hy1))
  have hlz : Real.log z ≠ 0 := ne_of_gt (Real.log_pos (by exact_mod_cast hz1))
  have hxylog : Real.log ((x : ℝ) * y * z) = Real.log x + Real.log y + Real.log z := by
    rw [Real.log_mul (mul_ne_zero (ne_of_gt hx0) (ne_of_gt hy0)) (ne_of_gt hz0)]
    rw [Real.log_mul (ne_of_gt hx0) (ne_of_gt hy0)]
  have h2' : Real.log w / (Real.log x + Real.log y + Real.log z) = 12 := by
    rw [← hxylog]
    exact h2
  have hsum_ne : Real.log x + Real.log y + Real.log z ≠ 0 := by
    intro h
    rw [h] at h2'
    norm_num at h2'
  have e0 : Real.log w = 24 * Real.log x := by
    field_simp [hlx] at h0
    linarith
  have e1 : Real.log w = 40 * Real.log y := by
    field_simp [hly] at h1
    linarith
  have e2 : Real.log w = 12 * (Real.log x + Real.log y + Real.log z) := by
    field_simp [hsum_ne] at h2'
    linarith
  have hxy : 24 * Real.log x = 40 * Real.log y := by linarith
  have hly_eq : Real.log y = (24 / 40) * Real.log x := by
    field_simp at hxy
    linarith
  have hz_eq : Real.log z = (Real.log w - 12 * Real.log x - 12 * Real.log y) / 12 := by
    linarith
  rw [e0] at hz_eq
  rw [hly_eq] at hz_eq
  have hz_val : Real.log z = (24 * Real.log x - 12 * Real.log x - 12 * ((24 / 40) * Real.log x)) / 12 := by
    linarith
  have hz_simpl : Real.log z = (12 * Real.log x - 12 * (24 / 40) * Real.log x) / 12 := by
    linarith
  have hz_final : Real.log z = (12 - 12 * (24 / 40)) / 12 * Real.log x := by
    rw [hz_simpl]
    ring
  have hcoef : (12 - 12 * (24 / 40)) / 12 = (2 / 5 : ℝ) := by norm_num
  rw [hcoef] at hz_final
  have hz_eq2 : Real.log z = (2 / 5) * Real.log x := hz_final
  rw [e0, hz_eq2]
  field_simp [hlx]
  norm_num
```

### 🎯 Théorème : `mathd_algebra_141`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 205.9 ms | **Coût** : $0.00008
- **Timestamp** : `2026-09-17T12:35:22.341238+00:00`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
theorem mathd_algebra_141 (a b : ℝ) (h₁ : a * b = 180) (h₂ : 2 * (a + b) = 54) :
    a ^ 2 + b ^ 2 = 369 := by
  have hsum : a + b = 27 := by linarith
  have hsq : (a + b) ^ 2 = a ^ 2 + 2 * (a * b) + b ^ 2 := by ring
  rw [hsum, h₁] at hsq
  norm_num at hsq
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
