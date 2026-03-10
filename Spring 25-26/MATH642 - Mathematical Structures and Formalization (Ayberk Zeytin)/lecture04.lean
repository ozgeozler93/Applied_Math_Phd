import Mathlib


/-
LEAN LECTURE RECAP: FUNDAMENTAL TACTICS AND EXAMPLES

This file is designed to be copy–pasted into a Lean project.
It summarizes the main tactics from the lecture and adds two
worked examples:

1. An induction proof about a sum (similar in spirit to the Gauss sum).
2. A divisibility result over the integers of the form
     x - a ∣ p(x)   ↔   x - a ∣ constant.

We assume we are working with Mathlib available.
-/

open Classical
open Nat Function
open scoped BigOperators
open Finset

/-
------------------------------------------------------------
1. INTRODUCTION AND CONTEXT MANIPULATION
------------------------------------------------------------

`intro` / `intros` :
  Introduce variables or hypotheses into the context.
-/
/-
`cases` :
  Perform case analysis on inductive types (e.g. `Bool`, `Option α`,
  disjunctions, etc.).
-/
/-
------------------------------------------------------------
2. EQUALITY, REWRITING, SIMPLIFICATION
------------------------------------------------------------

`rfl` :
  Closes goals where both sides are definitionally equal.
-/
/-
`rw` :
  Rewrites occurrences using equalities or lemmas.
-/
example (a b : Nat) (h : a = b) : a + 1 = b + 1 := by
  rw [h]

/-
`simp` and `simp_all` :
  Use the global set of `[simp]` lemmas (and local hypotheses)
  to simplify goals and hypotheses.
-/
example (a b : Nat) : (a + 0) + b = a + b := by
  simp

example (a b : ℕ) (h₁ : a = b) (h₂ : b = 2) : a + b = 4 := by
  simp_all


/-
------------------------------------------------------------
3. GOAL TRANSFORMATION: `exact`, `assumption`, `apply`
------------------------------------------------------------

`exact` :
  If you have `h : P` and goal `⊢ P`, then `exact h` finishes the proof.

`assumption` :
  Tries to close the goal using some hypothesis in the context.

`apply` :
  If you have `h : P → Q` and goal `⊢ Q`, `apply h` turns the goal into `⊢ P`.
-/
example (P : Prop) (h : P) : P := by
  exact h

example (P : Prop) (h : P) : P := by
  assumption

example (P Q : Prop) (h : P → Q) (p : P) : Q := by
  apply h
  exact p


/-
------------------------------------------------------------
4. BUILDING STRUCTURED OBJECTS: `constructor`, `use`
------------------------------------------------------------

`constructor` :
  Used for conjunctions (`P ∧ Q`) and other structures with multiple fields.

`use` :
  Supplies an explicit witness for existential statements (`∃ n, P n`).
-/
example (P Q : Prop) (h₁ : P) (h₂ : Q) : P ∧ Q := by
  constructor
  · exact h₁
  · exact h₂

example : ∃ n : Nat, n > 3 := by
  use 4
  -- We can discharge the inequality with `norm_num`
  simp_all

/-
------------------------------------------------------------
5. `by_cases`, `symm`, `trans`, `revert`,
   `have`, `let`
------------------------------------------------------------

`by_cases` :
  Case distinction on a proposition `P`.
-/
example (P : Prop) : P ∨ ¬ P := by
  by_cases h : P
  · left;  exact h
  · right; exact h

/-
`symm` and `trans` :
  `symm` reverses equalities; `trans` chains equalities/inequalities.
-/
example (a b c : Nat) (h₁ : a = b) (h₂ : b = c) : a = c := by
  trans b
  · exact h₁
  · exact h₂

example (a b c : ℕ) (h₁ : a < b) (h₂ : b < c) : a < c := by
  trans b
  · exact h₁
  · exact h₂

example (x y : ℚ) (h : x + 2 = y) : y = 2 + x := by
  symm
  rw [← h, add_comm]

/-

`revert` :
  Moves a hypothesis back into the goal; inverse to `intro`.
