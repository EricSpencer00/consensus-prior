# Prior work

**Ariyani, Bouraoui, Booth, Schockaert. "Evaluating Large Reasoning Models on Belief
Revision." AACL-IJCNLP 2026 short, pp. 717–730.** Random 3-CNF knowledge bases (25 clauses,
6 atoms) plus one observation clause. Task: remove a minimal set of clauses (subset-maximal
consistent remainder) so the observation fits. Generation guarantees at least two minimal
unsatisfiable subsets and one single-clause fix. Scoring is pass/fail: any valid maximal
remainder counts ("we simply require that the model selects any of these"). Errors split into
non-minimal, observation dropped, still inconsistent. 15 models; Grok-4 99/100, o3 81,
DeepSeek-V3.2 91, small open models near 0. Clauses are verbalized as attributes of "Alice";
no clause carries a name, source or status.

**Jenkins. "AGM-Bench: Do Large Language Models Revise Beliefs Rationally?" ICLR 2026
Workshop on Logical Reasoning of LLMs (poster).** 2,400 synthetic scenarios scored against
six AGM postulates (Success, Consistency, Inclusion, Vacuity, Extensionality, Preservation)
and Darwiche–Pearl iterated revision, seven frontier models. Success and Consistency hold;
Inclusion (minimal change) and Preservation fail often; iterated revision shows belief
inertia and collateral retraction. Read from the abstract and ICLR listing only: the PDF sits
behind an OpenReview bot check, so scoring details are unverified.

## What both leave open

1. **Choice among valid revisions.** Ariyani et al. accept any valid minimal set and never
   record which one. AGM-Bench tests postulates every rational revision satisfies; the
   postulates say nothing about which of several minimal revisions to pick (that is the job
   of an entrenchment ordering, which neither benchmark supplies or measures).
2. **Reputation of the assumption.** No item in either benchmark attaches a name, authority
   or pedigree to a belief. Neither can detect a model that keeps "Conservation of Energy"
   and drops an unnamed rule with the same logical role.
3. **The swap control.** Neither renders one logical item under different labelings, so
   neither separates a preference caused by the label from a preference caused by position,
   content or logical structure.

Q2 measures exactly these three: on items with ≥2 mechanically verified minimal correction
sets, move a famous name across assumptions and measure whether the dropped set follows it.
