# Prior art: GPT-1900

Michael Hla, 2026. Fork of nanochat. Code: github.com/michaelhla/gpt1900 (MIT). Blog:
michaelhla.com/blog/machina-mirabilis.html. Models and data: huggingface.co/mhla.

## What was built

| Item | Value |
|---|---|
| Base model | `mhla/gpt1900-d34-22btok`: nanochat d34, 3.29B params, dim 2176, 17 heads × 128, ctx 2048, vocab 32,768 |
| Tokens | ~22B (6.7 tokens/param; card says "11x" against non-embedding params), 10,507 steps, ~5.5e20 FLOPs |
| Hardware | 64 H100 (8×8), FP8 tensorwise, Muon+AdamW |
| Quality | val BPB 0.726; CORE 0.140 (pre-1900) vs 0.163 (pre-1905), 0.190 (pre-1964), 0.260 (FineWeb-Edu) |
| Corpus | `mhla/pre1900-corpus`, 56.4 GB parquet: Institutional Books (Harvard), British Library books, AmericanStories newspapers; `year < 1900` |
| Corpus filters | OCR cleanup; token-prior quality filter; anachronism filter: reject on photon/spacetime/transistor etc., on ≥5 post-1900 years, or on ≥3 ambiguous terms (quantum, nuclear, radiation) |
| Later variants | `gpt1905-d34` (~40B tokens), `gpt1964-d34` |

## Training chain of the headline model (v11)

1. Base pretraining on pre-1900 text.
2. Physics CLM: ~290M tokens, ~2,600 texts from Gutenberg, Wikisource, Internet Archive. The
   "expanded" set used by v11 runs to a **1905** cutoff and includes Planck 1901, Lorentz 1904 and
   Rutherford on radioactivity.
3. SFT: 53k conversations **written by Claude** from corpus excerpts ("safe" subset 32k).
4. RL: REINFORCE with DAPO-style normalisation, 839 steps. Problems: an LLM extracts an insight
   from a physics excerpt and frames it as a contradiction (284 train / 14 val). Reward: a modern
   LLM judge (Claude Sonnet; earlier GPT-4 and gpt-4.1-mini) scoring format, coherence, correctness.

## Evaluation

8 prompts (`EVAL.json`): UV catastrophe, photoelectric effect, four special-relativity thought
experiments, two general-relativity thought experiments. Graded 0–5 by an LLM judge, 3 samples
per task. v11 peak mean 1.25/5; best single samples photoelectric 4/5, elevator 3/5. The peak
checkpoint was chosen among 24 by the same eval. The author calls the evaluation "vibes based".

## Why it does not answer Q4

- **Assumption menu.** UV and photoelectric prompts list the 3–4 classical assumptions and ask
  which is wrong. The model picks from a menu instead of finding the assumption.
- **Answer in the prompt.** The SR prompts state "all inertial observers measure light … to have
  the same speed c" and "there is no preferred inertial frame"; the GR prompt states "acceleration
  and gravity are physically equivalent". These are the discoveries, given as premises.
- **Post-cutoff leaks.** Physics CLM reaches 1905 (Planck's quantum, Lorentz transformations). SFT
  text and RL problems were written by a modern LLM; the RL reward comes from a modern LLM that
  knows the answer. Every stage after pretraining carries 20th-century knowledge.
- **No leak audit** of the corpus beyond keyword rejection; no canary report, no reprint check.
- **Selection on test.** Peak checkpoint and best sample picked on the 8-prompt eval.
- **One cutoff, one run, no replication.** `EVAL_no_assumptions.json` exists but no scores for it
  are reported.
- **Licence.** `pre1900-corpus` republishes Institutional Books text under MIT; the IDI terms
  forbid redistribution.

## What we keep

nanochat d34 recipe and tokenizer size, for a like-for-like comparison. The pre-1900 base model
is a usable baseline for our evaluation once we audit it with our canaries.
