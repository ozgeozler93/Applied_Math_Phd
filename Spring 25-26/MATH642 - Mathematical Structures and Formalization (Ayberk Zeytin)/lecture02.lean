
/-
Lean 4 — Lecture 1 Recap
This file recalls the most important ideas from the first lecture: evaluating and checking
expressions, precedence and application, basic types, conditionals, definitions (named and
anonymous), let‑bindings, and simple structures.
-/

/-
#eval runs code and shows a result.
#check asks Lean for the type of an expression/identifier.
-/
#eval 2 + 6
#eval 3 * 8
#eval 7 - 4
#eval 10 / 2
#eval 10 % 3
#eval 2 ^ 5

#check 42          -- : Nat (default numeric literal type here)
#check (42 : Int)  -- explicit type ascription
#check (3.14 : Float)
#check true
#check "Lean"

#eval 7 - 12
#eval (7 : Int) - 12

#check (7 : Int)

/-
Function application binds tighter than infix operators.
Application is left‑associative: f a b c ≡ (((f a) b) c).
Use parentheses to group nested applications.
-/
#eval String.append "great " (String.append "oak " "tree") -- Python equivalent of this statement is print("great","oak","tree")
-- without parentheses the inner call would be parsed as an argument, which is wrong.

#eval 2 + 3 * 4       -- 14
#eval (2 + 3) * 4     -- 20 (parentheses change grouping)

/-
if ... then ... else ... has a value.
The two branches must have the same type.
-/
#eval (if 5 % 2 == 0 then "even" else "odd")
#eval (if 2 + 2 == 4 then 1 else 0)     -- type: Nat, both branches Nat

/-
Binding expressions are usually introduced with let or def.
let x := e; ... uses x in the scope that follows.
-/
#eval (let x := 5; let y := x + 2; y * y)  -- (5+2)^2 = 49

/-
def introduces a (possibly typed) constant or function. In Lean, functions are defined using the def keyword, just like other definitions. The syntax is:
def name (arg1 : Type1) (arg2 : Type2) ... : ReturnType := expr
-/

def addThree (x : Int) : Int := x + 3
#check addThree

#eval addThree 7

def EO (x: Int) : String :=
  if x % 2 == 0 then "even" else "odd"

#check EO

#eval EO 42
#eval EO 55
#eval EO (addThree 10)

def isEven (x : Int) : Bool := x % 2 == 0
#eval isEven 42
#eval isEven 55


-- curried function (two arguments), written with arrows
--   Int → Int → Int  means  Int → (Int → Int)

def add_prime (x : Int) (y : Int) : Int := x + y

#check add_prime
#check (add_prime 5)

def add : Int → Int → Int := fun a b => a + b -- This is a function that takes two Ints and returns their sum.
#check add
#check add 2
#eval add 2 5

def isOdd : Int → Bool := fun x => x % 2 != 0
#eval isOdd 42
#eval isOdd 55

/-A polymorphic function is a function that can operate on arguments of various types. In Lean, we can define polymorphic functions using type parameters. These type parameters are specified within curly braces {} in the function definition. This allows the function to be used with different types without needing to define separate functions for each type.
-/


-- polymorphic identity function


def myId {α : Type} (x : α) : α := x -- This func
#check myId              -- {α : Type} → α → α
#check myId 3            -- α := Nat;  result has type Nat
#check myId "hello"      -- α := String; result has type String


-- Defining a polymorphic constant function
-- It takes an argument of type A, a second argument of type B, and ignores the second one,
-- always returning the first argument (type A).
def const (A : Type) (B : Type) (x : A) (y : B) : A := x

-- Examples using the requested types:

-- x is Nat, y is Bool (A = Nat, B = Bool)
#eval const Nat Bool 5 true    -- 5 : Nat

-- x is Int, y is Float (A = Int, B = Float)
#eval const Int Float (-10) 3.14  -- -10 : Int

