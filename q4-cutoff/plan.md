# Q4 plan

Claim under test: a model trained only on text from before year Y, with no post-Y knowledge in
any training stage and no menu of assumptions, derives a result that overturned the consensus
after Y.

## Runs

| Cutoff | Targets held out | Models | Node-hours |
|---|---|---|---|
| 1900 | quanta (Planck 1900, Einstein 1905), special relativity (1905) | 1B ×2 seeds, 3B | 58 + 428 |
| 1880 | same; Michelson–Morley null (1887) becomes an observation | 1B ×2 seeds, 3B | 58 + 428 |
| 1905 | equivalence principle (1907), Bohr atom (1913) | 1B ×2 seeds, 3B | 58 + 428 |
| 1915 | positive control: SR and quanta are in the corpus | 1B ×2 seeds, 3B | 58 + 428 |
| 1900 | leak-injection control (below) | 1B | 29 |
| all | FSDP port and 3B pilot | — | 30 |
| all | SFT, checker RL, evaluation sampling | — | 150 |
| | **Total** | | **2,153** |

1B = nanochat d20 (0.90B params) on 20B tokens. 3B = d34 (3.29B, GPT-1900's size) on 66B tokens,
Chinchilla. The audited 1900 corpus holds ~40–50B tokens, so the 3B run repeats data 1.3–1.6×,
and 1880 (~25B) ~2.6×; repetition up to 4 epochs costs little (Muennighoff et al. 2023).

1900 runs first: the 1B model gates the 3B one. Each cutoff gets its own tokenizer and its own
audited corpus (`corpus.md`). Cross-cutoff comparisons use matched model size and tokens.

## Post-training without leaks

GPT-1900 leaked through every stage after pretraining (`prior.md`). Rules here:

- No text written after the cutoff enters any stage. No modern-LLM-written SFT data, no modern-LLM
  judge as reward, no nanochat default SFT mixes (SmolTalk etc.).
- SFT data: worked problems and solutions from pre-cutoff textbooks and examination papers
  (Cambridge Mathematical Tripos problems with solutions, Routh, Todhunter, Maxwell's *Treatise*
  exercises), dated by the same rules as the corpus. Format: problem → derivation → `ANSWER:` line.
- RL (optional, after SFT): reward from the programmatic checker only, on pre-cutoff problems
  only. The target discoveries never appear as RL tasks.

## Evaluation

Open-ended derivation prompts. Each gives observations or data, no assumption list, no named
principle, and asks for a law or a model that accounts for them.

| Task | Prompt gives | Checker accepts |
|---|---|---|
| Black-body | Measured u(ν,T) tables at 4 temperatures (Lummer–Pringsheim, Rubens–Kurlbaum values) | A closed form fitting all tables within 3% (sympy + least squares, ≤2 fitted constants), with finite total energy. Planck's law passes; Wien and Rayleigh–Jeans fail |
| Photoelectric | Tables of stopping potential vs frequency and intensity | A law with max energy linear in frequency, independent of intensity, threshold at nonzero frequency; slope fitted to data |
| Moving frames | Maxwell's equations; null result of the interferometer; the question "how do coordinates of a moving observer relate?" | A transformation leaving the wave equation invariant and reducing to Galilean at v→0 (symbolic check). Lorentz transformation passes |
| Simultaneity | Light-signal synchronisation setup, no stated postulates | Correct order of events in the moving frame, checked by computation from the model's own transformation |

Grading is code: sympy for the symbolic tasks, numeric fit for the data tasks. A small extractor
parses the `ANSWER:` line; an LLM is never the grader. Each task has 10 paraphrases; we report
pass@1, pass@10, pass@1000 with temperature 1.0, and keep every sample.

Controls:

- **Enumerator baseline.** A symbolic-regression search over the same grammar of expressions,
  given the same data, with the same sample budget. A model result counts only above this.
- **Positive control.** The 1915 model on the same prompts; it has read the answers.
- **Pre-cutoff control tasks.** Results known before the cutoff (Wien's displacement law 1893,
  Stefan–Boltzmann 1879/1884) in the same format. A model that fails these is too weak to judge.
- **Leak-injection control.** A 1B 1900 model trained with 0.1% planted post-1900 physics text
  calibrates how much leakage lifts the scores.

## Falsification

The claim fails if, with the leak audit passing:

1. the 1900 3B model's pass@1000 on a target task is not above the enumerator baseline; or
2. the 1880 model scores the same as the 1900 model on the targets (then the prompt data, not
   the era's knowledge, carry the result); or
3. success disappears when prompts are paraphrased (pass@1000 across paraphrases drops to the
   baseline); or
4. the leak-injection control shows that the 0.1% leak the audit misses lifts scores by as much as
   the observed result.

Support requires a checker-verified derivation above baseline at 1900, absent or weaker at 1880,
stable across paraphrases.

## Throughput pilot

Polaris debug queue, 2026-11-21, nanochat `92d63d4` (torch 2.9.1+cu128, FA3 from
`kernels-community/flash-attn3`, bf16, no FP8 on A100). Tokenizer: 32k BPE on 1B chars of
GPT-1900 corpus shard 5; training data: the same shard. Batch 524,288 tokens, seq 2048.
Logs: `pilot/logs/`, on Polaris `$WORK/consensus/q4-cutoff/logs/`.

| Job | Nodes | Model | Params | Micro-batch | tok/s total | tok/s/node | MFU |
|---|---|---|---|---|---|---|---|
| 7874657 | 1 | d20 | 0.90B | 8 | 243,938 | 243,938 | 56% |
| 7874657 | 1 | d26 | 1.68B | 4 | 115,414 | 115,414 | 55% |
| 7874668 | 2 | d26 | 1.68B | 4 | 184,632 | 92,316 | 44% |
| 7874657 | 1 | d34 | 3.29B | 1 | OOM | — | — |
| 7874668 | 2 | d34 | 3.29B | 2 | OOM | — | — |

Findings:

- One node sustains 6.95e14 FLOP/s (nanochat's FLOP count), 56% of A100 bf16 peak.
- Two nodes reach 80% of single-node rate per node. The aws-ofi-nccl plugin runs with GPUDirect
  RDMA disabled ("Could not disable CUDA API usage for HMEM"); fixing that is the first lever.
- d34 does not fit on A100-40GB: nanochat replicates fp32 weights and gradients on every rank
  (26 GB before activations). The 3B runs need FSDP (ZeRO-3) or bf16 weights with fp32 master
  shards. Budgeted above as a 30 node-hour port.

Estimate: node-hours = FLOPs/token × tokens / (5.5e14 FLOP/s/node), the 2-node rate.

| Model | FLOPs/token | Tokens | Node-hours at 1 node rate | at 2-node rate |
|---|---|---|---|---|
| 1B (d20) | 2.89e9 | 20B | 23 | **29** |
| 1.7B (d26) | 5.99e9 | 34B | 81 | 103 |
| 3B (d34) | 1.28e10 | 66B | 339 | **428** |
| GPT-1900 replica (d34) | 1.28e10 | 22B | 113 | 143 |

Pilot cost: 0.63 node-hours (4 jobs, including two aborted on a triton compiler and an OOM fix).

## Schedule against the allocation

The plan uses 2,153 Polaris node-hours; the rest of the allocation stays in reserve for reruns, a second 3B seed at 1900 (428) and the 1915 3B if the first
three disagree.

| Window | Work |
|---|---|
| Nov 22 – Dec 1 | Audited 1900 corpus (AmericanStories + BL first), FSDP port, 1900 1B ×2 |
| Dec 2 – Dec 10 | Checker and eval harness; 1880/1905/1915 1B; leak-injection control |
| Dec 11 – Dec 31 | 3B at 1900 and 1880 (16 nodes, ~27 h wall each), then 1905 and 1915 |
| Jan 1 – Jan 10 | Post-training, evaluation, reserve |
