import Mathlib

section Functions

variable {α β γ : Type*} -- we declare three types
variable (f : α → β) (g : β → γ) (h : α → γ) -- and three functions with specified domains and ranges
variable (x : α)


/-
`LeftInverse g f` means `g ∘ f = id`, i.e. `g (f x) = x`.
`RightInverse g f` means `f ∘ g = id`, i.e. `f (g y) = y`.

`Injective f` means `f x = f y → x = y`.
`Surjective f` means every `y : β` has a preimage under `f`.
`Bijective f` is `Injective f ∧ Surjective f`.
-/
#check 1
#check Function.LeftInverse
#check Function.RightInverse
#check Function.Injective f
#check Function.Surjective f
#check Function.Bijective f

/-
`fR : ℝ → ℝ` is the function x ↦ 2x + 1.
`gR : ℝ → ℝ` is the function x ↦ x² - 4.
-/
def fR (x : ℝ) : ℝ := 2 * x + 1
def gR (x : ℝ) : ℝ := x^2 - 4

noncomputable def fiR (y : ℝ) : ℝ := (y - 1) / 2

lemma fiR_leftInverse : Function.LeftInverse fiR fR := by
  intro x
  simp [fR, fiR]

#check fiR_leftInverse

example (x : ℝ) : fiR (fR x) = x :=
  fiR_leftInverse x

example : Function.Injective fR :=
  (Function.LeftInverse.injective fiR_leftInverse)

example : Function.Injective fR := by
  intro x y h
  simp [fR] at h
  exact h

def some_func (x : ℝ) : ℝ := 3*x - 1

lemma some_func_surjective : Function.Surjective some_func := by
  intro y
  refine ⟨( y + 1 ) / 3 , ?_⟩ -- we need to show that some_func ((y + 1) / 3) = y. ?_ is a placeholder for the goal that we need to prove.
  simp [some_func]
  ring

example some_func_surjective : Function.Surjective some_func := by
  intro y
  use (y+1)/3
  simp [some_func]
  ring

/-
Another simple function: `shift2 x = x - 2`.
We will compose `hR` with `shift2`.
-/
def shift2 (x : ℝ) : ℝ := x - 2

/-
Evaluate the composition (hR ∘ shift2) at some concrete points.
-/

-- def fR (x : ℝ) : ℝ := 2 * x + 1
-- noncomputable def fiR (y : ℝ) : ℝ := (y - 1) / 2

example : Function.LeftInverse fiR fR := by
  intro x
  -- goal: fiR (fR x) = x
  -- unfold the definitions
  dsimp [fiR, fR] -- dsimp is a tactic that unfolds definitions
  -- goal is now: ((2 * x + 1) - 1) / 2 = x
  have h1 : ((2 : ℝ) * x + 1 - 1) = 2 * x := by
    ring                -- from Mathlib
  have h2 : (2 * x) / 2 = x := by
    -- lemma: a * b / b = a when b ≠ 0
    simp [mul_comm]
  simp [h1, h2]


example (hf : Function.Injective f) (hg : Function.Injective g) : Function.Injective (g ∘ f) := by -- `circ` is the notation for function composition, that is, (g ∘ f) x = g (f x)
  intro x y hcomp
  -- use injectivity of `g` on the equation `g (f x) = g (f y)`
  have hfxy : f x = f y := hg hcomp
  -- then use injectivity of `f` to conclude `x = y`
  exact hf hfxy

/-
Now a concrete example over the integers `ℤ`.

`addTwo` is the function `z ↦ z + 2`.
`timesThree` is the function `z ↦ 3 * z`.
We will show both are injective.
-/
/-
def shift2 (x : ℝ) : ℝ := x - 2
-/
def addTwo : ℤ → ℤ := fun z => z + 2
def timesThree : ℤ → ℤ := fun z => 3 * z
def addTwoReal : ℝ → ℝ := fun z => z + 2

#eval addTwo 5
#eval addTwoReal 5.0
example : addTwo 5 = 7 := by
  rfl

#eval timesThree 4

/-
congrArg is another tool from the Mathlib library. In fact, it is a general lemma that allows you to apply a function to both sides of an equality.
Its type is:

