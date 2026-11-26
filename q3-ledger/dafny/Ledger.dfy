// Assumption ledger, JTMS core. See ../spec.md.
// Proves: each operation preserves Inv (believed = derivable from enabled),
// hence I1 live support and I2 closure under retraction.

datatype Just = Just(ants: set<nat>, c: nat)
datatype Op = Assert(a: nat) | Justify(j: Just) | Retract(a: nat)
datatype Ledger = Ledger(enabled: set<nat>, J: set<Just>, believed: set<nat>, log: seq<Op>)

// ---------- Reference semantics ----------

ghost predicate Closed(S: set<nat>, J: set<Just>) {
  forall j :: j in J && j.ants <= S ==> j.c in S
}

// n is in the least closed superset of E.
ghost predicate InCl(n: nat, E: set<nat>, J: set<Just>) {
  forall S: set<nat> :: E <= S && Closed(S, J) ==> n in S
}

lemma InClBase(n: nat, E: set<nat>, J: set<Just>)
  requires n in E
  ensures InCl(n, E, J)
{}

lemma InClStep(j: Just, E: set<nat>, J: set<Just>)
  requires j in J
  requires forall x :: x in j.ants ==> InCl(x, E, J)
  ensures InCl(j.c, E, J)
{
  forall S: set<nat> | E <= S && Closed(S, J) ensures j.c in S {
    assert j.ants <= S;
  }
}

lemma InClMono(n: nat, E: set<nat>, E2: set<nat>, J: set<Just>, J2: set<Just>)
  requires InCl(n, E, J) && E <= E2 && J <= J2
  ensures InCl(n, E2, J2)
{
  forall S: set<nat> | E2 <= S && Closed(S, J2) ensures n in S {
    assert Closed(S, J);
  }
}

// ---------- Forward closure, computed ----------

function Conses(J: set<Just>): set<nat> { set j | j in J :: j.c }

method Close(J: set<Just>, ghost E: set<nat>, S0: set<nat>) returns (S: set<nat>)
  requires E <= S0
  requires forall n :: n in S0 ==> InCl(n, E, J)
  ensures forall n :: n in S <==> InCl(n, E, J)
{
  S := S0;
  ghost var U := S0 + Conses(J);
  while exists j :: j in J && j.ants <= S && j.c !in S
    invariant S0 <= S <= U
    invariant forall n :: n in S ==> InCl(n, E, J)
    decreases |U - S|
  {
    var j :| j in J && j.ants <= S && j.c !in S;
    InClStep(j, E, J);
    assert U - (S + {j.c}) < U - S;
    S := S + {j.c};
  }
  assert Closed(S, J);
}

// ---------- Downstream set ----------

function Edges(J: set<Just>): set<Just> {
  set j, x | j in J && x in j.ants :: Just({x}, j.c)
}

ghost predicate FwdClosed(D: set<nat>, J: set<Just>) {
  forall j, x :: j in J && x in j.ants && x in D ==> j.c in D
}

method Down(J: set<Just>, a: nat) returns (D: set<nat>)
  ensures a in D
  ensures FwdClosed(D, J)
{
  D := Close(Edges(J), {a}, {a});
  assert InCl(a, {a}, Edges(J));
  forall j, x | j in J && x in j.ants && x in D ensures j.c in D {
    var e := Just({x}, j.c);
    assert e in Edges(J);
    InClStep(e, {a}, Edges(J));
  }
}

// A derivation of n that leaves the downstream set of a never used a.
lemma Avoid(n: nat, E: set<nat>, J: set<Just>, a: nat, D: set<nat>)
  requires InCl(n, E, J) && n !in D && a in D && FwdClosed(D, J)
  ensures InCl(n, E - {a}, J)
{
  forall T: set<nat> | E - {a} <= T && Closed(T, J) ensures n in T {
    var T2 := T + D;
    forall j | j in J && j.ants <= T2 ensures j.c in T2 {
      if exists x :: x in j.ants && x in D {
        var x :| x in j.ants && x in D;
      } else {
        assert j.ants <= T;
      }
    }
    assert Closed(T2, J);
    assert E <= T2;
  }
}

