# Q7 design

## Objects

- Assumption `a`: a claim the system holds, in text, with an id in the Q3 ledger.
- Question `q`: binary or numeric, with a forecast time `t_q`, a resolution time and a
  resolution rule. Only information available at `t_q` enters a forecast.
- Implied forecast `f_a(q)`: the predictive distribution the system issues for `q` while
  holding `a` and nothing else different.

## Assumption to forecast

Two mechanisms, same interface `forecast(a, q, info_t) -> p`.

1. Structured: `a` compiles to a model. "BTC follows a driftless random walk" becomes a
   lognormal with trailing volatility. Exact, cheap, auditable. Used when `a` is
   quantitative. The prototype uses this.
2. Conditioned LLM: a fixed base model, fixed retrieval snapshot at `t_q`, and a prompt
   that states `a` as true. Score the contrast, not the raw forecast:
   - Run `f_a` (holds `a`), `f_¬a` (holds the negation) and `f_∅` (no stance).
   - Credit for `a` is `S(f_a) − S(f_∅)` summed over questions. This isolates the assumption
     from the model's general skill.
   - Leakage control: base model cutoff before `t_q` (Q4 cutoff models), or questions that
     resolve after the model's cutoff. No search results dated after `t_q`.
   - Consistency check: if `f_a = f_∅` on a question, `a` is silent there; that question
     carries no evidence for or against `a`.

## Scoring

- Primary: log score, cumulative, prequential. Sum over questions in resolution order.
  `sum_q log f_a(y_q)` is the log marginal likelihood of `a` on the question stream, so the
  ranking is Bayesian model comparison with no extra machinery.
- Report Brier alongside, with Murphy decomposition, because log score is dominated by a few
  confident misses and readers compare Brier.
- Forecasts are clipped to [0.01, 0.99] before scoring. An assumption that says "certain"
  and misses loses `log 0.01` once, not infinity.
- Uncertainty: paired differences against a reference forecaster on the same questions,
  block bootstrap over correlated questions (same event, same day), and a Diebold-Mariano
  test on the per-block differences.
- Credence: `w_a ∝ prior_a · exp(sum_q log f_a(y_q))`, renormalized across rivals that answer
  the same questions. Prior is uniform. Popularity never enters the prior.
- Anytime-valid statement: the likelihood ratio of `a` against a rival `b` is an e-process,
  so "reject `b` in favor of `a`" at ratio 20 holds at any stopping time.

## Assumptions that make no forecast

- Silent on a question (`f_a = f_∅`): contributes zero. No credit, no penalty.
- Silent on every resolvable question: credence is unscored and marked `unscored`, not
  ranked. The ledger keeps it with its prior and flags it as untested. It never inherits
  credence from popularity.
- Indirect forecasts: find a downstream question where the assumption does bite. Generate
  candidate questions with the conditioned LLM, keep the ones where `|f_a − f_¬a|` is
  largest (the FRI value-of-information idea pointed the other way).
- Long-horizon assumptions with no resolution in reach: allowed fallback is a coherence
  score (Paleka-style consistency across related questions) and surrogate scoring. Both are
  stored as a separate field, `proxy_score`, never mixed into `score`. Peer prediction and
  Bayesian truth serum are excluded: they reward agreeing with other agents.

## Ledger plug-in (Q3)

Each ledger entry gains:

```
score:        cumulative log score over scored questions
n_scored:     number of questions where the assumption was not silent
delta_ref:    score minus the no-stance reference, with bootstrap interval
credence:     posterior weight among rivals
status:       ranked | unscored
proxy_score:  coherence/surrogate score, optional, separate
```

Uses:

1. Retraction order. When a contradiction forces giving up one of several assumptions (Q2's
   minimal-fix choice), retract the one with the lowest credence among those that are
   `ranked`. `unscored` assumptions do not get protection from being unscored. Ties go to the
   assumption with fewer scored questions.
2. Closure. Derived claims inherit the minimum credence of the assumptions they rest on.
3. Audit. Every credence traces to a list of question ids, forecasts and outcomes. A
   reviewer reproduces it from the ledger alone.

## Consensus baseline

Two consensus signals, both reported and neither used for ranking:

- Consensus forecast: the market price or community forecast on the same question. Scored by
  the same rule; tells whether an assumption beats the crowd.
- Consensus ranking: assumptions ranked by how closely their forecasts track the consensus
  forecast. Agreement with the proper-score ranking means consensus and predictive record
  coincide in that domain; disagreement is the Q7 result.
