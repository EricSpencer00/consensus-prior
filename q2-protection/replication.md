# Q2 replication: preregistration (written 2026-11-24, before any replication output)

200 new items, `gen.py --n 200 --seed 1` (`items_rep.jsonl`, `prompts_rep.jsonl`; 50 per family,
no item shared with the 50-item pilot). Same 5 conditions, 4 samples per prompt, same scorer
(`Q2_ITEMS=items_rep.jsonl python3 score.py ...`), same sampling per model as the pilot.

Open-weight models only, on Sophia (ALCF allocation, no paid API).

Hypotheses, tested on valid-minimal answers, 95% bootstrap CI over items:
1. gpt-oss-120b: reputation bias Δ_F − Δ_O > 0 (pilot +0.126 [+0.04, +0.21]).
2. Name effect: Δ_O > 0 for gpt-oss-20b, Qwen3.8-27B and Kimi (pilot significant).
3. No other pilot model shows reputation bias (CI includes 0).

A hypothesis replicates if the replication CI excludes 0 in the predicted direction.
New models (Kimi K2.6, Qwen3.8-Flash-Next, Mistral Medium 3.5) are exploratory.
The Claude reverse bias (Opus 5.5, −0.05) was not in the preregistered set; it was added later with Claude Code subagents (below), so it is exploratory.

## Results

| Model | Valid-minimal | Δ_F | Δ_O | Bias Δ_F − Δ_O | Items | Verdict |
|---|---|---|---|---|---|---|
| gpt-oss-120b | 99.4% | +0.110 [+0.07, +0.15] | −0.038 [−0.07, −0.01] | **+0.148 [+0.10, +0.20]** | 200 | H1 replicates |
| gemma-4-31b | 95.3% | +0.036 [+0.01, +0.06] | −0.007 [−0.03, +0.01] | **+0.043 [+0.01, +0.08]** | 200 | H3 fails: small bias |
| gpt-oss-20b | 98.7% | +0.081 [+0.05, +0.12] | **+0.054 [+0.03, +0.08]** | +0.027 [−0.01, +0.07] | 200 | H2 and H3 replicate |
| Qwen3.8-27B | 99.8% | +0.103 [+0.07, +0.14] | **+0.114 [+0.08, +0.15]** | −0.012 [−0.04, +0.01] | 200 | H2 and H3 replicate |
| Inkling-2-small (ALCF endpoint) | 100.0% | +0.072 [+0.03, +0.12] | +0.069 [+0.03, +0.11] | +0.004 [−0.04, +0.05] | 200 | exploratory: name effect, no reputation bias |
| Beam 1.0 (ALCF endpoint) | 100.0% | +0.099 [+0.05, +0.15] | +0.034 [−0.00, +0.07] | **+0.064 [+0.02, +0.11]** | 200 | exploratory: reputation bias |
| Muse Spark (ALCF endpoint) | 100.0% | +0.080 [+0.05, +0.11] | +0.041 [+0.02, +0.07] | **+0.039 [+0.01, +0.07]** | 200 | exploratory: small reputation bias |
| Inkling (ALCF endpoint) | 100.0% | −0.007 [−0.06, +0.04] | +0.086 [+0.05, +0.12] | **−0.092 [−0.13, −0.05]** | 200 | exploratory: reverse bias |
| Nemotron 3 Ultra (ALCF endpoint) | 99.7% | +0.077 [+0.04, +0.12] | +0.013 [−0.02, +0.05] | **+0.064 [+0.02, +0.10]** | 200 | exploratory: reputation bias |
| Mistral Medium 3.5 | 99.3% | +0.142 [+0.11, +0.17] | +0.098 [+0.07, +0.13] | **+0.044 [+0.01, +0.08]** | 200 | exploratory: small reputation bias |
| Qwen3.8-Flash-Next | 99.9% | +0.158 [+0.12, +0.19] | +0.129 [+0.10, +0.16] | **+0.029 [+0.00, +0.06]** | 200 | exploratory: name effect, marginal reputation bias |
| Mistral Large 4 (ALCF endpoint) | 99.9% | +0.100 [+0.07, +0.13] | +0.081 [+0.05, +0.11] | +0.020 [−0.00, +0.04] | 200 | exploratory: name effect, no reputation bias |
| Claude Opus 5.5 (subagents, 4 samples) | 95.7% | +0.169 [+0.13, +0.21] | +0.170 [+0.13, +0.21] | −0.002 [−0.02, +0.01] | 200 | exploratory: name effect, no bias |
| Claude Sonnet 5.5 (subagents, 4 samples) | 99.8% | +0.162 [+0.13, +0.20] | +0.173 [+0.14, +0.21] | −0.011 [−0.03, +0.01] | 200 | exploratory: name effect, no bias |

- gpt-oss-120b: reputation bias replicates, larger than the pilot (+0.126) and with a CI half as
  wide. On 200 items the famous-name protection is now significant on its own (Δ_F +0.11), and
  against no label at all the famous name raises survival by +0.12 while the made-up name changes
  nothing (+0.00). 4,000 completions in 589 s on 4 A100s, all stop cleanly.
- Gemma 4 31B: H3 predicted no bias (pilot +0.023 [−0.03, +0.08]). With 200 items a small
  reputation bias appears, +0.043 [+0.01, +0.08], a third of gpt-oss-120b's. Same direction as
  the pilot point estimate; the pilot lacked the power to see it.
- gpt-oss-20b: the name effect replicates (Δ_O +0.054, pilot +0.066) and the reputation bias
  stays non-significant (+0.027 [−0.01, +0.07]). 8 of 4,000 completions hit the 12,000-token limit.
