import Mathlib

section Sets
/-
Some `#check` lines: these ask Lean "what is the type of this expression?"
They are useful for exploring library definitions.
-/
#check Set                 -- Type* → Type*
#check Set.univ            -- universal set (all elements of a type)
#check Set.empty_def       -- a lemma about ∅ (definition)

/-
Basic set constructions:
-/

variable {α : Type*}
variable (A B : Set α)
variable (f : α → β)

#check A ∪ B               -- union of `A` and `B`
#check A ∩ B               -- intersection
#check Aᶜ                  -- complement of `A` (relative to the universe `α`)
#check A \ B               -- set difference: elements in `A` but not in `B`
#check f '' A              -- image of `A` under `f`

------------------------------------------------------------
-- Suggested additional facts about sets
------------------------------------------------------------

/-
Subset reflexivity: every set is a subset of itself.
This follows immediately from the definition of `⊆`.
-/
example : A ⊆ A := by
  intro x hx
  exact hx

/-
Subset transitivity:
If `A ⊆ B` and `B ⊆ C`, then `A ⊆ C`.

We apply both inclusions in sequence.
-/
example {C : Set α} (hAB : A ⊆ B) (hBC : B ⊆ C) : A ⊆ C := by
  intro x hx
/-  have : x ∈ B := by exact (hAB hx)
  have t : x ∈ C := by exact (hBC this)
  exact t
-/
  exact hBC (hAB hx)


/-
Empty set is a subset of every set (already seen).
Conversely, no set is a subset of ∅ unless it is empty.

This shows: if `A ⊆ ∅`, then `A = ∅`.
Proof: extensionality reduces to showing membership equivalence.
-/
example (hA : A ⊆ (∅ : Set α)) : A = ∅ := by
  by_cases he : A = ∅
  · exact he
  · -- Assume A ≠ ∅, so A contains an element
    have hne : A.Nonempty := Set.nonempty_iff_ne_empty.mpr he
    obtain ⟨a, ha⟩ := hne -- as we know that A is not empty, hne is a proof of ∃ x, x ∈ A. With this line, the hyphothesis hne is transformed to the definition : a is an element (in the type α), contained in A.
    -- From hA, a ∈ ∅
    have : a ∈ ∅ := hA ha
    -- Contradiction
    contradiction

/-
our context contains:
ha : a ∈ A
hA : A ⊆ ∅
So have : a ∈ ∅ is now in the context.
Lean knows the lemma Set.not_mem_empty a : ¬(a ∈ ∅) from the library.
-/


example (hA : A ⊆ (∅ : Set α)) : A = ∅ := by
  by_cases he : A = ∅
  · exact he
  · -- Assume A ≠ ∅, so A contains an element
    have hne : A.Nonempty := Set.nonempty_iff_ne_empty.mpr he
    cases hne with
    | intro a ha =>
      -- From hA, a ∈ ∅
      have : a ∈ ∅ := hA ha
      contradiction

/-
Characterization of intersection membership:
`x ∈ A ∩ B ↔ x ∈ A ∧ x ∈ B`.

This is definitional, so `rfl` works.
-/
example {x : α} : x ∈ A ∩ B ↔ x ∈ A ∧ x ∈ B := by
  rfl

/-
Characterization of union membership:
`x ∈ A ∪ B ↔ x ∈ A ∨ x ∈ B`.

Again definitional.
-/
example {x : α} : x ∈ A ∪ B ↔ x ∈ A ∨ x ∈ B := by
  rfl

/-
Difference membership:
`x ∈ A \ B` means `x ∈ A` and `x ∉ B`.
-/
example {x : α} : x ∈ A \ B ↔ x ∈ A ∧ x ∉ B := by
  rfl

/-
Complement facts: `A ∩ Aᶜ = ∅`.