-/
example (a b : Nat) (h : a = b) : b = a := by
  revert h
  intro h'
  rw [h']

/-

`have` and `let` :

`have` :
  Introduces an intermediate fact that must be proved immediately.

`let` :
  Introduces a local definition (abbreviation).
-/
example (a b : Nat) : (a + b)^2 = a^2 + 2*a*b + b^2 := by
  have h₁ : (a + b)^2 = (a + b)*(a + b) := by ring
  rw [h₁]
  simp [Nat.add_mul]
  simp [Nat.mul_add]
  ring

/-
example (a b : Nat) (h : a = b) : b = a := by
  ring
  sorry
-/

example (a b : Nat) (h : a + b = 10) : b + a = 10 := by
  let s := a + b
  have : s = 10 := h
  -- replace goal using the local definition `s`
  rw [← this]
  -- express `s` back in terms of `a` and `b`
  simp [Nat.add_comm]
  ring

/-
`contradiction` :
  Closes the goal if there is a pair of contradictory hypotheses.
-/

example (P : Prop) (h₁ : P) (h₂ : ¬ P) : False := by
  contradiction


example (n : Nat) (h : n < 1) : n = 0 := by
  by_cases h0 : n = 0
  · exact h0
  · have hpos : 0 < n := Nat.pos_of_ne_zero h0
    have h1le : 1 ≤ n := Nat.succ_le_of_lt hpos
    have hlt : 1 < 1 := Nat.lt_of_le_of_lt h1le h
    have hnot : ¬ 1 < 1 := lt_irrefl _
    contradiction

/-
------------------------------------------------------------
6. INDUCTION EXAMPLE (NEW):
   SUM OF FIRST n ODD NUMBERS = n²
------------------------------------------------------------

We prove, by induction, the classical identity
  ∑_{i=0}^{n-1} (2i + 1) = n².

This is analogous in spirit to the Gauss sum proof from the lecture.
-/

/-
#eval range 3
#eval (∑ i ∈ range 3, ((2*i) + 1 : ℕ)) -- \ sum
#eval (Σ i ∈ range 3, ((2*i) + 1 : ℕ)) -- \ Sigma
#eval (3 ∣ 6) -- \ |
#eval (3 | 6) -- |
-/

/-- Induction proof: ∑_{i=0}^{n-1} (2i + 1) = n². -/
lemma sum_first_odds (n : ℕ) :
    (∑ i ∈ range n, (2*i + 1 : ℕ)) = n^2 := by
  induction n with
  | zero =>
      -- base case: n = 0, the sum over an empty range is 0 and 0² = 0.
      ring -- or simp or simp_all or norm_num
  | succ k ih =>
      -- inductive step: assume the statement for k, prove for k+1.
      have  :
          (∑ i ∈ range (k+1), (2*i + 1 : ℕ))
            = (∑ i ∈ range k, (2*i + 1 : ℕ)) + (2*k + 1) := by
        -- split the sum off the last term at i = k
        simp [sum_range_succ]
      calc
        (∑ i ∈ range (k+1), (2*i + 1 : ℕ))
            = (∑ i ∈ range k, (2*i + 1 : ℕ)) + (2*k + 1) := this
        _ = k^2 + (2*k + 1) := by
                -- use the inductive hypothesis
                simp [ih]
        _   = (k + 1)^2 := by ring -- purely algebraic step; `ring` handles it in ℕ

/-
------------------------------------------------------------
7. DIVISIBILITY EXAMPLE (NEW):
   A RESULT SIMILAR TO `x - 3 ∣ x^3 - 3 ↔ x - 3 ∣ 24`
------------------------------------------------------------
-/

example (x : ℤ) : ((x-3) ∣ x^3 - 3 ↔ x - 3 ∣ 24 ) := by
  have hdiv : x - 3 ∣ x^3 - 27 := by
    use x^2 + 3*x + 9
    ring
  constructor
  · intro h
    convert dvd_sub h hdiv -- convert tactic rewrites the goal using the mentioned lemma.
    ring -- simp
  · intro h
    have : x^3 - 3 = (x^3 - 27) + 24 := by ring
    rw [this]
    convert dvd_add hdiv h

/-  · intro h
    have : x^3 - 3 = (x^3 - 27) + 24 := by ring
    rw [this]
    rw [Int.add_comm]
    exact dvd_add h hdiv
-/

example (x: ℤ) : x - 1 ∣ x^2 + x + 1 ↔ x - 1 ∣ 3 := by
  have hdiv : x - 1 ∣ x^2 + x - 2 := by
    use x + 2
    ring
  constructor
  · intro h
    convert dvd_sub h hdiv
    simp
  · intro h
    have : x^2 + x + 1 = x^2 + x - 2 + 3 := by ring
    rw [this]
    exact dvd_add hdiv h

section Sets

------------------------------------------------------------
-- . SET AND MEMBERSHIP NOTATIONS
------------------------------------------------------------
/-
Lean uses:
- `∈` ("in")
- `⊆` ("subset")
- `∅` (empty set)
- `∪`, `∩` (union, intersection)

We also open the `Set` namespace so we can write `A ∪ B`, `A ∩ B`
instead of `Set.union A B`, `Set.inter A B`, etc.
-/

open Set

/-
We fix a type `α` and two subsets `A` and `B` of `α`.
Think of `α` as a "universe", i.e. universal set and `A`, `B` as subsets of `α`.
-/

variable {α : Type} (A B : Set α)

/-
Example 1: `∅ ⊆ A`.

This says "the empty set is a subset of any set `A`".
The definition of `X ⊆ Y` is `∀ x, x ∈ X → x ∈ Y`.

So we assume `x ∈ ∅` and then derive a contradiction,
because by definition nothing is in the empty set.
-/

example : ∅ ⊆ A := by
  intro x
  intro h
  contradiction

/-
Example 2: `A ∩ B ⊆ A`.

If `x ∈ A ∩ B`, then by definition we have a pair of proofs:
`hx.left : x ∈ A` and `hx.right : x ∈ B`.
We simply project the left component.
-/
theorem int1 : A ∩ B ⊆ A := by
  intro x hx
  exact hx.left

/-
Example 3: `A ⊆ A ∪ B`.

If `x ∈ A`, then `x` is certainly in the union `A ∪ B`
(by the left injection into the disjunction).
-/
theorem int2 : A ⊆ A ∪ B := by
  intro x hx
  left
  exact hx

lemma int3 : A ∩ B ⊆ A ∪ B := by
  trans A
  · apply int1
  · apply int2

lemma int4 : A ∩ B ⊆ A ∪ B := by
  intro x h
  left
  exact h.left

/-
Now we add another type `β` and a function `f : α → β`,
still working with sets `A B : Set α`.
-/
variable {α β : Type*} (A B : Set α) (f : α → β)
