# Q3 prior work

Checked 2026-11-21 (web search plus abstracts; full texts of PerMIT and the Doyle-to-AGM
survey not read).

| Work | What it verifies | Retraction closure | Support sets / ATMS labels | Systems |
|------|------------------|--------------------|----------------------------|---------|
| Doyle 1979, JTMS | Algorithm; no mechanized proof | Yes (dependency-directed) | Well-founded support pointers | none |
| de Kleer 1986, ATMS | Algorithm; label soundness, completeness, minimality, consistency stated on paper | Implicit: labels are context-free, belief = label env inside current context | Yes, the source of the label invariants | none |
| PerMIT, arXiv 2610.28987 | Two Lean 4 theorems: environment-derived memory reaches a sensitive action only through a confirmation gate, and shapes behavior only through what the gate shows. Federated protocol is paper-only. Lean artifact "available upon request" | No | No | Lean 4 |
| MemTX, arXiv 2607.23929 | I1 action gating, I2 cascade-repair completeness (transitive descendants of a retracted record go inactive), G3 no committed record with a revoked ancestor | Yes, transitive over a provenance DAG | Provenance edges only; no per-belief support sets, no alternative supports, no labels | Property-based testing plus a custom bounded enumerator (5.5M states). No proof assistant, no model checker. Found a missed-cascade bug on the abort path |
| Verified concurrency anomalies, arXiv 2606.17182 | Shared agent memory in TLA+ (TLC counterexamples), TLAPS shallow checks, Verus proofs (274 obligations) | Cascading abort via predecessor sets recorded at read time | No | TLA+/TLC, TLAPS, Verus, GenMC. No Apalache |
| Isabelle AFP `Belief_Revision` (Fouillard et al.) | AGM postulates for contraction and revision, Levi and Harper identities | Abstract belief sets, not a dependency structure | No | Isabelle/HOL |
| Doyle-to-AGM survey, arXiv 2608.14567 | Narrative review; lists formal guarantees as future work | n/a | n/a | none |

Searches for a mechanized JTMS or ATMS in Coq/Rocq, Isabelle, Lean, Dafny or TLA+, and for a
TLA+ spec of belief revision or truth maintenance, returned nothing.

## Gap

1. No machine-checked truth maintenance system exists. Nobody has proved, in any proof
   assistant, that an incremental retraction algorithm leaves exactly the beliefs that keep
   a well-founded support from the remaining assumptions, nor that maintained ATMS labels
   stay sound, complete, minimal and consistent.
2. Agent-memory work that does verify retraction (MemTX, 2606.17182) tracks a single
   provenance edge set. A record with two independent supports is revoked when one support
   goes; neither models alternative supports, so neither can state "believed iff some
   support set is live". MemTX's check is bounded testing of an implementation, not a proof.
3. No one has written one belief-revision spec in several verification systems and
   reported where they agree and disagree. The TLA+ "trifecta" paper (arXiv 2211.07216)
   compares TLC, Apalache and TLAPS on other protocols; none of it touches truth maintenance.

The gap stands. Q3 fills it with one ledger spec checked in TLA+ (TLC and Apalache), Lean 4
and Dafny.

## Sources

- PerMIT: https://arxiv.org/abs/2610.28987
- MemTX: https://www.alphaxiv.org/abs/2607.23929
- Concurrency anomalies in multi-agent LLM memory: https://huggingface.co/papers/2606.17182
- AFP Belief Revision Theory: https://www.isa-afp.org/entries/Belief_Revision.html
- From Doyle to AGM: https://arxiv.org/abs/2608.14567
- TLA+ trifecta: https://arxiv.org/abs/2211.07216
- Doyle, "A Truth Maintenance System", AI 12(3), 1979
- de Kleer, "An Assumption-based TMS", AI 28(2), 1986
