# Q3 results

One ledger spec (`spec.md`), four checkers. MacBook (M-series, 10 cores, 64 GB), local only.
Tool versions: TLC 2026.11.19 (tla2tools nightly), Apalache 0.63.0, Lean 4.33.1 (core only,
no Mathlib), Dafny 4.11.0 (Z3 bundled). Dafny won the third-system slot: `brew install dafny`
took 17 s; Isabelle and Rocq were not tried.

Three retraction modes run through every system:

- `correct`: `believed' = close((believed \ Down(a)) ∪ enabled')`.
- `naive`: Doyle's JTMS without well-founded support (keep any node with a locally valid
  justification).
- `noseed`: `correct` without the `∪ enabled'` re-seed.

## Per system

### TLA+ / TLC (explicit state)

Bounds: assumptions {a, b}, derived nodes {x, y}, contradiction F; justification pool of
every 1- or 2-antecedent rule (50 rules); 2 preloaded rules, `MaxJ = 3`, `MaxOps = 3`.

| Mode | Checked | Result | States (distinct) | Depth | Time |
|------|---------|--------|-------------------|-------|------|
| correct | TypeOK, I1 (always), I1q, I3, L1–L5, H2; action props H1, I2 | pass | 2,638,377 | 12 | 4m14s (10 workers, idle machine); 18m25s rerun under load |
| correct, MaxOps 4, 1-antecedent pool | same | pass | 687,322 | 16 | 3m07s |
| naive | same minus I1-always | I1q violated | 1,769,819 explored | 6 | 1m56s |
| naive | I2, H1 only | I2 violated | 1,223,834 explored | 5 | 1m22s |
| noseed | same minus I1-always | I3 violated | 296,579 explored | 4 | 11s |

Naive counterexample (TLC): rules `a ← F`, `F ← a`; assert a; F fires; retract a (believed
{F}); `a ← F` fires again. The retracted assumption comes back through a cycle that runs
through itself. Noseed counterexample: `b ← {F, a}`, assert a, assert b, retract a: b is
enabled and not believed.

TLC also checks the full ATMS: labels sound, minimal, consistent and equal to the declarative
`DLabel` at quiescence, and JTMS belief equal to "some label environment inside `enabled`" (L5)
whenever F is out. All hold in every reachable state within the bounds.

### TLA+ / Apalache (symbolic, Z3)

Same module. Apalache needed type annotations on 9 operators, `DOMAIN log` in place of
`1..Len(log)`, and `MaxAnts = 1` (20-rule pool) for most runs. Bounded checking from `Init`
with `MaxAnts = 2` and the full `Inv` took 6m40s for length 2 (no error); deeper runs used
`MaxAnts = 1`.

Inductive checks (all states satisfying the invariant, any history depth, within the node
and rule bounds):

