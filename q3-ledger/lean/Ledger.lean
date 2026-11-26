/-
Assumption ledger, JTMS core. See ../spec.md.
Proves: every operation preserves `LInv` (believed = derivable from enabled assumptions),
hence I1 live support and I2 closure under retraction. Also proves that the naive
(Doyle, non-well-founded) retraction violates I1 on a concrete ledger.
-/

abbrev Node := Nat

structure Just where
  ants : List Node
  c : Node
deriving DecidableEq, Repr

/-- Reference semantics: well-founded derivation of `n` from assumptions `E`. -/
inductive Derives (J : List Just) (E : Node → Prop) : Node → Prop
  | base {n} : E n → Derives J E n
  | step {j} : j ∈ J → (∀ x ∈ j.ants, Derives J E x) → Derives J E j.c

theorem Derives.mono {J J' : List Just} {E E' : Node → Prop}
    (hJ : ∀ j ∈ J, j ∈ J') (hE : ∀ n, E n → E' n) {n} (h : Derives J E n) :
    Derives J' E' n := by
  induction h with
  | base h => exact .base (hE _ h)
  | step hj _ ih => exact .step (hJ _ hj) ih

/-! ## Forward closure, computed -/

def fires (S : List Node) (j : Just) : Bool :=
  j.ants.all (fun x => decide (x ∈ S)) && !decide (j.c ∈ S)

theorem filter_le {α} (l : List α) (p q : α → Bool) (h : ∀ x, q x = true → p x = true) :
    (l.filter q).length ≤ (l.filter p).length := by
  induction l with
  | nil => simp
  | cons y ys ih =>
    simp only [List.filter_cons]
    cases hq : q y <;> cases hp : p y <;> simp_all <;> omega

theorem filter_lt {α} (l : List α) (p q : α → Bool) (h : ∀ x, q x = true → p x = true)
    (x : α) (hx : x ∈ l) (hp : p x = true) (hq : q x = false) :
    (l.filter q).length < (l.filter p).length := by
  induction l with
  | nil => simp at hx
  | cons y ys ih =>
    have hle := filter_le ys p q h
    simp only [List.filter_cons]
    rcases List.mem_cons.mp hx with rfl | hx'
    · simp [hp, hq]; omega
    · have := ih hx'
      cases hq' : q y <;> cases hp' : p y <;> simp_all <;> omega

def close (J : List Just) (S : List Node) : List Node :=
  match h : J.find? (fires S) with
  | some j => close J (j.c :: S)
  | none => S
termination_by (J.filter (fun j => !decide (j.c ∈ S))).length
decreasing_by
  have hmem := List.mem_of_find?_eq_some h
  have hf := List.find?_some h
  simp [fires] at hf
  apply filter_lt J _ _ _ j hmem
  · simp [hf.2]
  · simp
  · intro x hx; simp at hx ⊢; exact hx.2

theorem close_sup (J : List Just) (S : List Node) : ∀ x ∈ S, x ∈ close J S := by
  fun_induction close J S with
  | case1 S j h ih => intro x hx; exact ih x (List.mem_cons_of_mem _ hx)
  | case2 S h => intro x hx; exact hx

theorem close_closed (J : List Just) (S : List Node) :
    ∀ j ∈ J, (∀ x ∈ j.ants, x ∈ close J S) → j.c ∈ close J S := by
  fun_induction close J S with
  | case1 S j h ih => exact ih
  | case2 S h =>
    intro j hj hants
    have := List.find?_eq_none.mp h j hj
    simp [fires] at this
    exact Classical.byContradiction fun hc => hc (this hants)

theorem close_least (J : List Just) (S : List Node) (T : Node → Prop)
    (hT : ∀ j ∈ J, (∀ x ∈ j.ants, T x) → T j.c) (hS : ∀ x ∈ S, T x) :
    ∀ x ∈ close J S, T x := by
  fun_induction close J S with
  | case1 S j h ih =>
    apply ih
    intro x hx
    rcases List.mem_cons.mp hx with rfl | hx
    · have hf := List.find?_some h
      simp [fires] at hf
      exact hT _ (List.mem_of_find?_eq_some h) (fun y hy => hS y (hf.1 y hy))
    · exact hS x hx
  | case2 S h => exact hS

/-- Seed lemma: closing any seed between `E` and `Cl(E)` yields exactly `Cl(E)`. -/
theorem close_eq (J : List Just) (E : Node → Prop) (S : List Node)
    (hE : ∀ n, E n → n ∈ S) (hS : ∀ n ∈ S, Derives J E n) :
    ∀ n, n ∈ close J S ↔ Derives J E n := by
  intro n
  constructor
  · exact close_least J S (Derives J E) (fun _ hj h => .step hj h) hS n
  · intro h
    induction h with
    | base h => exact close_sup J S _ (hE _ h)
    | step hj _ ih => exact close_closed J S _ hj ih

/-! ## Downstream set of an assumption -/

