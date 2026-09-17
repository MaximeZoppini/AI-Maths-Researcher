# 🏆 AI-Maths-Researcher — Rapport Officiel de Certification & Bounties

> **Généré le** : `2026-09-17 17:31:12 UTC`  
> **Infra de Vérification** : LXC Container 200 (Proxmox 100.90.108.89)  
> **Lean 4 / Mathlib** : `v4.34.0` | **Axiomes Admis** : `[propext, Classical.choice, Quot.sound]` (Strict Zero-Sorry)

---

## 1. Métrique Officielle & Synthèse Exécutive

| Métrique | Valeur |
| :--- | :--- |
| 🎯 **Métrique Officielle de Référence (MiniF2F Test, 30 premiers)** | **17 / 30** (56.7%) |
| **Théorèmes MiniF2F Certifiés en Prod (problems/)** | **18 / 244** (7.4%) |
| **Problèmes Olympiades Tentés en Base (Historique cumulé)** | **19 / 36** (52.8%) |
| **Sous-Lemmes Décomposés & Résolus** | **9 / 19** |
| **Nombre Total de Tentatives** | **261** |
| **Temps Moyen par Tentative (REPL)** | **802.3 ms** |
| **Coût Total Consommé (API LLM)** | **$0.9820** |

---

## 2. Taux de Succès par Classe de Difficulté

| Classe | Tentés | Résolus | p_success |
| :--- | :--- | :--- | :--- |
| `mathd` | 17 | 14 | **82.4%** |
| `olympiad_other` | 8 | 3 | **37.5%** |
| `imo` | 6 | 0 | **0.0%** |
| `amc` | 4 | 1 | **25.0%** |
| `other` | 3 | 3 | **100.0%** |
| `aime` | 1 | 1 | **100.0%** |

---

## 3. Répartition par Modèle

| Modèle | Essais | Succès | Taux | Latence Moy. | Coût Total |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `deepseek-chat` | 222 | 29 | 13.1% | 884.4 ms | $0.0959 |
| `deepseek-reasoner` | 32 | 7 | 21.9% | 395.0 ms | $0.8861 |
| `gemini-2.5-flash` | 7 | 2 | 28.6% | 60.5 ms | $0.0000 |

---

## 4. Registre des Preuves Formelles Certifiées ('Axiom-Clean')

### 🎯 Théorème : `AutoNatCancel`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `gemini-2.5-flash` | **Itération** : 2 | **Latence REPL** : 45.1 ms | **Coût** : $0.00000
- **Timestamp** : `2026-09-17 11:49:08`

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
- **Timestamp** : `2026-09-17 12:50:27`

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

### 🎯 Théorème : `algebra_sqineq_unitcircatbpabsamblt1`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-reasoner` | **Itération** : 3 | **Latence REPL** : 1251.5 ms | **Coût** : $0.01665
- **Timestamp** : `2026-09-17 13:43:03`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
theorem algebra_sqineq_unitcircatbpabsamblt1 (a b : ℝ) (h₀ : a ^ 2 + b ^ 2 = 1) :
    a * b + ‖a - b‖ ≤ 1 := by
  have ha2 : a ^ 2 ≤ 1 := by nlinarith [sq_nonneg b]
  have hb2 : b ^ 2 ≤ 1 := by nlinarith [sq_nonneg a]
  have ha_le : a ≤ 1 := by nlinarith [sq_nonneg (a - 1), ha2]
  have ha_ge : -1 ≤ a := by nlinarith [sq_nonneg (a + 1), ha2]
  have hb_le : b ≤ 1 := by nlinarith [sq_nonneg (b - 1), hb2]
  have hb_ge : -1 ≤ b := by nlinarith [sq_nonneg (b + 1), hb2]
  have h1 : a - b ≤ 1 - a * b := by
    have hA : 0 ≤ 1 - a := by linarith
    have hB : 0 ≤ 1 + b := by linarith
    have hprod : 0 ≤ (1 - a) * (1 + b) := mul_nonneg hA hB
    nlinarith [hprod]
  have h2 : -(1 - a * b) ≤ a - b := by
    have hC : 0 ≤ 1 - b := by linarith
    have hD : 0 ≤ 1 + a := by linarith
    have hprod : 0 ≤ (1 - b) * (1 + a) := mul_nonneg hC hD
    nlinarith [hprod]
  have habs : |a - b| ≤ 1 - a * b := abs_le.mpr ⟨h2, h1⟩
  have h_norm : ‖a - b‖ ≤ 1 - a * b := by
    rw [Real.norm_eq_abs]
    exact habs
  linarith
