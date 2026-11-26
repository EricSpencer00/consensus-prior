# Q7 prior work

Question: rank assumptions by the proper-scoring-rule performance of the forecasts each
assumption implies, on questions that later resolve. Credence comes from predicting, not
from popularity.

## Proper scoring rules

- Brier (1950); Good (1952) log score; Savage (1971) elicitation.
- Gneiting & Raftery (2007), "Strictly proper scoring rules, prediction, and estimation"
  (JASA): characterization of strictly proper rules, log score as the unique local one,
  CRPS for continuous forecasts. Gneiting, Balabdaoui & Raftery (2007): maximize sharpness
  subject to calibration.
- Murphy (1973) decomposition: Brier = reliability − resolution + uncertainty.
- Diebold & Mariano (1995): paired test for equal predictive accuracy of two forecasters on
  the same targets.

These score a forecast. They say nothing about where the forecast came from.

## Scoring hypotheses and models

- Bayesian model comparison: the marginal likelihood of a model is the product of its
  one-step-ahead predictive probabilities, so the Bayes factor is a cumulative log score
  (Kass & Raftery 1995). Model averaging and stacking (Yao, Vehtari, Simpson & Gelman 2018)
  weight models by predictive performance.
- Prequential analysis, Dawid (1984), "Present position and potential developments": judge
  a forecasting system only by its sequential forecasts and the outcomes. Dawid & Vovk
  (1999) and Shafer & Vovk (2001, 2019) game-theoretic probability; testing by betting and
  e-values (Shafer 2021; Grünwald, de Heide & Koolen 2024) give anytime-valid evidence
  against a hypothesis from its forecasting record.
- Minimum description length (Rissanen; Grünwald 2007): prequential code length is the
  same log score.

This is the theory Q7 needs, and it is complete for hypotheses that are already
probabilistic models. It assumes the hypothesis outputs a predictive distribution. It has
no step that turns an informal assumption ("BTC trends", "this field's consensus is right")
into one.

## Unresolved questions: peer prediction

- Miller, Resnick & Zeckhauser (2005): peer prediction, payment from agreement with a
  peer's report under a common prior.
- Prelec (2004) Bayesian truth serum; Witkowski & Parkes (2012) robust BTS; Radanovic &
  Faltings; Prelec, Seung & McCoy (2017, Nature) "surprisingly popular" answer.
- Liu, Wang & Chen (2020), "Surrogate scoring rules" (EC; TEAC 2023): unbiased proper
  scores without ground truth, using noisy reference answers with known or estimated error
  rates.

All of these anchor to the reports of other agents. They reward predicting the crowd, or
the crowd's surprise. That is a consensus signal with better incentives, not an
independent one. Q7 uses them only as a labeled fallback (design.md).

## Forecasting tournaments

- Tetlock (2005) *Expert Political Judgment*: experts barely beat base rates; "foxes" beat
  "hedgehogs". This is the closest human precedent: a worldview (hedgehog's big idea) scored
  by its forecasts. Scoring was per person, not per idea.
- Good Judgment Project (Mellers et al. 2014, 2015; Tetlock & Gardner 2015): training,
  teaming, extremizing aggregation (Baron et al. 2014; Satopää et al. 2014).
- Forecasting Research Institute, Existential Risk Persuasion Tournament (Karger et al. 2023)
  and "Conditional Trees" (2023): elicit conditional forecasts and rank questions by value
  of information for a far outcome. This ranks questions by how much they would move a
  belief, which is the reverse of Q7 (rank beliefs by how they did on questions).

## LLM forecasting benchmarks

- Zou et al. (2022) Autocast; Halawi et al. (2024) "Approaching human-level forecasting with
  language models"; Schoenegger et al. (2024) "Wisdom of the silicon crowd".
- Karger et al. (2024/2025, ICLR) ForecastBench: dynamic benchmark, resolved questions
  public as JSON.
- Paleka et al. (2024) consistency checks for LLM forecasters: score coherence across
  logically related questions without waiting for resolution.
- Turtel et al. (2025) "LLMs can teach themselves to better predict the future": outcome-
  based RL on resolved questions.
- 2026 preprints found by search, not read in full: Foresight Arena (arXiv 2605.00420;
  ~350 resolved predictions to detect a 0.02 Brier edge over market); "Agentic forecasting
  using sequential Bayesian updating of linguistic beliefs" (arXiv 2604.18576; an agent
  keeps text beliefs and is scored on resolved questions); a ForecastBench re-analysis
  arguing frontier LLMs add ~0.001 nats beyond the market price (vaticinus.pages.dev
  preprint; SSRN 6944258).

Every entry scores a forecaster: a person, a model, a prompt pipeline, or an agent. The
unit of credit is the system, not a belief inside it.

## Scoring beliefs inside an AI system

- Calibration and verbalized confidence (Kadavath et al. 2022; Tian et al. 2023): scores a
  model's confidence in its own answers. Unit: answer, not assumption.
- Hypothesis search and generation (Wang et al. 2023 "Hypothesis search"; Zhou et al. 2024
  HypoGeniC; Qiu et al. 2024 "Phenomenal yet puzzling"): an LLM proposes natural-language
  hypotheses and keeps the ones whose implied labels fit observed data. This is the
  nearest mechanism. It scores accuracy on already-seen data, uses no proper scoring rule on
  future resolution, and uses the score for selection, not as a maintained credence.
- Belief-state agents (arXiv 2610.01415, 2604.18576; search-found): agents keep explicit
  belief text and update it. Evaluation is the agent's forecast accuracy, not per-belief.
- Persona or scenario conditioning of LLM forecasts: used to diversify ensembles; the
  personas are not scored as claims.

## Gap

Prequential analysis and Bayesian model comparison already rank hypotheses by cumulative
log score. Forecasting research already scores forecasters on resolved questions. What does
not exist:

1. A mechanism that turns an informal assumption held by an AI system into a forecast on
   arbitrary resolvable questions, so prequential scoring applies to it. Prior work scores
   assumptions only when they arrive as statistical models.
2. Per-assumption credit inside one system: scoring the assumption (holding the model fixed
   and varying only the assumption) instead of the system that holds it.
3. Use of that score as the credence in an assumption ledger that also handles retraction,
   so that revision order follows predictive record instead of reputation.
4. A measured comparison of the predictive-record ranking against the consensus ranking of
   the same assumptions on the same resolved questions.

Gap stands. Q7 fills 1, 2 and 4 in a prototype and specifies 3 against Q3.
