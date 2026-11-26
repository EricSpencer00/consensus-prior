# Q6 baseline: re-checking Mathlib after a one-line change

**Setup**
- Mathlib `v4.33.0` (db584cd), Lean `v4.33.0`, Lake default (no `cache get`).
- Apple M1 Max, 10 cores, 64 GB.
- The machine was shared with other agents: two JVMs at 100% CPU throughout. CPU time is the
  stable number; wall time is an upper bound.

**Target file:** `Mathlib/Algebra/Group/Basic.lean`. It sits low in the import graph, is
written in the module system (`module`, `public section`), and 6,839 modules import it
transitively.

## Results

| run | change | modules rebuilt | wall | CPU (user+sys) | share of full CPU |
|---|---|---|---|---|---|
| full | build from scratch | 8,690 jobs (8,312 Mathlib modules) | 4,878 s (81 min) | 32,047 s (8.9 h) | 100% |
| e0 | none (no-op) | 0 | 8.3 s | 14 s | 0.04% |
| e1 | one-line proof edit in `mul_left_comm` (`mul_comm a` → `mul_comm a b`) | 1 | 14.4 s | 21 s | 0.07% |
| e2 | revert e1 | 1 | 14.6 s | 22 s | 0.07% |
| e3 | append one public lemma (`a * 1 = a := mul_one a`) | 6,840 | 3,756 s (63 min) | 28,066 s (7.8 h) | 88% |

Edit script and raw timings: `lean/`.

## What gets rechecked

- **Proof-body edit (e1, e2).** Lean's module system keeps proofs out of the exported
  interface, so Lake rebuilds only the edited module (7 s of elaboration). No importer is
  touched. This is the incremental case working.
- **Interface edit (e3).** Adding one unused lemma changes the module's public interface
  hash. Lake then re-elaborates the file and all 6,839 transitive importers, 88% of the CPU cost
  of a from-scratch build. None of those modules mention the new lemma. A dependency-precise
  scheme (iCoq-style, per declaration) would re-check zero of them. The 7.8 CPU-hours are
  pure over-approximation from module-level granularity.
- **Trust.** The e1 skip is sound because Lean theorems are proof-irrelevant and the
  statement hash did not change; that argument lives in Lake's trace logic, not in a checked
  certificate. `lake exe cache get` replaces local checking with downloaded `.olean` files and
  trusts Mathlib CI outright.

## The gap this measures

Granularity sets the cost of re-checking. Here a one-line change costs either 0.07% or 88%
of a full check, depending only on whether it touches a module's public interface, not on
what it affects semantically. A verified-compiler pipeline that keys re-validation on files
or modules inherits the same cliff. seL4 and Alive2 sit at the 100% end today (`prior.md`).

## Kernel-only recheck

`lake env leanchecker --fresh Mathlib` replays every declaration in Mathlib and its
dependencies through the kernel, with no elaboration:

| check | wall | CPU | share of full CPU |
|---|---|---|---|
| kernel replay of all Mathlib, one thread | 1,271 s (21 min) | 1,250 s | 3.9% |

The trusted check costs 1/25 of building. Elaboration (tactic search, unification, instance
resolution) is the expensive part, and it sits outside the trusted base. So a re-check needs
three things:

- an untrusted cache of elaborated terms;
- a kernel re-check of each declaration whose term or dependencies changed;
- a key that names those dependencies.

That is the proof-carrying-code split applied to incremental builds. A full rebuild never
needs to re-elaborate in order to re-establish trust.

The scope of `--fresh` comes from leanchecker's documentation and the single-thread run time.
I did not confirm declaration counts.
