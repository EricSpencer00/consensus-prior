# Q6 direction

## Question

Make a rebuild re-verify only the functions whose machine code or proof obligation changed,
and make a cache hit carry evidence a small checker validates, rather than trust in whoever
wrote the cache. The cost of re-checking a build should scale with the semantic diff, not with
program size. Every skipped check should reduce to a mechanically checked fact: the inputs the
validator read are a subset of the key that matched.

Three failure modes define the problem:

1. **Full re-run.** seL4 binary validation (59 min at -O1, 4.4 h at -O2), Alive2 (6.4 h for
   SQLite) and CakeML bootstrap (33–39 h) recheck everything on every build (`prior.md`).
2. **Coarse skip.** Mathlib (`baseline.md`) re-checks one module in 14 s after a proof
   edit. After adding one unused lemma to that same module it re-checks 6,840 modules:
   7.8 CPU-hours, 88% of a from-scratch build. Module granularity puts every change at one
   of two extremes.
3. **Unsound skip.** Lake, Bazel, Boogie's cache and iCoq skip work on a key match and assume
   the key is complete. An input missing from the key turns a stale result into a silent
   "verified". No system checks key completeness.

The runtime half has the same shape. `determinism.md` shows greedy decoding is bitwise
reproducible across machines for a fixed (weights, token ids, engine, kernel config, batch,
GPU model), and breaks when the batch changes, even under vLLM's batch-invariant mode on A100.
A re-execution checker has a key, and the key must be complete.

## Thesis

Split search from checking. In Mathlib, elaboration (search) is 96% of build CPU. A kernel
re-check of all 8,312 modules takes 21 minutes on one thread, 3.9% of the build
(`baseline.md`).

Translation validation has the same two phases: it searches for a simulation relation and then
checks it. `prior.md` found no published measurement of how the cost divides between the two.

The design: cache the search output (proof term, simulation witness) untrusted, and re-run
only the checker on units whose key changed.

Incremental verification is sound when the cache key is a **hermetic read set**. Run each
per-unit validation in a sandbox that records every byte it reads: source IR, target code,
callee summaries, validator binary, flags. Key the result on the hash of that recorded set,
and re-check a unit exactly when a byte in its read set changes. Soundness then rests on the
sandbox and the hash function, not on a hand-written dependency list. The same rule covers
GPU re-execution: the read set includes the batch, the kernel selection and the device model.

Precision comes from recording reads at declaration granularity, not file granularity. In the
Mathlib e3 case, an importer that never resolved the name `q6_probe` keeps its key, so 6,839
re-checks drop to zero. Recording a declaration-level read set takes two kinds of reads beyond
"which declarations were used":

- **Negative lookups.** A name that failed to resolve, or an instance that was searched for
  and not found.
- **Index queries.** Simp sets, instance tables and `grind` attributes.

Adding an instance or simp lemma changes the answer to such a query without changing any
declaration the importer used. The research problem is a read set that captures these
queries and that a small checker validates.

## First experiment (≤2 weeks, Linux CPU: hst-bench or a Polaris CPU node)

**Setup**
- Alive2 `alive-tv`, per function and per pass.
- SQLite, built with clang -O2, over 50 consecutive upstream commits.

**Step 1: measure the headroom**
- At every commit, emit the before-pass and after-pass IR for each (function, pass) pair.
- Hash each pair, and count the fraction whose hash changes between adjacent commits.
- That fraction bounds incremental savings from above.
- Prior expectation from cHash: about 80% of compiles are redundant.

**Step 2: build the cache**
- Wrap `alive-tv` in a read-recording sandbox (`strace -e openat,read` or a FUSE layer).
- Key each verdict on SHA-256 of the recorded read set.
- Re-run only pairs whose key changed.

**Step 3: measure**
- Wall time: full Alive2 against cached Alive2 for each commit.
- Fraction of pairs re-checked.
- Verdict agreement between cached and full runs. Target: 100% agreement.
- Fault injection: mutate an input that is absent from a naive key (header, flag, validator
  version). Show that the naive key returns a stale verdict and the read-set key does not.

**Success criteria**
- Over 10x less validation work per commit.
- Zero verdict disagreements across 50 commits.
- A demonstrated stale-hit bug in the naive key that the read-set key closes.

**Runtime follow-up on Sophia**
- Add batch composition and kernel config to the re-execution key.
- Show cross-machine bitwise checks pass for 1,000 generations at batch sizes 1–64 when the
  checker replays the recorded batch, and fail when it does not.
- Run the same test on an H100 to see whether vLLM's batch-invariant mode closes the batch
  term there.