If `x ∈ A` and `x ∈ Aᶜ`, we contradict `x ∉ A`.
-/
example : A ∩ Aᶜ = (∅ : Set α) := by
  by_cases hempty : A = ∅
  · have : Aᶜ = Set.univ := by
      rw[hempty]
      exact Set.compl_empty
    rw [this]
    rw [hempty]
    exact Set.empty_inter Set.univ

  · -- intro x fails.
    ext x
    /- the tactic `ext` stands for extensionality. It is used to prove equalities of objects that are defined by their elements, such as sets, functions, or further structures. In this case :
    1. Lean knows that two sets are equal if they have the same elements.
    2. ext x introduces an arbitrary element x that is in both A and Aᶜ.
    Notice that the goal was the equality of two sets, and it has changed now.
    -/
    simp -- `simp` works in this case. But, we may also go ahead and prove the statement directly.
example : A ∩ Aᶜ = (∅ : Set α) := by
  by_cases hempty : A = ∅
  · have : Aᶜ = Set.univ := by
      rw [hempty, Set.compl_empty]
    rw [this, hempty, Set.empty_inter]
  · ext x
    constructor
    · intro h
      have hinA : x ∈ A := h.left
      have hinAcompl : x ∈ Aᶜ := h.right
      contradiction
    · intro h
      contradiction

/-
Union with complement gives the universal set:
`A ∪ Aᶜ = univ`.

If `x` is in `A`, done; otherwise `x ∈ Aᶜ`.
-/
example : A ∪ Aᶜ = (Set.univ : Set α) := by
  rw [Set.Subset.antisymm_iff]
  constructor
  · intro x hx
    exact Set.mem_univ x
  · intro x hx
    by_cases h : x ∈ A
    · left; exact h
    · right; exact h

end Sets

section Functions

open Real
/- - Section 4: Functions -/

/-
We now work with three types `α`, `β`, `γ` and three functions:
- `f : α → β`
- `g : β → γ`
- `h : α → γ`

We will look at function composition and the usual properties:
injectivity, surjectivity, bijectivity.
-/

variable {α β γ : Type*} -- we declare three types
variable (f : α → β) (g : β → γ) (h : α → γ) -- and three functions with specified domains and ranges
variable (x : α)

/-
`fR : ℝ → ℝ` is the function x ↦ 2x + 1.
`gR : ℝ → ℝ` is the function x ↦ x² - 4.
-/
def fR (x : ℝ) : ℝ := 2 * x + 1
def gR (x : ℝ) : ℝ := x^2 - 4

/-
Evaluating `fR` at some concrete points.
-/

#eval fR 0

example : fR 0 = 1 := by
  -- fR 0 = 2 * 0 + 1 = 1
  simp [fR]

example : fR 3 = 7 := by
  -- fR 3 = 2 * 3 + 1 = 7
  norm_num [fR]

/-
Evaluating `gR` at some concrete points.
-/
example : gR (-3) = 5 := by
  -- gR (-3) = (-3)^2 - 4 = 9 - 4 = 5
  norm_num [gR]

example : Real.sin (π / 6) = 1 / 2 := by
  simp [Real.sin_pi_div_six]

example : Real.sin (π / 4) = Real.sqrt 2 / 2 := by
  simp [Real.sin_pi_div_four]

example : Real.tan (π / 4) = 1 := by
  simp [Real.tan_pi_div_four]

#check Real.log
#check Real.exp 1

-- #eval fR (Real.exp 1)
-- #eval fR (Real.sqrt 2)
#eval fR 1.5
 -- #eval fR ( (3 : ℚ) / (2 : ℚ) )
#check 3/2
#check 1.5
-- #eval Real.exp 1


-- def hR (x : ℝ) : ℝ := Real.sin x

noncomputable def hR (x : ℝ) : ℝ := Real.sin x

example : hR (π / 3) = Real.sqrt 3 / 2 := by
  simp [hR,Real.sin_pi_div_three]


#check hR 3        -- type check: fR 3 : ℝ
-- #eval hR (3:ℝ) will produce an error

def piF : Float := 3.141592653589793
def approxSin (x : Float) : Float :=
  Float.sin x

#eval approxSin (piF / 3)
#eval Float.sqrt 3 / 2
#eval approxSin (piF / 6)
#eval approxSin 3.0