- Inkling-2-small (ALCF Inference Endpoints, Minerva B200, temperature 0.7, default reasoning):
  protects any named assumption equally, famous or made-up (+0.07 each); zero reputation bias.
  1 of 4,000 completions hit the 32,000-token limit; 0 requests lost.
- Qwen3.8-27B: the strongest name effect again (Δ_O +0.114, pilot +0.108) and no reputation
  bias (−0.012, pilot −0.003). 19 of 4,000 completions hit the 32,000-token limit.
- Beam 1.0 (ALCF Inference Endpoints, Tara GH200, temperature 0.7, default reasoning): reputation
  bias +0.064 [+0.02, +0.11], the second model after gpt-oss-120b. Famous names are protected
  (+0.10); made-up names barely (+0.03, CI touches 0). All 4,000 stop cleanly; 0 requests lost.
- Muse Spark (ALCF Inference Endpoints, Minerva B200, temperature 0.7, default reasoning):
  protects named assumptions (Δ_O +0.04) and famous ones about twice as much (Δ_F +0.08), a small
  reputation bias of +0.039 [+0.01, +0.07]. The gateway wrote its own error text into 1,029 streams,
  which were dropped and rerun; the final 4,000 all stop cleanly with 0 requests lost.
- Claude Opus 5.5 and Sonnet 5.5 via Claude Code subagents, not the API: 160 workflow agents, each
  reading one file of 50 prompts drawn from 50 different items (no agent saw two conditions of the
  same item; prompt ids opaque; item grouping and order reshuffled per sample; tools used: Read and
  StructuredOutput only). 4 samples per prompt, answers returned as the give-up set only.
  Both protect any named assumption more strongly than any open model (Δ_F and Δ_O +0.16 to +0.17)
  with no reputation bias (Opus −0.002, Sonnet −0.011). Sample 0 alone showed a reverse bias
  (Sonnet −0.048 [−0.09, −0.01], Opus −0.024); samples 1–3 did not (per-sample bias −0.003 to
  +0.024), so the pilot's Opus reverse bias (−0.052) does not replicate here. Differences from the
  pilot: Claude Code system prompt, 50 questions per context, model-chosen reasoning.

- Inkling (ALCF Inference Endpoints, Tara GH200, temperature 0.7, default reasoning): the only model
  that protects made-up names over famous ones. Made-up names are protected (+0.086); famous names
  are not (−0.007). Reverse bias −0.092 [−0.13, −0.05], below zero in every sample (−0.075, −0.083,
  −0.110, −0.102). All 4,000 stop cleanly; 0 requests lost after retries. Inkling-2-small, its
  smaller sibling, shows no bias (+0.004).

- Nemotron 3 Ultra (ALCF Inference Endpoints, Tara GH200, temperature 0.7, default reasoning):
  famous names are protected (+0.077), made-up names are not (+0.013, CI spans 0). Reputation bias
  +0.064 [+0.02, +0.10], above zero in every sample (+0.035, +0.093, +0.074, +0.063). At the
  32,000-token cap 527 of 4,000 completions spent the whole budget reasoning and returned no
  answer; those 527 were rerun at 64,000 (Kimi K2 precedent) and 11 still hit the cap. The 32k
  originals are kept in `out/nemotron-3-ultra.rep.32k.jsonl`.
- Mistral Medium 3.5 (Sophia, 2 nodes, 16 A100s, vLLM pipeline parallel, temperature 0.7): the
  strongest name protection among open models (Δ_F +0.142, Δ_O +0.098) and a small reputation bias
  of +0.044 [+0.01, +0.08], above zero in every sample (+0.048, +0.072, +0.008, +0.033). All 4,000
  stop cleanly.
- Qwen3.8-Flash-Next (Sophia, 2 nodes, 16 A100s, vLLM pipeline parallel, temperature 0.6, 32,000
  tokens): against no name, famous and made-up names both raise protection by +0.15; in the direct
  swap famous names win by +0.029 [+0.001, +0.058], positive in every sample (+0.020, +0.045,
  +0.020, +0.023). 7 of 4,000 completions hit the cap. The first job failed at load: vLLM 0.34
  pads the fused hyper-connection projection to 16 rows and counts the pad as a missing checkpoint
  weight. `run.py --no-weight-track` skips that check; the checkpoint index was verified complete
  (131 of 131 shards) and the unfused A100 path discards the pad columns.
- Mistral Large 4 (ALCF Inference Endpoints, Tara GH200, temperature 0.7, default reasoning):
  famous and made-up names both protected (+0.100, +0.081; +0.11 each against no name); bias
  +0.020 [−0.002, +0.042], not significant. At the 32,000-token cap 336 completions were cut (327
  empty), unevenly across conditions (F0 82, O0 50); those and 1 lost request were rerun at 64,000
  and 4 still hit the cap. The 32k originals are kept in `out/mistral-large-4.rep.32k.jsonl`.

## Scoring guard (2026-11-25)

Pilot (`items.jsonl`) and replication (`items_rep.jsonl`) reuse item IDs q2-000…q2-049 with
different MCS lists: "GIVE UP: A2" on q2-000 is valid-minimal in the pilot and invalid in the
replication. `score.py` now scores against one manifest and refuses rows stamped with another
manifest's SHA-256, unstamped rows unless the manifest is selected explicitly (`--items` or
`Q2_ITEMS`), unknown IDs, and repeated (model, item, cond, sample). `gen.py` stamps prompts with
the manifest SHA and the runners copy it into output rows. Tests: `python3 -m unittest test_score`.
All 19 published score files (pilot and replication) re-score to identical numbers under the
guard, scored with their own manifest; feeding pilot and replication gpt-oss-120b outputs together
is rejected at q2-000 N 0.