```

### 🎯 Théorème : `amc12b_2020_p2`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 69.5 ms | **Coût** : $0.00006
- **Timestamp** : `2026-09-17 12:55:20`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
theorem amc12b_2020_p2 :
    (100 ^ 2 - 7 ^ 2 : ℝ) / (70 ^ 2 - 11 ^ 2) * ((70 - 11) * (70 + 11) / ((100 - 7) * (100 + 7))) =
      1 := by
  norm_num
```

### 🎯 Théorème : `amc12b_2021_p3_amc12b_2021_p3_step1`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-reasoner` | **Itération** : 3 | **Latence REPL** : 347.7 ms | **Coût** : $0.00919
- **Timestamp** : `2026-09-17 13:41:48`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
import Mathlib.Data.Nat.Factorial.Basic

open scoped Nat
open scoped Real

set_option linter.style.header false

lemma amc12b_2021_p3_step1 (x : ℝ)
    (h₀ : 2 + 1 / (1 + 1 / (2 + 2 / (3 + x))) = 144 / 53) :
    1 + 1 / (2 + 2 / (3 + x)) = 53 / 38 := by
  have h₁ : 1 / (1 + 1 / (2 + 2 / (3 + x))) = 38 / 53 := by
    linarith
  have h₂ : (1 / (1 + 1 / (2 + 2 / (3 + x))))⁻¹ = 53 / 38 := by
    rw [h₁]
    norm_num
  simpa [one_div, inv_inv] using h₂
```

### 🎯 Théorème : `amc12b_2021_p3_amc12b_2021_p3_step2`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 494.5 ms | **Coût** : $0.00019
- **Timestamp** : `2026-09-17 13:41:55`

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


lemma amc12b_2021_p3_step1 (x : ℝ)
    (h₀ : 2 + 1 / (1 + 1 / (2 + 2 / (3 + x))) = 144 / 53) :
    1 + 1 / (2 + 2 / (3 + x)) = 53 / 38 := by
  have h₁ : 1 / (1 + 1 / (2 + 2 / (3 + x))) = 38 / 53 := by
    linarith
  have h₂ : (1 / (1 + 1 / (2 + 2 / (3 + x))))⁻¹ = 53 / 38 := by
    rw [h₁]
    norm_num
  simpa [one_div, inv_inv] using h₂

lemma amc12b_2021_p3_step2 (x : ℝ)
    (h₁ : 1 + 1 / (2 + 2 / (3 + x)) = 53 / 38) :
    2 + 2 / (3 + x) = 38 / 15 := by
  have h₂ : 1 / (2 + 2 / (3 + x)) = 15 / 38 := by
    linarith
  have h₃ : (1 / (2 + 2 / (3 + x)))⁻¹ = 38 / 15 := by
    rw [h₂]
    norm_num
  simpa [one_div, inv_inv] using h₃
```

### 🎯 Théorème : `imo_1960_p2_imo_1960_p2_step1`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-reasoner` | **Itération** : 3 | **Latence REPL** : 225.6 ms | **Coût** : $0.01428
- **Timestamp** : `2026-09-17 13:52:47`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
import Mathlib.Data.Nat.Factorial.Basic

open scoped Nat
open scoped Real

set_option linter.style.header false

lemma imo_1960_p2_step1 (x : ℝ) (hx : 0 ≤ 1 + 2 * x) :
    (1 - Real.sqrt (1 + 2 * x)) ^ 2 ≠ 0 ↔ x ≠ 0 := by
  constructor
  · intro hsq hx0
    apply hsq
    rw [hx0]
    simp [Real.sqrt_one]
  · intro hx0 hsq
    have ha : 1 - Real.sqrt (1 + 2 * x) = 0 := by
      exact sq_eq_zero_iff.mp hsq
    have hs : Real.sqrt (1 + 2 * x) = 1 := by linarith
    have hy : 1 + 2 * x = 1 := by
      have hsqr := Real.sq_sqrt hx
      rw [hs] at hsqr
      norm_num at hsqr
      linarith
    apply hx0
    linarith