congrArg : {α β : Sort u} → (f : α → β) → {x y : α} → x = y → f x = f y

In practtice, we use it with the following syntax :
have := congrArg (fun t => ...) h

-/

example (x y : ℕ) (h : x = y) : x + 5 = y + 5 := by
  have := congrArg (fun t => t + 5) h
  exact this

example : Function.Injective addTwo := by
  intro z w h
  have := congrArg (fun t => t - 2) h
  simp [addTwo] at this
  exact this

/-
`timesThree` is injective:

If `3 * x = 3 * y` and `3 ≠ 0`, we can cancel `3` from the left.

`mul_left_cancel₀` says: if `a ≠ 0` and `a * x = a * y` then `x = y`.

`by decide` is a small automation that proves `3 ≠ 0` in `ℤ`.
-/

example : Function.Injective timesThree := by
  intro x y h
  have : 3 ≠ 0 := by decide
  simp [timesThree] at h
  exact h

example : Function.Injective timesThree := by
  intro x y h
  have := congrArg (fun t => t/3) h
  simp [timesThree] at this
  exact this

/-
A family of bijections on `ℤ`:

`shift k` is the function `z ↦ z + k`. Intuitively this is a translation
by `k`, and it should be a bijection with inverse `z ↦ z - k`.
-/
def shift (k : ℤ) : ℤ → ℤ := fun z => z + k

/-
We now prove that `shift k` is bijective for every integer `k`.

- Injective part:
  If `x + k = y + k`, we can cancel `k` from the left.

- Surjective part:
  Given `y`, we need `x` with `shift k x = y`.
  Take `x := y - k`. Then:
    `shift k (y - k) = (y - k) + k = y`.

We use a small list of lemmas about addition and subtraction to
simplify this expression.
-/
#print Function.Bijective

example (k : ℤ) : Function.Bijective (shift k) := by
  refine ⟨?inj, ?surj⟩ -- refine is like constructor but for structures, that is, we can use refine to build a structure by providing its fields one by one
  · -- injectivity
    intro x y h
    have : x + k = y + k := h
    exact add_right_cancel this
  · -- surjectivity
    intro y
    use y-k
    simp [shift]
end Functions


section FunctionLimits

/-
We now consider real-valued functions f : ℝ → ℝ and limits at a point a.

Mathematical definition:

  lim_{x → a} f(x) = ℓ   means

    ∀ ε > 0, ∃ δ > 0, ∀ x,
      0 < |x - a| → |x - a| < δ → |f x - ℓ| < ε.

We exclude x = a by the condition 0 < |x - a|.
-/
def LimitAt (f : ℝ → ℝ) (a ℓ : ℝ) : Prop :=
  ∀ ε > 0, ∃ δ > 0, ∀ x, 0 < |x - a| → |x - a| < δ → |f x - ℓ| < ε

/-
Unfolding lemma for convenience.
-/
theorem LimitAt_iff {f : ℝ → ℝ} {a ℓ : ℝ} :
    LimitAt f a ℓ ↔
      ∀ ε > 0, ∃ δ > 0,
        ∀ x, 0 < |x - a| → |x - a| < δ → |f x - ℓ| < ε := by
  rfl

/-
Constant function:

If f(x) = c for all x, then lim_{x→a} f(x) = c.

Proof: |c - c| = 0 < ε for every ε > 0; any δ > 0 works.
-/
theorem LimitAt.const {a c :ℝ} : LimitAt (fun _ : ℝ => c) a c := by
  intro ε hε
   -- we can choose any δ > 0; take δ = 1.
  use 1
  norm_num
  intro x hxnot0 hx1
  trivial
  -- exact hε

  /-
  intro ε hε
   -- we can choose any δ > 0; take δ = 1.
  refine ⟨1, by norm_num, ?_⟩
  intro x hx0 hxδ
  have : |(fun _ : ℝ => c) x - c| = 0 := by
    simp
  simp [hε]
-/

def f (x : ℝ) : ℝ := x + 2

