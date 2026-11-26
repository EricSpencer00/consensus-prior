------------------------------- MODULE Ledger -------------------------------
(* Assumption ledger: JTMS belief set plus ATMS labels, with retraction.   *)
(* See ../spec.md for invariant IDs.                                        *)
EXTENDS FiniteSets, Sequences, Naturals

CONSTANTS
    \* @type: Str;
    Mode,     \* "correct" | "naive" | "noseed"
    \* @type: Int;
    MaxJ,     \* bound on |J|
    \* @type: Int;
    MaxOps,   \* bound on Len(log)
    \* @type: Int;
    MaxAnts   \* bound on antecedents per justification

A     == {"a", "b"}
F     == "F"
Nodes == A \cup {"x", "y", F}

\* Justification pool: 1..MaxAnts antecedents, consequent not among them.
Ants  == {s \in SUBSET Nodes : Cardinality(s) \in 1..MaxAnts}
JPool == {j \in {[ants |-> s, c |-> n] : s \in Ants, n \in Nodes} : j.c \notin j.ants}

VARIABLES
    \* @type: Set(Str);
    enabled,
    \* @type: Set({ants: Set(Str), c: Str});
    J,
    \* @type: Set(Str);
    believed,
    \* @type: Str -> Set(Set(Str));
    label,
    \* @type: Seq({op: Str, node: Str, ants: Set(Str)});
    log

vars == <<enabled, J, believed, label, log>>

----------------------------------------------------------------------------
(* Reference semantics *)

\* @type: (Set(Str), Set({ants: Set(Str), c: Str})) => Bool;
Closed(S, JS) == \A j \in JS : j.ants \subseteq S => j.c \in S

\* n is in the least closed superset of E.
\* @type: (Str, Set(Str), Set({ants: Set(Str), c: Str})) => Bool;
InCl(n, E, JS) == \A S \in SUBSET Nodes : (E \subseteq S /\ Closed(S, JS)) => n \in S
\* @type: (Set(Str), Set({ants: Set(Str), c: Str})) => Set(Str);
Cl(E, JS) == {n \in Nodes : InCl(n, E, JS)}

Nogood(e) == InCl(F, e, J)

\* @type: Set(Set(Str)) => Set(Set(Str));
Min(S) == {e \in S : \A e2 \in S : e2 \subseteq e => e2 = e}

Supports(e, n) == InCl(n, e, J) /\ (n = F \/ ~Nogood(e))
DLabel(n) == Min({e \in SUBSET A : Supports(e, n)})

\* Everything that can depend on a: least set containing a, closed under
\* "some antecedent inside => consequent inside".
FwdClosed(S) == \A j \in J : (j.ants \cap S # {}) => j.c \in S
Down(a) == {n \in Nodes : \A S \in SUBSET Nodes : (a \in S /\ FwdClosed(S)) => n \in S}

----------------------------------------------------------------------------
(* Propagation steps *)

\* @type: {ants: Set(Str), c: Str} => Bool;
JFireOK(j) == j \in J /\ j.ants \subseteq believed /\ j.c \notin believed
JFire == \E j \in J : JFireOK(j)
         /\ believed' = believed \cup {j.c}
         /\ UNCHANGED <<enabled, J, label, log>>

\* Naive cleanup (Doyle without well-founded support).
UnsupOK(n) == Mode = "naive" /\ n \in believed /\ n \notin enabled
              /\ \A j \in J : j.c = n => ~(j.ants \subseteq believed)
Unsupport == \E n \in Nodes : UnsupOK(n)
             /\ believed' = believed \ {n}
             /\ UNCHANGED <<enabled, J, label, log>>

\* @type: ({ants: Set(Str), c: Str}, Set(Str)) => Bool;
Covers(j, e) == \A x \in j.ants : \E ex \in label[x] : ex \subseteq e
Inconsistent(e) == \E g \in label[F] : g \subseteq e
\* @type: {ants: Set(Str), c: Str} => Set(Set(Str));
NewEnvs(j) ==
    {e \in Min({e2 \in SUBSET A : Covers(j, e2)}) :
        (j.c = F \/ ~Inconsistent(e)) /\ ~(\E old \in label[j.c] : old \subseteq e)}
\* @type: {ants: Set(Str), c: Str} => Bool;
LFireOK(j) == j \in J /\ NewEnvs(j) # {}
LFire == \E j \in J : LFireOK(j)
         /\ LET L1  == [label EXCEPT ![j.c] = Min(label[j.c] \cup NewEnvs(j))]
                nog == L1[F]
            IN  label' = [n \in Nodes |->
                            IF n = F THEN nog
                            ELSE {e \in L1[n] : ~(\E g \in nog : g \subseteq e)}]
         /\ UNCHANGED <<enabled, J, believed, log>>

Quiescent == ~(\E j \in J : JFireOK(j)) /\ ~(\E n \in Nodes : UnsupOK(n))
             /\ ~(\E j \in J : LFireOK(j))

----------------------------------------------------------------------------
(* External operations *)

\* @type: (Str, Str, Set(Str)) => {op: Str, node: Str, ants: Set(Str)};
Entry(op, n, s) == [op |-> op, node |-> n, ants |-> s]

Ready == Quiescent /\ Len(log) < MaxOps

Assert(a) == Ready /\ a \notin enabled
             /\ enabled' = enabled \cup {a}
             /\ believed' = believed \cup {a}
             /\ log' = Append(log, Entry("assert", a, {}))
             /\ UNCHANGED <<J, label>>

