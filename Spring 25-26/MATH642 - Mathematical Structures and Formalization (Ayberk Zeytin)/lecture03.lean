import Mathlib


/-
# Basic Tactics and Notations in Lean 4

This week we will talk about the simplest tactics (intro, exact, apply, rw, simp, etc.)

Each section is self-contained — you can evaluate them one by one.
-/

------------------------------------------------------------
-- 0. IMPORTS AND LOGICAL OPENINGS
------------------------------------------------------------

open Classical -- enables classical reasoning (like by_contradiction)
open Nat        -- opens natural number operations
open Function   -- allows use of ∘ (composition)

------------------------------------------------------------
-- 1. BASIC LOGICAL NOTATIONS
------------------------------------------------------------
/-
Lean supports most standard logical symbols:
- `→`  : implication  (P → Q)
- `↔`  : equivalence  (P ↔ Q)
- `¬`  : negation     (¬P)
- `∧`  : conjunction  (P ∧ Q)
- `∨`  : disjunction  (P ∨ Q)
- `∀`  : "for all"
- `∃`  : "there exists"
- `=`  : equality
- `≠`  : inequality, shorthand for ¬(a = b)
-/
example (P Q : Prop) : (P ∧ Q) → P := by -- declares an example whose type is (P ∧ Q ) → P . "by" opens tactic mode for the proof.
  intro h -- introduces the assumption h : P ∧ Q into the context.
  exact h.left -- uses the projection .left (And.left) on the conjunction h to produce the proof of P and finishes the goal.

example (P Q : Prop) : (P ∧ Q) → Q := by
  intro h
  exact h.right

example (a b : Nat) : a ≠ b → ¬(a = b) := by -- declares an example (forall a b : Nat) whose type is a ≠ b → ¬(a = b). "by" opens tactic mode for the proof.
  intro h -- moves the antecedent into the context as a hypothesis h : a ≠ b. Note: in Lean, a ≠ b is notation for ¬(a = b), i.e. (a = b) → False.
  exact h -- supplies h as the exact proof of the current goal ¬(a = b). this succeeds because the hypothesis type and the goal type are definitionally the same.


open scoped BigOperators

example : ∑ i ∈ Finset.range 4, i = 0 + 1 + 2 + 3 := by
  simp [Finset.range, Finset.sum]


/-
example (n : Nat) : ∑ i ∈ Finset.range n, i = n*(n-1)/2 := by
  simp [Finset.range, Finset.sum]

-/

example : ∑ i ∈ Finset.range 4, i^2 = 0^2 + 1^ 2 + 2^2 + 3^2:= by
  simp [Finset.range, Finset.sum]

------------------------------------------------------------
-- 2. INTRO
------------------------------------------------------------
/-
Introduces assumptions or universally quantified variables.
-/
example : ∀ n : Nat, n = n := by
  intro n
  rfl


------------------------------------------------------------
-- 3. RFL
------------------------------------------------------------
/-
`rfl` solves equalities where both sides simplify identically.
-/
example : (1 + 2) * 3 = 10 - 1 := by
  rfl

example : (1 + 2) * 3 = 10 - 1 := by
  simp

/-
example : (1 + 2) * 3 = 10 - 1 := by
  intro h
-/
------------------------------------------------------------
-- 4. EXACT
------------------------------------------------------------
example (P : Prop) (h : P) : P := by -- (3 : Nat)
  exact h


------------------------------------------------------------
-- 5. ASSUMPTION
------------------------------------------------------------
example (P : Prop) (h : P) : P := by
  assumption


------------------------------------------------------------
-- 6. APPLY
------------------------------------------------------------
example (P Q : Prop) (h1 : P → Q) (h2 : P) : Q := by
  apply h1
  assumption

example (P Q : Prop) (h1 : P → Q) (h2 : P) : Q := by
  apply h1
  exact h2

example (P Q : Prop) (h1 : P → Q) (h2 : P) : Q := by
  apply h1 h2

------------------------------------------------------------
-- 7. RW (REWRITE)
------------------------------------------------------------
example (a b : Nat) (h : a = b) : a + 1 = b + 1 := by
  rw [h]
  -- rfl
------------------------------------------------------------
-- 8. SIMP
------------------------------------------------------------
example (n : Nat) : 0 + n = n := by
  simp

example (a b : Nat) : (a + 0) + b = a + b := by
  simp


/-
example (a b : Int) : a + (b + 1) = (1 + a) + b := by
  ring
-/

------------------------------------------------------------
-- 9. CONSTRUCTOR
------------------------------------------------------------
theorem lemma_burcu  (P Q : Prop) (h₁ : P) (h₂ : Q) : P ∧ Q := by
  constructor
  · exact h₁
  · assumption

example (P Q R : Prop) (h₁ : P) (h₂ : Q) (h₃ : R ) : P ∧ Q ∧ R := by
  constructor
  · exact h₁ -- P is true
  · apply lemma_burcu (P := Q) (Q := R) h₂ h₃
    /- symm
    apply lemma_burcu (P := R) (Q := Q) h₃ h₂
    -/


example (P Q R : Prop) (h₁ : P) (h₂ : Q) (h₃ : R ) : (P ∧ Q) ∧ R := by
  constructor
  constructor
  · exact h₁
  · exact h₂
  · exact h₃

/-- Existential constructor version -/
example : ∃ n : Nat, n^2 = 9 := by
  use 3
  simp