-- x is Bool, y is Nat (A = Bool, B = Nat)
#eval const Bool Nat false 100    -- false : Bool

-- polymorphic constant function : this function is like const above, but with implicit type parameters. The types α and β are inferred from the arguments. It takes an argument of type α, a second argument of type β, and ignores the second one, always returning the first argument (type α).

def myConst {α β : Type} (x : α) (y : β) : α := x
#check myConst           -- {α β : Type} → α → β → α
#check myConst 3 "hi"    -- α := Nat, β := String; result has type Nat


/-
Structures (records) and field access
Define a structure with named fields; create values with `{ field := value, … }`.
Access fields with dot notation.
-/
structure Point where
  x : Float
  y : Float
  z : Float := 0 -- default value for z
  deriving Repr

def p1 : Point := { x := 3, y := 4, z := 12 } -- p is a Point with x=3, y=4 and z = 12
#check p1
#check p1.x
#check p1.z
#eval p1.x + p1.y + p1.z
def p2 : Point := { x := 7, y := 8 } -- p2 is a Point with x=7, y=8 and z = 0 (default value)
#eval p2.x + p2.y + p2.z
#eval p2.z

#check Float.ofInt

def distance (p : Point) (q : Point) : Float :=
  Float.sqrt (((p.x - q.x) ^ 2 + (p.y - q.y) ^ 2 + (p.z - q.z) ^ 2))

#eval distance p1 p2

def dot_product (p : Point) (q : Point) : Float :=
  (p.x * q.x + p.y * q.y + p.z * q.z)

#eval dot_product p1 p2
#eval dot_product p1 p1
#eval dot_product p1 p2 / dot_product p1 p1

def origin : Point := { x := 0.0 , y := 0.0 , z := 0.0 }

def scalar_product (a : Float) (p : Point) : Point :=
  { x := a * p.x,
    y := a * p.y,
    z := a * p.z }

def projection (p : Point) (q : Point) : Point :=
  scalar_product ((dot_product p q) / (dot_product q q)) q -- This is the projection of p onto q, calculated using the formula: proj_q(p) = (p · q / q · q) * q

#eval projection p1 p2

/- # Inductive Data Types -/

/-
Structures (product types) are good for bundling fixed collections of fields. But many domain concepts involve choice (“this value is one of several forms”) or recursion (nesting).

For example, a syntax tree for arithmetic expressions: an addition node might have two children which themselves are expressions.

Inductive datatypes (also called sum types or variant / algebraic datatypes) let you define a type by listing constructors, each possibly carrying data. Combined with recursion, you get very powerful expressive types.

Many of Lean’s built-in types (e.g. Bool, Nat, ) are inductive in the standard library. For instance, Bool has two constructors: true and false.
inductive Bool where
  | true : Bool
  | false : Bool
This definition has two constructors, true and false, each of which takes no arguments and returns a value of type Bool.

Here is an example :
-/
inductive Color where
  | red : Color
  | green : Color
  | blue : Color
  deriving Repr
/- Here we defined an inductive type named Color with three constructors: red, green, and blue. Each constructor takes no arguments and returns a value of type Color.
-/
def favoriteColor : Color := Color.blue

#check favoriteColor
#eval favoriteColor  -- this function prints "blue" because favoriteColor is of type Color

def color (x: Int) : Color :=
  if x % 3 == 0 then Color.red
  else if x % 3 == 1 then Color.green
  else Color.blue

#eval color 7
#eval color 8
#eval color 9


inductive Son where
  | zero : Son
  | one  : Son
  | two  : Son
  | three : Son
  | four : Son
  deriving Repr
#check Son
#eval Son.one

def addSon (x : Son) (y : Son) : Son :=
  match x, y with
  | Son.zero, _       => y
  | _, Son.zero       => x
  | Son.one, Son.one  => Son.two
  | Son.one, Son.two  => Son.three
  | Son.one, Son.three => Son.four
  | Son.two, Son.one  => Son.three
  | Son.two, Son.two  => Son.four
  | Son.three, Son.one  => Son.four
  | Son.four, _      => Son.four
  | _, Son.four      => Son.four
  | _, _              => Son.four -- default case to handle any other combinations