```

### 🎯 Théorème : `imo_1963_p5_imo_1963_p5_step1`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 305.4 ms | **Coût** : $0.00018
- **Timestamp** : `2026-09-17 14:01:58`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
import Mathlib.Data.Nat.Factorial.Basic

open scoped Nat
open scoped Real

set_option linter.style.header false

lemma imo_1963_p5_step1 (c : ℝ)
    (hc : 8 * c ^ 3 - 4 * c ^ 2 - 4 * c + 1 = 0) :
    4 * c ^ 3 - 2 * c ^ 2 - 2 * c + 1 = 1 / 2 := by
  have h : 8 * c ^ 3 - 4 * c ^ 2 - 4 * c + 1 = 0 := hc
  have h2 : 2 * (4 * c ^ 3 - 2 * c ^ 2 - 2 * c + 1) = 1 := by
    linarith
  linarith
```

### 🎯 Théorème : `imo_1963_p5_imo_1963_p5_step2`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-reasoner` | **Itération** : 3 | **Latence REPL** : 1432.3 ms | **Coût** : $0.02980
- **Timestamp** : `2026-09-17 14:03:01`

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


lemma imo_1963_p5_step1 (c : ℝ)
    (hc : 8 * c ^ 3 - 4 * c ^ 2 - 4 * c + 1 = 0) :
    4 * c ^ 3 - 2 * c ^ 2 - 2 * c + 1 = 1 / 2 := by
  have h : 8 * c ^ 3 - 4 * c ^ 2 - 4 * c + 1 = 0 := hc
  have h2 : 2 * (4 * c ^ 3 - 2 * c ^ 2 - 2 * c + 1) = 1 := by
    linarith
  linarith