example : ∃ n : Nat, n^2 = 9 := by
  -- 1. 'constructor' generates two goals (in this typical order):
  --    case h: ⊢ ?w ^ 2 = 9  (Active proof goal)
  --    case w: ⊢ Nat        (Witness goal)
  constructor

  -- 2. Solve the Witness Goal (w) first.
  -- We use the 'case' tactic to switch the active goal to 'w'.
  case w =>
    -- The goal is ⊢ Nat. We need to provide a term of type Nat.
    exact 3

  -- 3. The remaining active goal is now the Proof Goal (h).
  -- Note: The witness ?w is now fixed to 3. The goal is ⊢ 3^2 = 9.
  case h =>
    -- 'rfl' or 'norm_num' solves the equality by computation.
    rfl
------------------------------------------------------------
-- 10. CASES
------------------------------------------------------------

example (b : Bool) : b = true ∨ b = false := by
  cases b
  · right
    rfl
  · left
    rfl

------------------------------------------------------------
-- 11. BY_CASES
------------------------------------------------------------
/-
`by_cases` splits the proof depending on whether a proposition holds or not.
-/
example (P : Prop) : P ∨ ¬P := by
  by_cases h : P
  · left
    exact h
  · right
    exact h

/-
example (P Q : Prop) (h : P) : P ∨ Q := by
  by_cases g : Q
  · left
    assumption
  · left
    exact h
-/


------------------------------------------------------------
-- 12. SYMMETRY and TRANS
------------------------------------------------------------
example (a b c : Nat) (h₁ : a = b) (h₂ : b = c) : a = c := by
  trans b
  · exact h₁
  · exact h₂

example (a b c : ℕ ) (h1 : a<b) (h2 : b<c) : a<c := by
  trans b
  · exact h1
  · exact h2



example (x y : ℚ) (h : x + 2 = y) : y = 2 + x := by
  symm
  rw [← h]
  rw [add_comm]


example (x y : ℚ) (h : x + 2 = y) : y = 2 + x := by
  symm
  rw [Rat.add_comm]
  assumption

-- REVERT
------------------------------------------------------------
/-
The **`revert`** tactic moves a hypothesis from the local context back into the goal.
This changes the goal type from `T` to `H₁ → ... → Hₙ → T`, where `Hᵢ` are the types of the reverted hypotheses.
It is the inverse of `intro` or `assume`. It's often used to prepare the goal for
an application of a theorem whose statement is an implication, or to change the order
of quantified variables in the goal.
-/
example (a b : Nat) (h : a = b) : b = a := by
  -- Goal: b = a (with hypothesis h : a = b)
  revert h
  -- New Goal: a = b → b = a
  intro h'
  -- New Goal: b = a (with hypothesis h' : a = b)
  rw [h']

  -- exact Eq.symm h' -- Proves the goal using symmetry


------------------------------------------------------------
-- 13. HAVE and LET
------------------------------------------------------------
/-
The **`have`** tactic is used to introduce an intermediate statement (a new
propositional or type-theoretic hypothesis) into the local context.
The statement introduced by `have` must be proven in the immediate following goal.
This breaks down a proof into smaller, verifiable steps.

The **`let`** tactic defines a local term or abbreviation. Unlike `have`, `let`
introduces a new definition (a term) rather than a proposition that needs a proof.
It is primarily used for **simplifying expressions** or **giving names** to complex terms.
The defined term is immediately available for use.
-/
example (a b : Nat) : (a + b)^2 = a^2 + 2*a*b + b^2 := by
  -- Use `have` to introduce an intermediate equality proof.
  have h₁ : (a + b)^2 = (a + b)*(a + b) := by ring -- Proof required for h₁
  -- Now h₁ is available as a hypothesis.
  rw [h₁]
  -- Use `let` (implicitly, if needed for complex terms) or simpler tactics.
  simp [Nat.add_mul, Nat.mul_add]
  ring -- requires Mathlib tactic (optional)


example (a b : Nat) (h : a + b = 10) : b + a = 10 := by
  -- Introduce a temporary name using `let`
  let sum := a + b
  -- Now `sum` is available as a local definition
  have : sum = 10 := by exact h --we didn’t give it a name, Lean automatically names it `this`. So `this` is just a placeholder for the unnamed hypothesis (sum = 10).
  -- Rewrite using `sum`
  rw [←this]
  -- Replace `sum` back with `b + a`
  rw [Nat.add_comm]

------------------------------------------------------------
-- 14. CONTRADICTION
------------------------------------------------------------
/-
The **`contradiction`** tactic attempts to close the goal (which must be `False` or an
equivalent proposition) by finding a pair of contradictory hypotheses in the local context,
typically of the form `P` and `¬P` (or `P` and `P → False`).
It can also be used to derive `False` from hypotheses that are mutually exclusive (e.g., `x > 0` and `x < 0`).
-/
example (P : Prop) (h₁ : P) (h₂ : ¬P) : False := by
  contradiction -- Closes the goal by finding h₁ : P and h₂ : ¬P

-- import Std.Tactic -- or import Mathlib.Tactic

example (n : Nat) (h : n < 1) : n = 0 := by
  by_cases h0 : n = 0
  · exact h0
  · have hpos : 0 < n := Nat.pos_of_ne_zero h0
    have h1le : 1 ≤ n := Nat.succ_le_of_lt hpos
    have hlt : 1 < 1 := Nat.lt_of_le_of_lt h1le h
    -- have hltnot : ¬ 1 < 1 := lt_irrefl 1
    contradiction

example (n : Nat) (h : n < 1) : n = 0 := by
  by_cases h0 : n = 0
  · exact h0
  · have h1 : n ≤ 0 := Nat.le_of_lt_succ h
    have h_cont : n > 0 := Nat.pos_iff_ne_zero.mpr h0
    have h_contra : n < n := Nat.lt_of_le_of_lt h1 h_cont
    have h_false : ¬ n < n := Nat.lt_irrefl n
    contradiction