example (a : ℝ) : LimitAt f a (a + 2) := by
  intro ε hε
  simp [f]
  refine ⟨ε, hε, ?_⟩
  intro x hxnot0 hxε
  exact hxε


/-
A small but useful lemma: if two functions agree near a point (for all x ≠ a),
they have the same limit there.

Formally:

If f and g satisfy  g x = f x  for all x ≠ a, and f has limit ℓ at a,
then g also has limit ℓ at a.

The identifier (that is congr) follows the common Lean mathlib convention of naming lemmas : we use Something.congr when we want to state that two objects that agree on the relevant domain have the same property.
-/
theorem LimitAt.congr {f g : ℝ → ℝ} {a ℓ : ℝ}
    (h : ∀ x, x ≠ a → g x = f x)
    (hf : LimitAt f a ℓ) :
    LimitAt g a ℓ := by
  unfold LimitAt at *
  intro ε hε
  rcases hf ε hε with ⟨δ, hδpos, hδ⟩
  norm_num
  refine ⟨ δ, hδpos, ?_ ⟩
  intro x hxnot0 hxδ
  have xnota : x ≠ a := by
    intro hxa
    apply hxnot0
    simp [hxa]
  have hgequalf : g x = f x := h x xnota
  simp at hδ
  simp [hgequalf]
  exact hδ x hxnot0 hxδ

/-
  refine ⟨δ, hδpos, ?_⟩
  intro x hx0 hxδ
  -- from 0 < |x - a| we know x ≠ a
  have hxne : x ≠ a := by
    have hz : |x - a| ≠ 0 := ne_of_gt hx0
    intro hxa
    apply hz
    simp -- |x - a| = |a - a| = 0

  have hgf : g x = f x := h x hxne
  have hfx : |f x - ℓ| < ε := hδ x hx0 hxδ
  simp [hgf] using hfx
-/

/-
Example: limit of a function that is "almost constant".

Suppose g(x) = 1 for all x ≠ a, and g(a) is defined arbitrarily.
Then lim_{x→a} g(x) = 1.

We show this by comparing with the constant function x ↦ 1.
-/

#print LimitAt.const

example (a : ℝ) (g : ℝ → ℝ)
    (h : ∀ x, x ≠ a → g x = 1) :
    LimitAt g a 1 := by
  -- constant function 1 has limit 1 at a
  have hconst : LimitAt (fun _ : ℝ => (1 : ℝ)) a 1 := LimitAt.const

  -- Lean understands the parameters a and 1 as implicit, so we can just write LimitAt.const without parameters. It can be the case that these parameters are not inferred correctly, so we can also write @LimitAt.const a 1 to specify them explicitly.

  /-
  have hconst : LimitAt (fun _ : ℝ => (1 : ℝ)) a 1 := by
    -- use the example above with c = 1
    simpa using (show LimitAt (fun _ : ℝ => (1 : ℝ)) a 1 from
      (by
        intro ε hε
        refine ⟨1, by norm_num, ?_⟩
        intro x hx0 hxδ
        have : |(fun _ : ℝ => (1 : ℝ)) x - 1| = 0 := by simp
        simpa [this] using hε))
    -/

  -- now we use the congruence lemma
  have h' : ∀ x, x ≠ a → g x = (fun _ : ℝ => (1 : ℝ)) x := by
    intro x hxne
    simpa using h x hxne
  exact LimitAt.congr h' hconst

/-
Standard facts (not all proved here):

- Limits, when they exist, are unique.
- Linearity: if lim f = L and lim g = M, then lim (f+g) = L+M.
- Product rule: if lim f = L and lim g = M, then lim (fg) = LM.

These can all be proved from the ε–δ definition with usual analysis
arguments and the triangle inequality.
-/

theorem LimitAt.sum {f g : ℝ → R} {a L M :ℝ} (hf : LimitAt f a L) (hg : LimitAt g a M) : LimitAt (fun x => f x + g x ) a ( L + M) := by
  sorry

theorem LimitAt.diff {f g : ℝ → R} {a L M :ℝ} (hf : LimitAt f a L) (hg : LimitAt g a M) : LimitAt (fun x => f x * g x ) a ( L * M) := by
  sorry

end FunctionLimits