#eval addSon Son.three Son.two
#eval addSon Son.one Son.two
#check addSon -- This is a binary function.
#check addSon Son.one -- This is a unary function.


def fib : Nat → Nat
| 0 => 1
| 1 => 1
| Nat.succ (Nat.succ n) => fib (Nat.succ n) + fib n -- recursive case for n >= 2. Here, Nat.succ n represents n + 1, so Nat.succ (Nat.succ n) represents n + 2.

#eval fib 0
#eval fib 1
#eval fib 2
#eval fib 3
#eval fib 4
#eval fib 5
#eval fib 6
#eval fib 7
#eval fib 8
#eval fib 9

def fibo : Nat → Nat
| 0 => 1
| 1 => 1
| n+2 => fibo (n+1) + fibo n -- recursive case for n >= 2

#eval fibo 0
#eval fibo 1
#eval fibo 2
#eval fibo 3
#eval fibo 4
#eval fibo 5


-- Defining the 'Fin n' type conceptually in Lean
-- Note: Lean's standard library uses a more optimized
-- definition (a subtype of Nat), but this demonstrates
-- the inductive principle clearly.

/--
  The type Sonlu n represents the set of natural numbers
  {0, 1, ..., n-1}. It is an indexed family of types.
-/

inductive Sonlu : Nat → Type
  -- Base Case: 'zero' is the first element, valid in any Sonlu (n+1) where n >= 0
  | zero : ∀ (n : Nat), Sonlu (n + 1) -- this means that for any natural number n, we can create an element of type Sonlu (n + 1) by applying the zero constructor to n.
  -- Inductive Step: If we have an element 'k' in Fin n,
  -- we can form its successor in the larger set Fin (n + 1).
  -- This represents k+1.
  -- The successor constructor takes an element of type Sonlu n and returns an element of type Sonlu (n + 1).
  | succ : ∀ {n : Nat}, Sonlu n → Sonlu (n + 1) -- this means that if we have an element of type Sonlu n, we can create an element of type Sonlu (n + 1) by applying the succ constructor to it.
  deriving Repr

-- Demonstrating terms in Fin 3, which is the set {0, 1, 2}

#check Sonlu 7
#check Sonlu.zero 6
/-- The element 0 in Fin 3 -/
def son3_zero : Sonlu 3 :=
  Sonlu.zero 2 -- 3 is 2 + 1, so the index is 2
#check son3_zero -- son3_zero : Sonlu 3
#eval son3_zero  -- this function prints "zero 2" because son3_zero is of type Sonlu 3
#check Sonlu.zero
#eval Sonlu.zero 1 -- this function prints "zero 1" because Sonlu.zero 1 is of type  Sonlu 2
#eval Son.four
#eval Color.blue
#eval Sonlu.succ (Sonlu.zero 1)
/-- The element 1 in Fin 3 -/
def son3_one : Sonlu 3 :=
  Sonlu.succ (Sonlu.zero 1) -- 'one' in Fin 2, then lifted to Fin 3

/-- The element 2 in Fin 3 -/
def son3_two : Sonlu 3 :=
  Sonlu.succ (Sonlu.succ (Sonlu.zero 0)) -- 'two' in Fin 3, built from 'one' in Fin 2

-- Proving a simple property by pattern matching (structural recursion)
-- A function to convert a Fin n element to a Nat
def to_nat : ∀ {n : Nat}, Sonlu n → Nat
  | _, Sonlu.zero _ => 0  -- base case: zero maps to 0
  | _, Sonlu.succ k => 1 + to_nat k -- recursively convert the predecessor and add 1

-- Example of using the function
#check to_nat son3_two -- to_nat fin3_two : Nat
#eval to_nat son3_two  -- 2
