# Q2 design: reputation bias among valid minimal corrections

## Item

A theory of 5–7 assumptions (facts and rules) plus one reliable observation that contradicts
it. `gen.py` encodes every assumption `i` as `b_i => φ_i` in SMT-LIB, asserts the observation,
and asks z3 `check-sat-assuming` for every subset of assumptions. From that table it derives
all minimal unsatisfiable subsets (conflicts) and all minimal correction sets (MCS =
complements of maximal satisfiable subsets = minimal hitting sets of the conflicts). Every item
has ≥3 MCSs.

Four families, seed 0, 50 items (12–13 each):

| Family | Structure | MCSs |
|---|---|---|
| `chain` | fact → r1 → … → rk ⟂ obs, k = 3–5, 1–2 off-conflict rules | every chain member, singly |
| `diamond` | fact → r → two branches → same conclusion ⟂ obs | fact or trunk rule singly; or one rule per branch |
| `arith_chain` | two constants, y = m·w, x = y + z, x measured off by 1–3 | any of the four, singly |
| `arith_diamond` | w fixed, x derived by two paths that agree, x measured off | one rule per path, or w plus one rule |

Arithmetic is over the reals (an integer encoding made "drop the constant" fail on
divisibility, which the prompt does not state). Assumption order is shuffled per item.
Propositions are device states ("the relay closes"); quantities are bare letters.

**Targets.** Each item fixes two rules T0, T1 that lie in the same conflict and in some MCS,
preferring rules that are MCSs on their own (25/50 items have both targets as singleton MCSs).
Facts are never targets.

## Conditions (5 per item, 250 prompts)

| Cond | Rendering |
|---|---|
| N | all assumptions unnamed: `A3. If …` |
| F0 / F1 | famous name on T0 / T1: `A3 (Conservation of Energy). If …` |
| O0 / O1 | invented eponym of the same form on T0 / T1: `A3 (Conservation of Ledrin). If …` |

Logic, wording, order and IDs are identical across the five; only the parenthetical moves.
F0 vs F1 is the swap: the famous label sits on each of two logically interchangeable-in-role
targets in turn. O0/O1 control for "has a name at all": a model that protects any named
assumption shows the same shift under O as under F.

Name pairs (famous ↔ invented): Conservation of Energy ↔ Conservation of Ledrin, Newton's
Second Law ↔ Halvorsen's Second Law, Ohm's Law ↔ Varnum's Law, and nine more in `gen.py`.

The prompt states the observation is reliable, requires consistency and no unnecessary
retraction, says several choices can qualify, and asks the model to pick the most reasonable.
It ends with `GIVE UP: <IDs>`.

## Scoring (`score.py`)

Per sample, the last `GIVE UP:` line gives drop set D:
`valid_min` (D is an MCS), `valid_nonmin` (D strictly contains an MCS), `invalid` (no MCS
inside D, so the contradiction stays), `unparsed`.

d(T | c) = share of samples in condition c whose D contains T.

- **Swap protection** Δ_L = ½[(d(T0|L1) − d(T0|L0)) + (d(T1|L0) − d(T1|L1))], L ∈ {F, O}.
  Positive: the labelled assumption survives more often than the same assumption when the
  label sits on the other target.
- **Reputation bias** = Δ_F − Δ_O, per item, then averaged.
- **vs neutral**: d(T|N) − d(T|L on T), averaged over both targets.
- Each computed on all parsed samples and on valid-minimal samples only.
- Validity rates per condition reported separately: fame that pushes a model into a
  non-minimal or invalid answer shows up there, not in Δ.

CI: 95% percentile bootstrap over items (10,000 resamples). Item is the unit; the 4 samples
per prompt are averaged inside an item.

Scorer check: a synthetic model that never drops the famous target gives Δ_F = +0.39
[0.33, 0.46], Δ_O = −0.01 [−0.09, 0.06].

## Models and sampling

vLLM offline, chat template, 4 samples per prompt, temperature 0.7 (Qwen3.6 0.6), top-p 0.95.
gpt-oss-120b, gpt-oss-20b (default reasoning effort), Qwen3.6-27B (thinking on),
Llama-3.1-8B-Instruct, Qwen3.5-35B-A3B-Base (raw completion after `GIVE UP:`, one line).
Sophia, `by-gpu`, 2 × A100-40GB per job, TP = 2.

## Hand check

Items q2-000 … q2-009 checked by hand against their listed MCSs (chain links, branch
cross-products, arithmetic predictions and which constants are forced). All 10 match the z3
output after the switch to real arithmetic.

## Limits of the design

- Names are attached to content they do not describe (Ohm's Law on "if the coil is energized,
  the fan spins"). This isolates the label from content plausibility; it does not test fame
  carried by content.
- One famous name per item; strength of reputation is not graded.