def edges (J : List Just) : List Just :=
  J.flatMap (fun j => j.ants.map (fun x => ⟨[x], j.c⟩))

def down (J : List Just) (a : Node) : List Node := close (edges J) [a]

theorem down_closed (J : List Just) (a : Node) :
    ∀ j ∈ J, ∀ x ∈ j.ants, x ∈ down J a → j.c ∈ down J a := by
  intro j hj x hx hd
  have : (⟨[x], j.c⟩ : Just) ∈ edges J := by
    simp only [edges, List.mem_flatMap, List.mem_map]
    exact ⟨j, hj, x, hx, rfl⟩
  exact close_closed (edges J) [a] ⟨[x], j.c⟩ this
    (by intro y hy; simp at hy; subst hy; exact hd)

theorem a_mem_down (J : List Just) (a : Node) : a ∈ down J a :=
  close_sup _ _ a (List.mem_singleton_self a)

/-- A belief outside `down a` never used `a`. -/
theorem derives_avoid (J : List Just) (E : Node → Prop) (a : Node) {n}
    (h : Derives J E n) (hn : n ∉ down J a) : Derives J (fun m => E m ∧ m ≠ a) n := by
  induction h with
  | base h =>
    refine .base ⟨h, ?_⟩
    rintro rfl; exact hn (a_mem_down J _)
  | step hj _ ih =>
    refine .step hj (fun x hx => ih x hx ?_)
    intro hxd; exact hn (down_closed J a _ hj x hx hxd)

/-! ## Ledger -/

inductive Op
  | assert (a : Node)
  | justify (j : Just)
  | retract (a : Node)
deriving DecidableEq, Repr

structure Ledger where
  enabled : List Node
  J : List Just
  believed : List Node
  log : List Op

def Ledger.init : Ledger := ⟨[], [], [], []⟩

def Ledger.assert (s : Ledger) (a : Node) : Ledger :=
  { s with enabled := a :: s.enabled, believed := close s.J (a :: s.believed),
           log := s.log ++ [.assert a] }

def Ledger.justify (s : Ledger) (j : Just) : Ledger :=
  { s with J := j :: s.J, believed := close (j :: s.J) s.believed,
           log := s.log ++ [.justify j] }

def Ledger.retract (s : Ledger) (a : Node) : Ledger :=
  let en := s.enabled.filter (· ≠ a)
  let D := down s.J a
  { s with enabled := en, believed := close s.J (s.believed.filter (· ∉ D) ++ en),
           log := s.log ++ [.retract a] }

def Ledger.apply (s : Ledger) : Op → Ledger
  | .assert a => s.assert a
  | .justify j => s.justify j
  | .retract a => s.retract a

def Ledger.query (s : Ledger) (n : Node) : Bool := decide (n ∈ s.believed)

/-- Belief is exactly derivability from the enabled assumptions. -/
def LInv (s : Ledger) : Prop := ∀ n, n ∈ s.believed ↔ Derives s.J (· ∈ s.enabled) n

theorem linv_init : LInv Ledger.init := by
  intro n; constructor
  · intro h; simp [Ledger.init] at h
  · intro h; induction h with
    | base h => simp [Ledger.init] at h
    | step hj => simp [Ledger.init] at hj

theorem linv_assert (s : Ledger) (a : Node) (h : LInv s) : LInv (s.assert a) := by
  apply close_eq
  · intro n hn
    rcases List.mem_cons.mp hn with rfl | hn
    · exact List.mem_cons_self
    · exact List.mem_cons_of_mem _ ((h n).mpr (.base hn))
  · intro n hn
    rcases List.mem_cons.mp hn with rfl | hn
    · exact .base List.mem_cons_self
    · exact ((h n).mp hn).mono (fun _ h => h) (fun _ h => List.mem_cons_of_mem _ h)

theorem linv_justify (s : Ledger) (j : Just) (h : LInv s) : LInv (s.justify j) := by
  apply close_eq
  · intro n hn; exact (h n).mpr (.base hn)
  · intro n hn; exact ((h n).mp hn).mono (fun _ h => List.mem_cons_of_mem _ h) (fun _ h => h)

theorem linv_retract (s : Ledger) (a : Node) (h : LInv s) : LInv (s.retract a) := by
  apply close_eq
  · intro n hn; exact List.mem_append_right _ hn
  · intro n hn
    rcases List.mem_append.mp hn with hn | hn
    · simp only [List.mem_filter, decide_eq_true_eq] at hn
      have := derives_avoid s.J _ a ((h n).mp hn.1) hn.2
      exact this.mono (fun _ h => h) (fun m hm => by simp [Ledger.retract, hm.1, hm.2])
    · exact .base hn

theorem linv_apply (s : Ledger) (op : Op) (h : LInv s) : LInv (s.apply op) := by
  cases op with
  | assert a => exact linv_assert s a h
  | justify j => exact linv_justify s j h
  | retract a => exact linv_retract s a h

