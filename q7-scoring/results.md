# Q7 results: prototype

## Setup

- Questions: Polymarket "Bitcoin above ___ on <date>?" events, 2025-07-31 to 2025-11-30,
  92 days with a resolved event under the standard slug (20 days missing, mostly alternate
  days in Aug–Sept). 968 resolved strike markets.
  Resolution: Binance BTC/USDT 1-minute close at noon ET.
- Forecast time: 24 h before resolution. Spot and volatility from Coinbase BTC-USD hourly
  closes at or before that time. Market price: last Polymarket trade price at or before that
  time (10-minute fidelity; always 594–598 s old).
- Primary set: one question per day, the strike nearest spot (92 questions, base rate 0.50).
  All-strikes set: 968 questions, scored with a day-block bootstrap because strikes on one day
  share one price path.
- Scoring: log score with forecasts clipped to [0.01, 0.99]; Brier alongside; 5,000-sample
  day-block bootstrap.
- Code: `fetch.py` (public read-only APIs), `score.py`. Raw output: `results_raw.txt`.

## Assumptions and their implied forecasts

Each is a claim about how BTC moves over the next 24 h, compiled to `P(S_T > K)`:

| assumption | claim | forecast |
|---|---|---|
| random_walk | price is a driftless random walk, volatility = trailing 30 d | lognormal, σ from 720 hourly returns |
| fat_tails | same, but returns are heavy-tailed | Student-t (df 3), same variance |
| vol_clustering | recent volatility persists | lognormal, σ from trailing 24 h |
| trend | the last 24 h move continues | lognormal, drift = trailing 24 h return |
| mean_reversion | the last 24 h move reverses | lognormal, drift = −trailing 24 h return |
| status_quo | the price stays where it is | 0.99 if spot > strike, else 0.01 |
| market (consensus) | the crowd price is right | Polymarket price |

## Scores

Primary set (92 questions):

| forecaster | mean log score | Δ vs market (95% CI) | Brier | P(best assumption) |
|---|---|---|---|---|
| market | −0.612 | 0 | 0.213 | – |
| fat_tails | −0.612 | −0.001 (−0.034, +0.029) | 0.214 | 0.66 |
| random_walk | −0.619 | −0.007 (−0.029, +0.014) | 0.216 | 0.25 |
| vol_clustering | −0.630 | −0.019 (−0.046, +0.008) | 0.221 | 0.09 |
| trend | −0.880 | −0.268 (−0.471, −0.072) | 0.277 | 0.00 |
| mean_reversion | −0.900 | −0.288 (−0.450, −0.141) | 0.315 | 0 |
| status_quo | −1.708 | −1.097 (−1.516, −0.702) | 0.362 | 0 |

All strikes (968 questions):

| forecaster | mean log score | Δ vs market (95% CI) | Brier | P(best assumption) |
|---|---|---|---|---|
| market | −0.165 | 0 | 0.049 | – |
| random_walk | −0.168 | −0.003 (−0.009, +0.003) | 0.050 | 0.66 |
| fat_tails | −0.170 | −0.005 (−0.014, +0.003) | 0.050 | 0.17 |
| vol_clustering | −0.172 | −0.008 (−0.017, +0.002) | 0.050 | 0.17 |
| trend | −0.217 | −0.052 (−0.086, −0.018) | 0.063 | 0.00 |
| mean_reversion | −0.261 | −0.096 (−0.136, −0.060) | 0.080 | 0 |
| status_quo | −0.333 | −0.168 (−0.215, −0.124) | 0.069 | 0 |

Posterior credence among the six assumptions (uniform prior, all strikes): random_walk 0.91,
fat_tails 0.08, vol_clustering 0.01, trend 2e−21, mean_reversion 4e−40, status_quo 3e−70.
On the primary set: fat_tails 0.58, random_walk 0.31, vol_clustering 0.11, the rest < 1e−10.

## Ranking

- Resolved: {random_walk, fat_tails, vol_clustering} > trend > {mean_reversion, status_quo}.
  random_walk beats trend by +0.049 nats/question (CI +0.016, +0.086) and status_quo by
  +0.165 (+0.120, +0.213). On all strikes mean_reversion beats status_quo by +0.072
  (+0.016, +0.133).
- Not resolved: the order inside the top three. Every paired difference among them has a CI
  spanning zero, and the leader flips between the primary set (fat_tails) and all strikes
  (random_walk). trend vs mean_reversion is also unresolved on 92 days.
- No assumption beats the market. The top three are statistically indistinguishable from it.

## Proper scoring vs consensus

Consensus ranking = assumptions ordered by mean distance from the market price.

| set | consensus ranking | proper-score ranking |
|---|---|---|
| primary | random_walk > vol_clustering > fat_tails > mean_reversion > trend > status_quo | fat_tails > random_walk > vol_clustering > trend > mean_reversion > status_quo |
| all strikes | random_walk > fat_tails > vol_clustering > trend > status_quo > mean_reversion | random_walk > fat_tails > vol_clustering > trend > mean_reversion > status_quo |

- The two rankings agree on the coarse structure: the assumptions closest to the market are
  the ones that predict best. In this domain the consensus is a good forecaster, so
  closeness to consensus and predictive record coincide.
- One disagreement is significant: on all strikes, consensus-closeness ranks status_quo above
  mean_reversion; proper scoring ranks it last, with the paired difference excluding zero.
  status_quo was closer to the outcome than the market on 156 of 216 questions where they
  differed by more than 0.1, and still lost 0.73 nats per such question. Being right more
  often while confidently wrong when wrong is exactly what agreement counts and a proper
  score punishes.
- The other disagreements (fat_tails first on the primary set, trend over mean_reversion) sit
  inside the noise.
- Where assumptions departed from the market by more than 0.1, the market won on average for
  every assumption. fat_tails was closer to the outcome on 34 of 48 such questions and still
  lost 0.03 nats per question.

## What this shows for Q7

1. The pipeline works end to end: assumption → implied forecast → proper score → credence,
   with no input from popularity.
2. 92 independent resolution days separate wrong assumptions from right ones at ~0.05 nats
   per question; they do not separate near-equivalent assumptions at ~0.01. Foresight Arena's
   ~350-prediction estimate for a 0.02 Brier edge matches this.
3. A domain where consensus is efficient gives agreement between the two rankings. The Q7
   test case needs a domain where consensus is known to have been wrong for a period, so the
   rankings can diverge. Candidates: long-dated questions with known favorite–longshot bias,
   and pre-cutoff scientific questions from Q4.

## Not verified

- Coinbase BTC-USD stands in for Binance BTC/USDT; the basis (typically under 0.1%) is not
  measured.
- The 10-minute market price is the last trade, not the bid-ask midpoint.
- Questions come from one four-month window with a falling November; regime dependence of the
  trend vs mean_reversion order is not tested.
- No conditioned-LLM mechanism was run; only structured assumptions.