\* @type: {ants: Set(Str), c: Str} => Bool;
Justify(j) == Ready /\ j \notin J /\ Cardinality(J) < MaxJ
              /\ J' = J \cup {j}
              /\ log' = Append(log, Entry("justify", j.c, j.ants))
              /\ UNCHANGED <<enabled, believed, label>>

Retract(a) == Ready /\ a \in enabled
              /\ enabled' = enabled \ {a}
              /\ believed' = (CASE Mode = "correct" -> (believed \ Down(a)) \cup (enabled \ {a})
                               [] Mode = "noseed"  -> believed \ Down(a)
                               [] Mode = "naive"   -> believed \ {a})
              /\ log' = Append(log, Entry("retract", a, {}))
              /\ UNCHANGED <<J, label>>

Init == /\ \E j1 \in JPool, j2 \in JPool : J = {j1, j2}
        /\ enabled = {}
        /\ believed = {}
        /\ label = [n \in Nodes |-> IF n \in A THEN {{n}} ELSE {}]
        /\ log = <<>>

Next == \/ JFire \/ Unsupport \/ LFire
        \/ \E a \in A : Assert(a) \/ Retract(a)
        \/ \E j \in JPool : Justify(j)

Spec == Init /\ [][Next]_vars

----------------------------------------------------------------------------
(* Invariants (IDs from spec.md) *)

TypeOK == /\ enabled \subseteq A
          /\ J \subseteq JPool
          /\ believed \subseteq Nodes
          /\ \A n \in Nodes : label[n] \subseteq SUBSET A

I1_LiveSupport  == believed \subseteq Cl(enabled, J)
I1q_LiveSupport == Quiescent => believed \subseteq Cl(enabled, J)
I3_Complete     == Quiescent => Cl(enabled, J) \subseteq believed
L1_LabelSound   == \A n \in Nodes : \A e \in label[n] : InCl(n, e, J)
L2_LabelMinimal == \A n \in Nodes : label[n] = Min(label[n])
L3_LabelConsistent == Quiescent => \A n \in Nodes \ {F} : \A e \in label[n] : ~Nogood(e)
L4_LabelComplete   == Quiescent => \A n \in Nodes : label[n] = DLabel(n)
L5_Agree == (Quiescent /\ F \notin believed) =>
                \A n \in Nodes : (n \in believed <=> \E e \in label[n] : e \subseteq enabled)
H2_Replay == \A a \in A :
                a \in enabled <=>
                  \E i \in DOMAIN log :
                     /\ log[i] = Entry("assert", a, {})
                     /\ \A k \in DOMAIN log : k > i => log[k] # Entry("retract", a, {})

Inv == TypeOK /\ I1q_LiveSupport /\ I3_Complete /\ L1_LabelSound /\ L2_LabelMinimal
       /\ L3_LabelConsistent /\ L4_LabelComplete /\ L5_Agree /\ H2_Replay


----------------------------------------------------------------------------
(* Inductive invariants for Apalache: checked over all states satisfying them,
   not only reachable ones, so they hold at every history depth. *)

IndInit == /\ enabled \in SUBSET A
           /\ J \in SUBSET JPool /\ Cardinality(J) <= MaxJ
           /\ believed \in SUBSET Nodes
           /\ label \in [Nodes -> SUBSET SUBSET A]
           /\ log = <<>>

\* JTMS part. Implies I1 always and I3 at quiescence.
IndJ == /\ Cardinality(J) <= MaxJ
        /\ enabled \subseteq believed
        /\ I1_LiveSupport

\* ATMS part: soundness and minimality.
IndL == /\ Cardinality(J) <= MaxJ
        /\ L1_LabelSound /\ L2_LabelMinimal

\* Naive candidate: soundness, minimality, and the quiescent label invariants.
IndAll == IndJ /\ IndL /\ L3_LabelConsistent /\ L4_LabelComplete

\* Strengthened: every assumption keeps its own environment unless it is a
\* nogood, and labels are complete whenever no ATMS step is pending.
LQuiet == ~(\E j \in J : LFireOK(j))
Base   == \A a \in A : (\E l \in label[a] : l \subseteq {a}) \/ (\E g \in label[F] : g \subseteq {a})
IndL2  == IndL /\ Base
          /\ (LQuiet => /\ \A n \in Nodes \ {F} : \A e \in label[n] : ~Nogood(e)
                        /\ \A n \in Nodes : label[n] = DLabel(n))

\* Plus: no label environment contains a currently recorded nogood.
NoNogoodInLabels == \A n \in Nodes \ {F} : \A e \in label[n] : ~Inconsistent(e)
IndL3  == IndL2 /\ NoNogoodInLabels

InitIndJ   == IndInit /\ IndJ
InitIndL3  == IndInit /\ IndL3
InitIndL   == IndInit /\ IndL
InitIndAll == IndInit /\ IndAll
InitIndL2  == IndInit /\ IndL2

(* Action invariants *)
\* @type: (Seq({op: Str, node: Str, ants: Set(Str)}), Seq({op: Str, node: Str, ants: Set(Str)})) => Bool;
IsPrefix(s, t) == Len(s) <= Len(t) /\ \A i \in DOMAIN s : s[i] = t[i]
H1_LogMonotone == IsPrefix(log, log')
I2_RetractClosure == \A a \in A :
    (a \in enabled /\ a \notin enabled') => \A n \in Nodes : ~InCl(n, enabled', J) => n \notin believed'

H1_Prop == [][H1_LogMonotone]_vars
I2_Prop == [][I2_RetractClosure]_vars
=============================================================================