| Check | Mode | Result | Time |
|-------|------|--------|------|
| `Init ⇒ IndJ` | correct | holds | 10 s |
| `IndJ ∧ Next ⇒ IndJ'`, IndJ = `enabled ⊆ believed ∧ believed ⊆ Cl(enabled, J)` | correct, MaxAnts 1 | inductive | 11m04s |
| same | correct, MaxAnts 2 (TLC's 50-rule pool) | inductive | 47m35s |
| `IndJ ⇒ I3` | correct | holds | 2m36s |
| `IndJ ∧ Next ⇒ IndJ'` | noseed | CTI: `b ← a`, a and b enabled and believed, retract a ⇒ b enabled, not believed | 11m03s |
| `IndJ ∧ Next ⇒ IndJ'` | naive | CTI: state right after the naive Retract, before cleanup, still believes b | 11m41s |
| `IndL3 ∧ Next ⇒ IndL3'` (label soundness, minimality, base envs, no recorded nogood inside a label, completeness at ATMS quiescence) | correct, MaxAnts 1 | open: Next splits into 6 transitions; 2 cleared every conjunct, 1 is disabled in correct mode, the 4th sat on one conjunct for 25 min, 2 never ran. Stopped | 47 min SMT translation + 49 min checking |

Bounded checks from `Init`, MaxAnts 1:

| Mode | Invariant | Length | Result | Time |
|------|-----------|--------|--------|------|
| noseed | I3 | 6 | violated at step 4: `a ← b`; assert a, assert b, retract b leaves a enabled and unbelieved | 74m18s |
| naive | I1q | 8 | violated at step 5: `y ← a`, `a ← y`; assert a, y fires, retract a, `a ← y` re-fires. Same shape as TLC | 51m21s |

The conjunct `enabled ⊆ believed` makes completeness at quiescence follow from IndJ in one
step (checked: `IndJ ⇒ I3`). I did not test `I1` alone for inductiveness. Apalache's naive CTI
is the transient state right after Retract, which TLC's quiescent invariant skips; the BMC run
then found the same re-fire interleaving TLC found. TLC found both control bugs in 11 s and
1m56s; Apalache took 74 and 51 minutes for the same traces.

### Lean 4 (`lean/Ledger.lean`)

Proved, for every finite list of operations from the empty ledger, with no bound on nodes,
rules, assumptions or history length:

- `linv_run`: `n ∈ believed ↔ Derives J enabled n` (believed = inductive well-founded
  derivability), preserved by `assert`, `justify`, `retract`.
- `live_support` (I1), `complete` (I3), `closure_under_retraction` (I2: a node with no
  derivation avoiding `a` is out after `retract a`), `log_append` (H1).
- `close` is an executable worklist fixpoint with a termination proof (measure: rules whose
  consequent is not yet believed).
- Controls: `naive_violates_live_support` (cycle `x ← a, x ← y, y ← x`; after naive retract
  of a, x stays believed with no derivation) and `noseed_violates_complete` (`b ← a`).

Axioms: `propext`, `Classical.choice`, `Quot.sound` for the theorems; the two control
counterexamples also trust `native_decide` (compiled evaluation), because `close` is
well-founded recursion and does not reduce in the kernel. Not covered: ATMS labels, L1–L5, H2.
Check time 3.2 s.

### Dafny (`dafny/`)

Proved the same JTMS core with no bounds: `Close` (worklist loop, decreases
`|U − S|`), `Down`, `DoAssert`/`DoJustify`/`DoRetract` each ensure `Inv` and the log append,
`Run` over any op sequence, `LiveSupport` (I1), `Complete` (I3), `RetractClosure` (I2).
Reference semantics is "in every closed superset", not an inductive predicate; the key lemma
`Avoid` (beliefs outside `Down(a)` survive without a) is a 15-line superset argument, against
an induction on derivations in Lean. 14 obligations, 1.4 s, first attempt.

Controls (`Controls.dfy`): both fail as intended. `noseed` fails at the call site, on
`Close`'s precondition `E <= S0`, before any invariant is consulted. `naive` fails on the
`Inv` postcondition. `Counterexample.dfy` proves the x/y cycle is locally supported and not
derivable (2 obligations). Not covered: ATMS labels, L1–L5, H2.

## Where the systems disagree

1. **The shape of the naive bug depends on the execution model.** TLC's interleaved
   semantics found re-derivation of the retracted assumption through a cycle that contains
   it (`a ← F ← a`). My first Lean `naiveRetract` runs cleanup to a fixpoint before
   re-propagating, and on that ledger it is correct: `native_decide` refuted the claimed
   counterexample. The Lean/Dafny counterexample is the textbook cycle that avoids the
   retracted node (`x ↔ y`). Both are failures of well-foundedness; which one shows up is
   fixed by whether cleanup and propagation interleave.
2. **"Always" vs "at quiescence."** TLC checks invariants on reachable states, so the
   quiescent forms are natural. Apalache's inductive mode needs invariants that hold on every
   state, which forced the `enabled ⊆ believed` conjunct. For labels I wrote the
   strengthening (`Base`, `NoNogoodInLabels`) by hand: the weaker `IndL2` run exhausted the
   heap before answering. Lean and Dafny avoid the issue: propagation is a function, there are
   no intermediate states.
3. **Where noseed is caught.** TLC and Apalache report a violated invariant after a 3-op
   trace. Dafny rejects the code statically at the `Close` precondition. In Lean I proved a concrete
   counterexample theorem; I did not attempt the preservation proof for the broken version.
4. **Bounds.** TLC and Apalache cover the full ATMS but only 5 nodes, 2 assumptions, ≤ 3
   rules. Lean and Dafny cover unbounded ledgers but only the JTMS core. No system covers
   both.

## Bugs found in the spec or models

| Found by | Bug |
|----------|-----|
| TLC | CASE in `Retract` swallowed the following conjuncts (precedence); successor state undefined. Fixed with parentheses |
| TLC | Deadlock at the op bound; run with `-deadlock` |
| TLC, Apalache, Lean, Dafny | `noseed`: retraction must re-seed with every still-enabled assumption, because an assumption can also be a consequent downstream of the retracted one |
| TLC, Apalache, Lean, Dafny | `naive`: locally supported ≠ well-founded; cycles keep or restore beliefs |
| Apalache | Snowcat type errors on untyped higher-order operators; non-constant integer ranges |
| Apalache | Heap exhaustion at the default JVM heap on the `IndL2` label check after 17 min; `IndL3` ran with `-Xmx20g` |
| Lean | `Inv` collides with a core name; renamed `LInv` |
| Lean | First naive counterexample was wrong for the eager-cleanup model (see disagreement 1) |

None of the four found a bug in the `correct` mode.

## Effort

| Artifact | Lines |
|----------|-------|
| `spec.md` | 70 |
| `tla/Ledger.tla` | 215 (incl. ATMS labels and inductive invariants) |
| `lean/Ledger.lean` | 313 (incl. 2 control counterexamples) |
| `dafny/Ledger.dfy` + controls | 213 + 38 |

Wall time to a first passing check: Dafny 1 attempt; Lean 5 compile iterations; TLC 3 runs;
Apalache 4 runs to type-check and parse, then 11–48 min per inductive check and 51–74 min per
control-bug BMC trace.

## Not verified

- ATMS labels (L1–L5) in Lean or Dafny, and inductively in Apalache (`IndL3` did not finish).
  Labels are checked on reachable states only, by TLC.
- H2 (log replay) in Apalache's inductive mode and in Lean/Dafny (Lean/Dafny prove the
  append-only half, H1).
- Anything beyond 5 nodes / 2 assumptions / 3 rules in TLA+.
- Nonmonotonic justifications (out-lists), the part of Doyle's JTMS that makes support
  non-unique. The ledger is monotone: every justification has only in-antecedents.
- Correspondence between the TLA+ model and the Lean/Dafny functions is by construction from
  the same `spec.md`, not machine-checked (no refinement proof).