// ---------- Ledger ----------

ghost predicate Inv(s: Ledger) {
  forall n :: n in s.believed <==> InCl(n, s.enabled, s.J)
}

method DoAssert(s: Ledger, a: nat) returns (t: Ledger)
  requires Inv(s)
  ensures Inv(t) && t.enabled == s.enabled + {a} && t.J == s.J && t.log == s.log + [Assert(a)]
{
  var E := s.enabled + {a};
  forall n | n in s.believed + {a} ensures InCl(n, E, s.J) {
    if n in s.believed { InClMono(n, s.enabled, E, s.J, s.J); }
  }
  var b := Close(s.J, E, s.believed + {a});
  t := Ledger(E, s.J, b, s.log + [Assert(a)]);
}

method DoJustify(s: Ledger, j: Just) returns (t: Ledger)
  requires Inv(s)
  ensures Inv(t) && t.enabled == s.enabled && t.J == s.J + {j} && t.log == s.log + [Justify(j)]
{
  var J2 := s.J + {j};
  forall n | n in s.believed ensures InCl(n, s.enabled, J2) {
    InClMono(n, s.enabled, s.enabled, s.J, J2);
  }
  var b := Close(J2, s.enabled, s.believed);
  t := Ledger(s.enabled, J2, b, s.log + [Justify(j)]);
}

method DoRetract(s: Ledger, a: nat) returns (t: Ledger)
  requires Inv(s)
  ensures Inv(t) && t.enabled == s.enabled - {a} && t.J == s.J && t.log == s.log + [Retract(a)]
{
  var en := s.enabled - {a};
  var D := Down(s.J, a);
  var seed := (s.believed - D) + en;
  forall n | n in seed ensures InCl(n, en, s.J) {
    if n in s.believed - D { Avoid(n, s.enabled, s.J, a, D); }
  }
  var b := Close(s.J, en, seed);
  t := Ledger(en, s.J, b, s.log + [Retract(a)]);
}

function Query(s: Ledger, n: nat): bool { n in s.believed }

method Apply(s: Ledger, op: Op) returns (t: Ledger)
  requires Inv(s)
  ensures Inv(t) && t.log == s.log + [op]
{
  match op
  case Assert(a) => t := DoAssert(s, a);
  case Justify(j) => t := DoJustify(s, j);
  case Retract(a) => t := DoRetract(s, a);
}

method Run(ops: seq<Op>) returns (s: Ledger)
  ensures Inv(s) && s.log == ops
{
  s := Ledger({}, {}, {}, []);
  assert forall n :: !InCl(n, {}, {}) by {
    forall n ensures !InCl(n, {}, {}) { assert Closed({}, {}); }
  }
  var i := 0;
  while i < |ops|
    invariant 0 <= i <= |ops|
    invariant Inv(s) && s.log == ops[..i]
  {
    s := Apply(s, ops[i]);
    assert ops[..i+1] == ops[..i] + [ops[i]];
    i := i + 1;
  }
  assert ops[..|ops|] == ops;
}

// ---------- The invariants from spec.md ----------

// I1: no belief without a live support set.
lemma LiveSupport(s: Ledger, n: nat)
  requires Inv(s) && Query(s, n)
  ensures InCl(n, s.enabled, s.J)
{}

// I3: everything derivable from the enabled assumptions is believed.
lemma Complete(s: Ledger, n: nat)
  requires Inv(s) && InCl(n, s.enabled, s.J)
  ensures Query(s, n)
{}

// I2: after retracting a, a node with no derivation avoiding a is not believed.
method RetractClosure(s: Ledger, a: nat) returns (t: Ledger)
  requires Inv(s)
  ensures forall n :: !InCl(n, s.enabled - {a}, s.J) ==> !Query(t, n)
{
  t := DoRetract(s, a);
}

// ---------- Control: naive retraction's acceptance condition ----------

// Doyle-style support without well-foundedness: every non-enabled node has a
// justification whose antecedents are all in S.
ghost predicate LocallySupported(S: set<nat>, en: set<nat>, J: set<Just>) {
  forall n :: n in S ==> n in en || exists j :: j in J && j.c == n && j.ants <= S
}
