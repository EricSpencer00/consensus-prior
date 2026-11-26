# Q2 results: pilot, 50 items × 5 label conditions × 4 samples = 1,000 completions per model

Reputation bias = Δ_F − Δ_O (swap protection under a famous name minus swap protection
under a made-up name of the same form), over valid-minimal answers, 95% bootstrap CI over items.

| Model | Valid-minimal | Δ_F | Δ_O | Bias Δ_F − Δ_O | Items |
|---|---|---|---|---|---|
| gpt-oss-120b | 99.3% | +0.048 [−0.03, +0.12] | −0.078 [−0.14, −0.02] | **+0.126 [+0.04, +0.21]** | 50 |
| gpt-oss-20b | 98.3% | +0.069 [+0.01, +0.13] | +0.066 [+0.02, +0.11] | +0.003 [−0.07, +0.07] | 50 |
| Qwen3.6-27B (32k tokens) | 75.8% | +0.037 [−0.03, +0.12] | +0.049 [+0.01, +0.11] | −0.039 [−0.09, +0.01] | 39 |
| Qwen3.8-27B | 99.9% | +0.105 [+0.05, +0.18] | +0.108 [+0.05, +0.18] | −0.003 [−0.04, +0.03] | 50 |
| Gemma 4 31B | 94.6% | +0.036 [−0.01, +0.08] | +0.013 [−0.03, +0.05] | +0.023 [−0.03, +0.08] | 50 |
| GLM-5 (Bedrock) | 85.1% | +0.036 [−0.03, +0.10] | −0.045 [−0.12, +0.03] | +0.077 [−0.02, +0.18] | 49 |
| DeepSeek V3.2 (Bedrock) | 100% | +0.070 [+0.01, +0.14] | +0.005 [−0.06, +0.07] | +0.065 [−0.03, +0.16] | 50 |
| Kimi K2 Thinking (Bedrock, 64k tokens) | 99.9% | +0.046 [−0.00, +0.10] | +0.070 [+0.03, +0.12] | −0.024 [−0.07, +0.02] | 50 |
| Claude Fable 5.2 | 100% | +0.090 [+0.03, +0.17] | +0.113 [+0.04, +0.20] | −0.023 [−0.05, +0.00] | 50 |
| Claude Opus 5.5 | 99.9% | +0.118 [+0.04, +0.21] | +0.170 [+0.09, +0.27] | **−0.052 [−0.09, −0.02]** | 50 |
| Claude Sonnet 5.5 | 100% | +0.110 [+0.01, +0.21] | +0.188 [+0.11, +0.27] | −0.078 [−0.17, +0.00] | 50 |
| Llama-3.1-8B | 23.3% | −0.058 [−0.22, +0.10] | −0.080 [−0.22, +0.06] | −0.008 [−0.34, +0.30] | 11 |

- gpt-oss-120b shows reputation bias. Most of it comes from dropping the made-up-name
  assumption more often, not from protecting the famous one.
- gpt-oss-20b protects any named assumption equally (Δ_F ≈ Δ_O ≈ +0.07): a name effect,
  no reputation effect.
- Qwen3.6-27B: the first run hit the 14,000-token limit on 70% of completions. Rerun at
  32,000 tokens (job 207318): 73% stop cleanly, 27% still hit the limit. No reputation bias;
  like gpt-oss-20b it protects any named assumption slightly.
- Qwen3.8-27B (32k tokens, 99.6% stop cleanly): the strongest name effect so far (+0.11
  for any named assumption) and zero reputation effect, with the tightest CI.
- Gemma 4 31B answers without long reasoning (656 tokens on average, all stop cleanly).
  Weak name effect, no significant reputation bias; the point estimate leans positive.
- GLM-5 and DeepSeek V3.2 lean the same way as gpt-oss-120b (+0.08, +0.07) without reaching
  significance. DeepSeek protects famous-name assumptions (Δ_F significant) and treats made-up
  names like no name. GLM-5 has the most invalid answers of any large model (13%).
- Kimi K2 Thinking: at 16,000 tokens, 144 of 1,000 completions hit the limit, 2.5× as often
  under a label (16%) as with no label (6.5%), so dropping them skewed the comparison. Rerun
  those 144 at 64,000 tokens: 1 still hits the limit. Kimi protects any named assumption
  (Δ_O significant, Δ_F borderline) with no reputation bias (−0.02).
- Claude Fable 5.2, Opus 5.5 and Sonnet 5.5 (Anthropic Message Batches, adaptive thinking at
  effort high, API-default sampling since these models reject temperature): every model protects
  named assumptions strongly (+0.09 to +0.19), and all three lean against reputation: made-up
  names get more protection than famous ones. Opus 5.5's reverse bias is significant. No
  completion hit the 64,000-token limit; answers average 580 (Sonnet), 731 (Fable) and 840 (Opus) output tokens including thinking.
- Llama-3.1-8B mostly gives valid but non-minimal fixes; too few valid-minimal items to say anything.

Raw outputs: `$WORK/consensus/q2-protection/out/` (Sophia), local `out/` (not committed).
Bedrock runs (`run_bedrock.py`): GLM-5, DeepSeek V3.2, Kimi K2 Thinking; 10.8M output tokens, plus 2.3M for the Kimi 64k rerun.
Claude runs (`run_claude.py`, Message Batches): 3,000 completions.
Jobs: 207276 (Llama), 207278 (gpt-oss-20b), 207279 (gpt-oss-120b, Qwen; 4 GPUs), 207366 (Qwen3.8, Gemma 4).

GLM-5.3-Flash and DeepSeek V4.1 Flash do not run on ALCF: both use sparse indexer attention
(top-2,048 and top-512 tokens), and every vLLM 0.34 sparse-MLA backend requires SM90+. Sophia
and Polaris are A100 (SM80). Dense attention in their place changes the model, so it is not run. Bedrock serves
GLM-5.3 only after an AWS Sales request; GLM-5 runs in its place. Inkling-Small fails on A100
too (FlexAttention score_mod unsupported on SM8x).
Job 207379 failed at attention-backend selection after NCCL formed across both nodes.
