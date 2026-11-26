# Consensus prior

Goal: AI that judges a claim by whether it checks, not by whether it agrees with
consensus, and revises broken assumptions in a way it can account for. End test: a
model blind to the answer reaches a discovery that overturned its era's consensus.

## Questions

| ID | Question | Track dir | Compute |
|----|----------|-----------|---------|
| Q2 | Protection: when a contradiction forces a model to give up an assumption and several minimal fixes are valid, does it protect the reputable ones? | `q2-protection/` | Sophia |
| Q3 | Ledger: an assumption ledger with retraction and closure, verified across proof systems (Lean, TLA+ with TLC and Apalache, Isabelle/Rocq/Dafny) | `q3-ledger/` | local |
| Q4 | Time-sliced discovery: models trained only on pre-cutoff text, leak-audited, several cutoffs, no assumption menu | `q4-cutoff/` | Polaris |
| Q6 | Cheap rechecking: machine-checked binaries exist but need full re-verification on every compile, which makes them unusable in practice. Make rechecking incremental; bitwise GPU re-execution is the runtime half | `q6-recheck/` | local + Sophia |
| Q7 | Ranking without consensus: rank assumptions by proper scores on questions that resolve | `q7-scoring/` | local |

Dropped: Q1 (wrongful rejection of valid proofs), Q5 (agent fleets as consensus
amplifiers; prior results likely cover it).

## Compute

ALCF Polaris and Sophia (A100), ALCF Inference Endpoints, Amazon Bedrock and the Anthropic API.
Cluster scripts expect `$WORK` (project directory) and `HF_HOME=$WORK/hf-cache`.

## Q2 results so far

Task: a reliable observation contradicts a theory; several minimal fixes are valid. Two target
assumptions carry a famous name, a made-up name of the same form, or no name, and the label swaps
between them. Bias = protection under the famous name minus protection under the made-up name.

Replication on 200 held-out items, 4 samples per prompt (`q2-protection/replication.md`,
hypotheses committed before any output):

| Model | Run | Δ famous | Δ made-up | Bias [95% CI] |
|---|---|---|---|---|
| gpt-oss-120b | Sophia | +0.110 | −0.038 | **+0.148 [+0.10, +0.20]** |
| Beam 1.0 | ALCF endpoint | +0.099 | +0.034 | **+0.064 [+0.02, +0.11]** |
| Nemotron 3 Ultra | ALCF endpoint | +0.077 | +0.013 | **+0.064 [+0.02, +0.10]** |
| Mistral Medium 3.5 | Sophia | +0.142 | +0.098 | **+0.044 [+0.01, +0.08]** |
| Gemma 4 31B | Sophia | +0.036 | −0.007 | **+0.043 [+0.01, +0.08]** |
| Muse Spark | ALCF endpoint | +0.080 | +0.041 | **+0.039 [+0.01, +0.07]** |
| Qwen3.8-Flash-Next | Sophia | +0.158 | +0.129 | **+0.029 [+0.00, +0.06]** |
| gpt-oss-20b | Sophia | +0.081 | +0.054 | +0.027 [−0.01, +0.07] |
| Mistral Large 4 | ALCF endpoint | +0.100 | +0.081 | +0.020 [−0.00, +0.04] |
| Inkling-2-small | ALCF endpoint | +0.072 | +0.069 | +0.004 [−0.04, +0.05] |
| Qwen3.8-27B | Sophia | +0.103 | +0.114 | −0.012 [−0.04, +0.01] |
| Inkling | ALCF endpoint | −0.007 | +0.086 | **−0.092 [−0.13, −0.05]** |
| Claude Opus 5.5 | Claude Code subagents | +0.169 | +0.170 | −0.002 [−0.02, +0.01] |
| Claude Sonnet 5.5 | Claude Code subagents | +0.162 | +0.173 | −0.011 [−0.03, +0.01] |

Observations:
- Every model keeps a named assumption more often than the same assumption unnamed.
- Seven models also favour famous names over made-up ones; gpt-oss-120b by far the most.
- One model favours made-up names: Inkling (−0.092), in every sample. Its smaller sibling
  Inkling-2-small shows no bias. The pilot's Claude Opus reverse bias (−0.052, 50 items, API)
  appeared in the first subagent sample and not in the next three.

Not yet known: whether the bias tracks fame or something else the names carry (familiarity,
domain, wording); whether it comes from training or from the prompt format; whether the Claude
result depends on running as subagents instead of single API requests. Still running:
Kimi K2.6 (Sophia).

Raw completions: release `q2-replication-raw` (96 MB tarball). Full page: `results.html`.
