# Q6 runtime half: is greedy LLM generation bitwise reproducible?

Llama-3.1-8B-Instruct, bf16, greedy, 8 fixed chat prompts, 128 new tokens, one A100-SXM4-40GB
per run. Each run is a fresh process. Both engines get the same token ids. "bs1" runs the
prompts one at a time; "bs8" runs all eight in one call (HF pads left; vLLM packs without
padding).

Compared per step: HF full-vocabulary fp32-cast logits (SHA-256); vLLM top-20 logprobs
(SHA-256). A step counts only up to the shorter of two sequences.

Software, identical on both machines: one uv venv on `/grand` (Python 3.12.16, torch
2.9.0+cu128, transformers 4.57.6, vLLM 0.12.0). Drivers: Sophia 595.71.05, Polaris 580.65.06.

Modes:
- `vllm`: defaults (CUDA graphs, torch.compile, prefix caching on)
- `vllm-bi`: `VLLM_BATCH_INVARIANT=1`, FLASH_ATTN backend, prefix caching off
- `vllm-bi-eager`: `vllm-bi` plus `enforce_eager=True`

| comparison | identical sequences | bitwise-identical steps | first token divergence |
|---|---|---|---|
| **Same machine, run 1 vs run 2** | | | |
| HF, Sophia, bs1 / bs8 | 8/8 / 8/8 | 983/983 / 983/983 | none |
| HF, Polaris, bs1 / bs8 | 8/8 / 8/8 | 983/983 / 983/983 | none |
| vLLM, Sophia, bs1 / bs8 | 8/8 / 8/8 | 983/983 / 981/981 | none |
| vLLM, Polaris, bs1 / bs8 | 8/8 / 8/8 | 983/983 / 981/981 | none |
| vLLM-bi, both machines, bs1 / bs8 | 8/8 / 8/8 | 989/989 / 983/983 | none |
| vLLM-bi-eager, both machines, bs1 / bs8 | 8/8 / 8/8 | 981/981 / 987/987 | none |
| **Sophia vs Polaris, run 1** | | | |
| HF, bs1 / bs8 | 8/8 / 8/8 | 983/983 / 983/983 | none |
| vLLM, bs1 / bs8 | 8/8 / 8/8 | 983/983 / 981/981 | none |
| vLLM-bi, bs1 / bs8 | 8/8 / 8/8 | 989/989 / 983/983 | none |
| vLLM-bi-eager, bs1 / bs8 | 8/8 / 8/8 | 981/981 / 987/987 | none |
| **bs1 vs bs8, same run (identical on both machines)** | | | |
| HF | 4/8 | 0/983 | token 29 |
| vLLM | 5/8 | 1/981 | token 26 |
| vLLM-bi | 5/8 | 0/983 | token 29 |
| vLLM-bi-eager | 4/8 | 0/981 | token 29 |
| **HF vs vLLM, run 1, both machines, bs1 and bs8** | 3/8 | n/a | |

Step-0 gap, bs1 vs bs8, largest |Δ logprob| over the shared top-20, per prompt (Sophia):

| mode | gap per prompt |
|---|---|
| vLLM | 0.12–0.38 |
| vLLM-bi | 0.12–0.29 |
| vLLM-bi-eager | 0.12–0.50 |

That is one to four bf16 ulps at logit magnitude ~20.

Wall time, 8 prompts, Sophia:

| mode | bs1 | bs8 |
|---|---|---|
| HF | 32.9 s | 5.1 s |
| vLLM | 15.6 s | 2.1 s |
| vLLM-bi | 19.6 s | 3.5 s |
| vLLM-bi-eager | 37.9 s | 4.9 s |

## Findings

1. **A fixed configuration is bitwise reproducible.** Run to run and machine to machine, on
   identical GPU model and software stack, all 24 comparisons match on every token and every
   logit bit. The two clusters run different drivers and different nodes. For this
   configuration a checker re-runs and compares hashes; no tolerance is needed.
2. **Batch composition is the nondeterminism.** Changing only the batch changes logits at the
   first step and the generated text by token 26–29 for half the prompts. This holds for HF,
   for vLLM, and for vLLM's batch-invariant mode.
3. **vLLM 0.12.0 batch-invariant mode is not batch-invariant on A100 (sm80).** That holds with
   prefix caching off and with CUDA graphs off. A re-execution checker cannot reproduce a
   result served inside a batch unless it reproduces the batch.
4. **HF and vLLM disagree on 5 of 8 greedy outputs** from identical token ids. The engine is
   part of the claim being checked.

The checkable claim is "this output came from (weights, token ids, engine, kernel config,
batch composition, GPU model)". Drop any of those fields and re-execution does not reproduce
the output.

## Jobs

| cluster | job | runs |
|---|---|---|
| Sophia (`by-gpu`, 1 GPU) | 207277 | HF ×2 |
| Sophia | 207282 | vLLM ×2 |
| Sophia | 207284 | vLLM-bi ×2, vLLM-bi-eager ×2 |
| Polaris (`debug`) | 7874654 | HF ×2 |
| Polaris (`debug-scaling`) | 7874690 | vLLM, vLLM-bi, vLLM-bi-eager, ×2 each |

These runs failed and were fixed:

| cluster | jobs | cause |
|---|---|---|
| Sophia | 207272 | venv interpreter missing on compute nodes |
| Sophia | 207280, 207281 | vLLM spawn guard |
| Sophia | 207283 | prefix caching left on in bi mode; superseded |
| Polaris | 7874629 | venv interpreter missing on compute nodes |
| Polaris | 7874671 | killed after a prompt-token fix |
| Polaris | 7874683 | Polaris CXX is nvc++; inductor needs gcc |

Usage is under 1.5 node-hours in total.

## Files

- Code: `gpu/gen.py`, `gpu/job.sh`, `gpu/compare.py`
- Per-run JSON (tokens, per-step hashes, timings, versions, host): `gpu/results/`
- Cluster copy: `$WORK/consensus/q6-recheck/`

## Not verified

- Cross-GPU-model agreement (A100 vs H100), or A100-40GB vs A100-80GB.
- Tensor-parallel runs.
- Sampling with a seed.
- Batch sizes other than 1 and 8.
- Batch-invariant mode on Hopper, where vLLM documents support.
- The Polaris HF node's driver version. `gpu.txt` was overwritten by the vLLM job; the 580.65.06
  reading comes from node x3003c0s25b1n0.
