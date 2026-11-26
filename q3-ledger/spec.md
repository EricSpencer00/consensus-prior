# Ledger spec

One spec, four checkers. TLA+ (`tla/Ledger.tla`) carries all of it; Lean (`lean/`) and Dafny
(`dafny/`) carry the JTMS core: closure under retraction and live support.

## State

- `Nodes`: finite set of claims. `A ⊆ Nodes`: assumptions. `F ∈ Nodes \ A`: contradiction.
- `enabled ⊆ A`: assumptions currently asserted.
- `J`: set of justifications `⟨ants, c⟩`, `ants` a nonempty subset of `Nodes`, `c ∈ Nodes \ ants`.
  Any node, assumptions included, can be a consequent.
- `believed ⊆ Nodes`: the stored belief set (JTMS view).
- `label : Nodes → set of environments`, an environment being a subset of `A` (ATMS view).
- `log`: sequence of operations.

## Reference semantics

- `Closed(S, J)`: every `⟨ants, c⟩ ∈ J` with `ants ⊆ S` has `c ∈ S`.
- `Cl(E, J)`: least closed superset of `E`. A node in `Cl(E, J)` has a well-founded
  derivation from `E`; that derivation is its support. `E` is a *live support set* for `n`
  when `E ⊆ enabled` and `n ∈ Cl(E, J)`.
- `Nogood(e)`: `F ∈ Cl(e, J)`.
- `DLabel(n)`: minimal elements of `{e ⊆ A : n ∈ Cl(e, J) ∧ (n = F ∨ ¬Nogood(e))}`.
- `Down(a)`: least set containing `a` and closed under "some antecedent is in the set ⇒ the
  consequent is in the set". Everything that can depend on `a`.

## Operations

- `Assert(a)`: `enabled ∪= {a}`, `believed ∪= {a}`, then propagate.
- `Justify(j)`: `J ∪= {j}`, then propagate.
- `Retract(a)`: `enabled' = enabled \ {a}`;
  `believed' = (believed \ Down(a)) ∪ enabled'`, then propagate.
- `Query(n)`: `n ∈ believed`. Read-only; not logged.
- Propagation (internal steps, one justification per step):
  - JTMS fire: `ants ⊆ believed`, `c ∉ believed` ⇒ add `c`.
  - ATMS fire: environments that cover one label environment of every antecedent, minimized,
    minus nogood supersets (unless `c = F`), not subsumed by `label[c]` ⇒ add them to
    `label[c]` and minimize; if `c = F`, drop every nogood superset from every other label.
- `Quiescent`: no propagation step is enabled. External operations run only when quiescent.
  Every operation appends `⟨op, node, ants⟩` to `log`.

Two broken retraction variants serve as controls:

- `naive` (Doyle without well-foundedness): `believed' = believed \ {a}`, then repeatedly drop
  a non-enabled node that has no justification with all antecedents believed.
- `noseed`: `believed' = believed \ Down(a)` (forgets to re-seed with the still-enabled
  assumptions that sit downstream of `a`).

## Invariants

| ID | Name | Statement | When |
|----|------|-----------|------|
| I1 | Live support | `believed ⊆ Cl(enabled, J)`: no belief without a live support set | always (correct mode); quiescent (all modes) |
| I2 | Closure under retraction | after `Retract(a)`, every `n ∉ Cl(enabled \ {a}, J)` is out of `believed'` | every Retract step and after |
| I3 | Completeness | `Cl(enabled, J) ⊆ believed` | quiescent |
| L1 | Label soundness | `e ∈ label[n] ⇒ n ∈ Cl(e, J)` | always |
| L2 | Label minimality | no two environments in `label[n]` are ⊆-comparable | always |
| L3 | Label consistency | `n ≠ F ∧ e ∈ label[n] ⇒ ¬Nogood(e)` | quiescent |
| L4 | Label completeness | `label = DLabel` | quiescent |
| L5 | JTMS/ATMS agreement | `F ∉ believed ⇒ (n ∈ believed ⇔ ∃ e ∈ label[n]. e ⊆ enabled)` | quiescent |
| H1 | Monotone log | `log` is a prefix of `log'` | every step |
| H2 | Replay | `a ∈ enabled ⇔` the log holds `Assert(a)` with no later `Retract(a)` | always |

I2 is I1 instantiated at a Retract step: with belief defined by live support, closure under
retraction is not a separate axiom but a consequence. Lean and Dafny state it as its own theorem
about `retract` so the claim is explicit.

Labels never change on Assert or Retract. That is the ATMS design: labels are context-free and
retraction only moves `enabled`. L5 ties the two views together, so I2 also holds in ATMS
terms: after `Retract(a)`, a node stays believed only if some label environment avoids `a`.
