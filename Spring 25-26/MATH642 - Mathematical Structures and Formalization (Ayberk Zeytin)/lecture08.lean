import Mathlib.Analysis.Complex.Basic
import Mathlib.Analysis.Calculus.Deriv.Basic
import Mathlib.Analysis.Calculus.FDeriv.Basic
import Mathlib.Analysis.Calculus.FDeriv.Mul
import Mathlib.Analysis.Calculus.FDeriv.Pow
import Mathlib.Analysis.Calculus.Deriv.Basic
import Mathlib.Analysis.Complex.Basic

/-!
# Complex Differentiability in Lean 4

This file demonstrates how to state that a complex function is differentiable
at a point or on a set using Mathlib4.

In complex analysis, a function $f: \mathbb{C} \to \mathbb{C}$ is differentiable
at $z$ if the limit:
$$f'(z) = \lim_{h \to 0} \frac{f(z+h) - f(z)}{h}$$
exists. This is a much stronger condition than real differentiability.
-/

open Complex

-- 1. Defining a function from ℂ to ℂ
def my_complex_fun (z : ℂ) : ℂ := z ^ 2

-- 2. Stating differentiability at a point
-- `DifferentiableAt ℂ f z` means f is complex-differentiable at 0.
example : DifferentiableAt ℂ my_complex_fun 0 := by
  unfold my_complex_fun
  fun_prop

-- 3. Stating differentiability on the entire complex plane - such functions are called entire
-- `Differentiable ℂ f` means f is differentiable at every point in ℂ.
example : Differentiable ℂ my_complex_fun := by
  unfold my_complex_fun
  -- `differentiable` is a powerful tactic in mathlib that handles polynomials,
  -- exponentials, and compositions.
  fun_prop

-- 4. Stating that a linear function is entire.
theorem analytic_linear_manual (a b : ℂ) (z : ℂ) :
    DifferentiableAt ℂ (fun z : ℂ => a * z + b) z := by
    fun_prop

-- 5. Stating that the product of two entire functions is entire.
theorem analytic_product_manual (f g : ℂ → ℂ) (z : ℂ)
    (hf : DifferentiableAt ℂ f z) (hg : DifferentiableAt ℂ g z) :
    DifferentiableAt ℂ (fun z => f z * g z) z := by
  fun_prop

-- 6. Example, using the above two propositions
-- We can use the facts we have proven above, but also fun_prop
example (z : ℂ) : DifferentiableAt ℂ (fun z => (z + 1) * (z + 2)) z := by
  have h1 : DifferentiableAt ℂ (fun z => z + 1) z := by
    simpa using analytic_linear_manual 1 1 z
  have h2 : DifferentiableAt ℂ (fun z => z + 2) z := by
    simpa using analytic_linear_manual 1 2 z
  apply analytic_product_manual (fun z => z + 1) (fun z => z + 2) z h1 h2

example (z : ℂ) :
    DifferentiableAt ℂ (fun z : ℂ => (z + 1) * (z + 2)) z := by
    fun_prop