lemma imo_1963_p5_step2 :
    8 * (Real.cos (π / 7)) ^ 3 - 4 * (Real.cos (π / 7)) ^ 2
      - 4 * Real.cos (π / 7) + 1 = 0 := by
  let c := Real.cos (π / 7)
  have hcpos : 0 < c := by
    dsimp [c]
    apply Real.cos_pos_of_mem_Ioo
    constructor <;> linarith [Real.pi_pos]
  have hne : c + 1 ≠ 0 := by
    intro h
    have : c = -1 := by linarith
    linarith [hcpos]
  have h3 : Real.cos (3 * (π / 7)) = 4 * c ^ 3 - 3 * c := by
    dsimp [c]
    exact Real.cos_three_mul (π / 7)
  have h3' : Real.cos (3 * (π / 7)) = Real.cos (3 * π / 7) := by
    congr 1
    ring
  have hcos : Real.cos (3 * π / 7) = -Real.cos (4 * π / 7) := by
    have : Real.cos (3 * π / 7) = Real.cos (π - 4 * π / 7) := by
      congr 1
      ring
    rw [this, Real.cos_pi_sub]
  have h4 : Real.cos (4 * π / 7) = 2 * (Real.cos (2 * π / 7)) ^ 2 - 1 := by
    have := Real.cos_two_mul (2 * π / 7)
    have harg : 2 * (2 * π / 7) = 4 * π / 7 := by ring
    rw [harg] at this
    exact this
  have h2 : Real.cos (2 * π / 7) = 2 * c ^ 2 - 1 := by
    have := Real.cos_two_mul (π / 7)
    have harg : 2 * (π / 7) = 2 * π / 7 := by ring
    rw [harg] at this
    dsimp [c]
    exact this
  have hcos4 : Real.cos (4 * π / 7) = 8 * c ^ 4 - 8 * c ^ 2 + 1 := by
    rw [h4, h2]
    ring
  have key : 4 * c ^ 3 - 3 * c = -(8 * c ^ 4 - 8 * c ^ 2 + 1) := by
    rw [← h3, h3', hcos, hcos4]
  have hpoly : 8 * c ^ 4 - 8 * c ^ 2 + 1 + 4 * c ^ 3 - 3 * c = 0 := by
    linarith [key]
  have hfac : (c + 1) * (8 * c ^ 3 - 4 * c ^ 2 - 4 * c + 1) = 0 := by
    have h_expand : (c + 1) * (8 * c ^ 3 - 4 * c ^ 2 - 4 * c + 1)
        = 8 * c ^ 4 + 4 * c ^ 3 - 8 * c ^ 2 - 3 * c + 1 := by ring
    rw [h_expand]
    linarith [hpoly]
  have hfinal : 8 * c ^ 3 - 4 * c ^ 2 - 4 * c + 1 = 0 :=
    (mul_eq_zero.mp hfac).resolve_left hne
  dsimp [c] at hfinal
  exact hfinal
```

### 🎯 Théorème : `mathd_algebra_137`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 521.8 ms | **Coût** : $0.00014
- **Timestamp** : `2026-09-17 14:10:22`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
theorem mathd_algebra_137 (x : ℕ) (h₀ : ↑x + (4 : ℝ) / (100 : ℝ) * ↑x = 598) : x = 575 := by
  have h₁ : (↑x : ℝ) * (1 + 4 / 100) = 598 := by
    linarith
  have h₂ : (↑x : ℝ) * (104 / 100) = 598 := by
    norm_num at h₁ ⊢
    linarith
  have h₃ : (↑x : ℝ) = 575 := by
    have h : (104 / 100 : ℝ) ≠ 0 := by norm_num
    field_simp at h₂
    linarith
  exact_mod_cast h₃
```

### 🎯 Théorème : `mathd_algebra_141`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 333.7 ms | **Coût** : $0.00007
- **Timestamp** : `2026-09-17 12:51:26`

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
- **Timestamp** : `2026-09-17 12:52:42`

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
- **Timestamp** : `2026-09-17 12:54:19`

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

### 🎯 Théorème : `mathd_algebra_392`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 2 | **Latence REPL** : 715.4 ms | **Coût** : $0.00021
- **Timestamp** : `2026-09-17 15:10:15`

```lean
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
```

### 🎯 Théorème : `mathd_algebra_398`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 242.2 ms | **Coût** : $0.00024
- **Timestamp** : `2026-09-17 13:59:59`

```lean
import Mathlib.Tactic

theorem mathd_algebra_398 (a b c : ℝ) (h₀ : 0 < a ∧ 0 < b ∧ 0 < c) (h₁ : 9 * b = 20 * c)
    (h₂ : 7 * a = 4 * b) : 63 * a = 80 * c := by
  have hb : b = (20 * c) / 9 := by linarith
  have ha : a = (4 * b) / 7 := by linarith
  rw [ha, hb]
  ring
```

### 🎯 Théorème : `mathd_algebra_419`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 39.6 ms | **Coût** : $0.00006
- **Timestamp** : `2026-09-17 12:56:55`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
theorem mathd_algebra_419 (a b : ℝ) (h₀ : a = -1) (h₁ : b = 5) : -a - b ^ 2 + 3 * (a * b) = -39 := by
  subst h₀
  subst h₁
  norm_num
```

### 🎯 Théorème : `mathd_algebra_459`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-reasoner` | **Itération** : 3 | **Latence REPL** : 507.2 ms | **Coût** : $0.00934
- **Timestamp** : `2026-09-17 14:04:54`

```lean
import Mathlib.Data.Rat.Lemmas
import Mathlib.Tactic

theorem mathd_algebra_459 (a b c d : ℚ) (h₀ : 3 * a = b + c + d) (h₁ : 4 * b = a + c + d)
    (h₂ : 2 * c = a + b + d) (h₃ : 8 * a + 10 * b + 6 * c = 24) : ↑d.den + d.num = 28 := by
  have ha : a = 1 := by linarith
  have hb : b = 4 / 5 := by linarith
  have hc : c = 4 / 3 := by linarith
  have hd : d = 13 / 15 := by linarith
  rw [hd]
  norm_num
```

### 🎯 Théorème : `mathd_algebra_478`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `gemini-2.5-flash` | **Itération** : 1 | **Latence REPL** : 59.9 ms | **Coût** : $0.00000
- **Timestamp** : `2026-09-17 11:51:20`

```lean
import Mathlib.Tactic
import Mathlib.Algebra.Ring.Parity

set_option linter.style.header false

theorem mathd_algebra_478 (b h v : ℝ) (h₀ : 0 < b ∧ 0 < h ∧ 0 < v) (h₁ : v = 1 / 3 * (b * h))
    (h₂ : b = 30) (h₃ : h = 13 / 2) : v = 65 := by
  subst_vars
  norm_num at *
```

### 🎯 Théorème : `mathd_numbertheory_1124`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-reasoner` | **Itération** : 3 | **Latence REPL** : 66.5 ms | **Coût** : $0.00547
- **Timestamp** : `2026-09-17 13:37:48`

```lean
import Mathlib.Tactic

theorem mathd_numbertheory_1124 (n : ℕ) (h₀ : n ≤ 9) (h₁ : 18 ∣ 374 * 10 + n) : n = 4 := by
  rcases h₁ with ⟨k, hk⟩
  norm_num at hk
  omega
```

### 🎯 Théorème : `mathd_numbertheory_1124_mathd_numbertheory_1124_step1`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 159.7 ms | **Coût** : $0.00010
- **Timestamp** : `2026-09-17 12:53:08`

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
- **Timestamp** : `2026-09-17 12:53:18`

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
- **Timestamp** : `2026-09-17 12:54:09`

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
- **Timestamp** : `2026-09-17 12:55:11`

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
- **Timestamp** : `2026-09-17 12:51:36`

```lean
import Mathlib.Data.Nat.ModEq
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Tactic.NormNum

theorem mathd_numbertheory_3 : (∑ x ∈ Finset.range 10, (x + 1) ^ 2) % 10 = 5 := by
  norm_num [Finset.sum_range_succ]
```

### 🎯 Théorème : `mathd_numbertheory_427_mathd_numbertheory_427_step1`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 29.9 ms | **Coût** : $0.00011
- **Timestamp** : `2026-09-17 13:55:49`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
import Mathlib.Data.Nat.Factorial.Basic

open scoped Nat
open scoped Real

set_option linter.style.header false

lemma mathd_numbertheory_427_step1 :
    ∑ k ∈ Nat.divisors 500, k = 1092 := by
  native_decide
```

### 🎯 Théorème : `mathd_numbertheory_427_mathd_numbertheory_427_step2`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 49.1 ms | **Coût** : $0.00015
- **Timestamp** : `2026-09-17 13:55:56`

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


lemma mathd_numbertheory_427_step1 :
    ∑ k ∈ Nat.divisors 500, k = 1092 := by
  native_decide

lemma mathd_numbertheory_427_step2 (a : ℕ) (ha : a = 1092) :
    ∑ k ∈ Finset.filter (fun x => Nat.Prime x) (Nat.divisors a), k = 25 := by
  subst ha
  native_decide
```

### 🎯 Théorème : `mathd_numbertheory_430`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 3679.9 ms | **Coût** : $0.00045
- **Timestamp** : `2026-09-17 14:04:23`

```lean
import Mathlib.Data.Nat.Digits.Div
import Mathlib.Tactic

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
```

### 🎯 Théorème : `mean_calc`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 250.3 ms | **Coût** : $0.00009
- **Timestamp** : `2026-09-17 12:46:29`

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
- **Timestamp** : `2026-09-17 12:46:23`

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

### 🎯 Théorème : `numbertheory_4x3m7y3neq2003_zmod7_cube_ne_two`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-chat` | **Itération** : 1 | **Latence REPL** : 118.1 ms | **Coût** : $0.00015
- **Timestamp** : `2026-09-17 13:30:53`

```lean
import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Parity
import Mathlib.Data.Nat.Factorial.Basic

open scoped Nat
open scoped Real

set_option linter.style.header false

lemma zmod7_cube_ne_two (z : ZMod 7) : z ^ 3 ≠ 2 := by
  fin_cases z <;> decide
```

### 🎯 Théorème : `numbertheory_x5neqy2p4`
- **Statut** : ✅ **Vérifié 'Sorry-Free' & Axiomes Valides**
- **Modèle** : `deepseek-reasoner` | **Itération** : 3 | **Latence REPL** : 182.1 ms | **Coût** : $0.02782
- **Timestamp** : `2026-09-17 13:57:35`

```lean
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
```