/-
Composition (gR ∘ fR) : ℝ → ℝ is x ↦ gR (fR x).
We compute a closed-form expression for this composition.
-/
example (x : ℝ) : (gR ∘ fR) x = 4 * x^2 + 4 * x - 3 := by
  -- (gR ∘ fR) x = (2x + 1)^2 - 4 = 4x² + 4x - 3
  simp [Function.comp, gR, fR]
  ring

/-
We can also check the composition at specific points.
-/
example : (gR ∘ fR) 3 = 45 := by
  -- (gR ∘ fR) 3 = gR (fR 3) = gR 7 = 49 - 4 = 45
  norm_num [Function.comp, gR, fR]

example : (gR ∘ fR) 0 = -3 := by
  -- (gR ∘ fR) 0 = gR (fR 0) = gR 1 = 1 - 4 = -3
  simp [Function.comp, gR, fR]
  norm_num

noncomputable def jR (x : ℝ) : ℝ := Real.cos x

example (x : ℝ) : (hR x)^2 + (jR x)^2 = 1 := by
  simp [hR, jR, Real.sin_sq_add_cos_sq]

/-!
A piecewise example: a function `hR : ℝ → ℝ` defined by

  hR(x) = x + 5  if x ≥ 0
        = -x    if x < 0.
-/

noncomputable def hS (x : ℝ) : ℝ :=
  if x ≥ 0 then
    x + 5
  else
    (-x : ℝ)

example : hS 1 = 6 := by
  unfold hS
  norm_num

example : hS (-3) = 3 := by
  -- -3 < 0, so we use the second branch: -(-3) = 3
  unfold hS
  norm_num

lemma hS_eq_add {x : ℝ} (hx : x ≥ 0) : hS x = x + 5 := by
  unfold hS
  simp [hx]

lemma hS_eq_neg {x : ℝ} (hx : x < 0) : hS x = -x := by
  unfold hS
  have hx' : ¬ x ≥ 0 := not_le_of_gt hx
  simp [hx']

lemma hS_nonneg (x : ℝ) : hS x ≥ 0 := by
  by_cases hx : x ≥ 0
  · -- case x ≥ 0: hS x = x + 5
    have hx5 : (0 : ℝ) ≤ 5 := by norm_num
    have : 0 ≤ x + 5 := add_nonneg hx hx5
    -- rewrite hS x as x + 5
    simp [hS, hx, this]
  · -- case x < 0: hS x = -x
    have hxlt : x < 0 := lt_of_not_ge hx
    have hxle : x ≤ 0 := le_of_lt hxlt
    have : 0 ≤ -x := neg_nonneg.mpr hxle
    simp [hS, hx, this]


/-
`LeftInverse g f` means `g ∘ f = id`, i.e. `g (f x) = x`.
`RightInverse g f` means `f ∘ g = id`, i.e. `f (g y) = y`.

`Injective f` means `f x = f y → x = y`.
`Surjective f` means every `y : β` has a preimage under `f`.
`Bijective f` is `Injective f ∧ Surjective f`.
-/
#check Function.LeftInverse
#check Function.RightInverse
#check Function.Injective f
#check Function.Surjective f
#check Function.Bijective f



/-
  Remember :
  def fR (x : ℝ) : ℝ := 2 * x + 1

-/
noncomputable def fiR (y : ℝ) : ℝ := (y - 1) / 2

lemma fiR_leftInverse : Function.LeftInverse fiR fR := by
  intro x
  simp [fR, fiR]

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
  refine ⟨( y + 1 ) / 3 , ?_⟩
  simp [some_func]
  field_simp
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
  dsimp [fiR, fR]
  -- goal is now: ((2 * x + 1) - 1) / 2 = x
  have h1 : ((2 : ℝ) * x + 1 - 1) = 2 * x := by
    ring                -- from Mathlib
  have h2 : (2 * x) / 2 = x := by
    -- lemma: a * b / b = a when b ≠ 0
    simp [mul_comm]
  simp [h1, h2]

end Functions