def Ledger.run (ops : List Op) : Ledger := ops.foldl Ledger.apply Ledger.init

theorem linv_run (ops : List Op) : LInv (Ledger.run ops) := by
  unfold Ledger.run
  suffices ∀ s, LInv s → LInv (ops.foldl Ledger.apply s) from this _ linv_init
  induction ops with
  | nil => intro s h; exact h
  | cons op ops ih => intro s h; exact ih _ (linv_apply s op h)

/-! ## The invariants from spec.md -/

/-- I1: no belief without a live support set. -/
theorem live_support (ops : List Op) (n : Node) (h : (Ledger.run ops).query n = true) :
    Derives (Ledger.run ops).J (· ∈ (Ledger.run ops).enabled) n :=
  (linv_run ops n).mp (by simpa [Ledger.query] using h)

/-- I3: every node derivable from the enabled assumptions is believed. -/
theorem complete (ops : List Op) (n : Node)
    (h : Derives (Ledger.run ops).J (· ∈ (Ledger.run ops).enabled) n) :
    (Ledger.run ops).query n = true := by
  simpa [Ledger.query] using (linv_run ops n).mpr h

/-- I2: after retracting `a`, a node with no derivation avoiding `a` is not believed. -/
theorem closure_under_retraction (ops : List Op) (a n : Node)
    (h : ¬ Derives (Ledger.run ops).J (fun m => m ∈ (Ledger.run ops).enabled ∧ m ≠ a) n) :
    ((Ledger.run ops).retract a).query n = false := by
  have hi := linv_retract _ a (linv_run ops) n
  have hnb : ¬ n ∈ ((Ledger.run ops).retract a).believed := by
    intro hb
    apply h
    exact (hi.mp hb).mono (fun _ h => h) (fun m hm => by simpa [Ledger.retract] using hm)
  simpa [Ledger.query] using hnb

/-- H1: the log only grows, by exactly the applied operation. -/
theorem log_append (s : Ledger) (op : Op) : (s.apply op).log = s.log ++ [op] := by
  cases op <;> rfl

/-! ## Control: naive retraction (Doyle without well-founded support) -/

/-- Drop non-enabled nodes with no justification whose antecedents are all believed. -/
def unsupportStep (J : List Just) (en S : List Node) : List Node :=
  S.filter (fun n => decide (n ∈ en) ||
    J.any (fun j => decide (j.c = n) && j.ants.all (fun x => decide (x ∈ S))))

def naiveRetract (s : Ledger) (a : Node) : Ledger :=
  let en := s.enabled.filter (· ≠ a)
  { s with enabled := en,
           believed := close s.J ((List.range (s.believed.length + 1)).foldl
                         (fun S _ => unsupportStep s.J en S) (s.believed.filter (· ≠ a))) }

def A : Node := 0
def X : Node := 2
def Y : Node := 3

/-- x ← a, x ← y, y ← x, then assert a: x and y support each other. -/
def cycleLedger : Ledger :=
  Ledger.run [.justify ⟨[A], X⟩, .justify ⟨[Y], X⟩, .justify ⟨[X], Y⟩, .assert A]

theorem no_derivation_from_nothing (J : List Just) (hJ : ∀ j ∈ J, j.ants ≠ []) (n : Node)
    (h : Derives J (fun _ => False) n) : False := by
  induction h with
  | base h => exact h
  | step hj _ ih =>
    rename_i j _
    match hl : j.ants, hJ j hj with
    | x :: _, _ => exact ih x (by simp [hl])

theorem naive_violates_live_support :
    X ∈ (naiveRetract cycleLedger A).believed ∧
    ¬ Derives (naiveRetract cycleLedger A).J (· ∈ (naiveRetract cycleLedger A).enabled) X := by
  refine ⟨by native_decide, ?_⟩
  intro h
  have hen : (naiveRetract cycleLedger A).enabled = [] := by native_decide
  rw [hen] at h
  exact no_derivation_from_nothing _ (by decide) _ (h.mono (fun _ h => h) (fun _ h => by simp at h))

/-! ## Control: retraction that forgets to re-seed enabled assumptions -/

def noseedRetract (s : Ledger) (a : Node) : Ledger :=
  let en := s.enabled.filter (· ≠ a)
  { s with enabled := en, believed := close s.J (s.believed.filter (· ∉ down s.J a)) }

def B : Node := 1

/-- b ← a, both asserted. -/
def seedLedger : Ledger := Ledger.run [.justify ⟨[A], B⟩, .assert A, .assert B]

theorem noseed_violates_complete :
    B ∉ (noseedRetract seedLedger A).believed ∧
    Derives (noseedRetract seedLedger A).J (· ∈ (noseedRetract seedLedger A).enabled) B :=
  ⟨by native_decide, .base (by native_decide)⟩

#print axioms live_support
#print axioms closure_under_retraction
#print axioms complete
#print axioms naive_violates_live_support
#print axioms noseed_violates_complete
