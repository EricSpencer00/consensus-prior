# Q6 prior work: incremental re-verification and bitwise re-execution

Tags: **[P]** number read in the primary source; **[S]** abstract or secondary source;
**[U]** not found in a primary source.

## 1. Checked compilers and binaries re-run in full

| System | What is checked | Re-check cost | Incremental? |
|---|---|---|---|
| CompCert (Leroy, JAR 2009) | Coq proof of the compiler; untrusted passes (register allocation, parser) checked by verified validators on every compile | Proof: ~37k lines Coq, ~7.5 min CPU on 2009 hardware [S]. Per-compile validator cost unpublished [U] | Proof build per file via make. Validators re-run on every compile, every function, no cache |
| SepCompCert (Kang et al., POPL 2016) | Separate compilation correctness for CompCert | Port: <2 person-months [S] | Per-file correctness composes at link; no result caching |
| CakeML (Tan et al., JFP 2019) | Compiler bootstrapped inside HOL4 | ~9 h translation + 24–30 h in-logic evaluation, one laptop [P] | No. HOL4 rebuilds whole theories; bootstrap is monolithic. Uses an external allocator plus a verified validator because in-logic allocation was infeasible |
| seL4 binary TV (Sewell, Myreen, Klein, PLDI 2013) | ARM binary refines C, per function, via decompilation to HOL4 + SMT | gcc -O1: 260 pairs, 59 min; -O2: 225 pairs, 4 h 23 min, 18 failed, 62 aborted; proof-producing decompilation +6–8 h [P] | Per function, but no cache across kernel versions: every build re-runs |
| seL4 l4v proofs | Isabelle refinement proofs | CI "Proofs" ~3 h per run [S]; 4–16 GB RAM, ~8 cores [P] | Isabelle session/heap granularity (coarse) |
| Alive2 (Lopes et al., PLDI 2021) | LLVM IR refinement per pass per function | LLVM unit tests ~2.5 h on 8 cores; SQLite3 -O3: 12.2k pairs, 6.37 h, 2,314 validated, 2,102 timeouts; bzip2: 2.2k pairs, 1.26 h [P] | Skips pairs unchanged by a pass within one run. No cache across runs |
| Necula TV (PLDI 2000, gcc) | Per-pass equivalence | Validation ~4x the pass, ~8x with dump/parse; false alarms up to ~10% of functions [P] | No; memoizing solver calls proposed as future work |
| Proof-carrying code (Necula, POPL 1997 / OSDI 1996) | Safety proof shipped with binary | Check 1–3 ms per packet filter; proof ~3x code size [S] | Check once per binary, fresh per version; no cross-version reuse |

## 2. Incremental checking exists for proofs and source-level verifiers

| System | Granularity | Measured gain |
|---|---|---|
| Lean 4 / Lake | Module (.olean, trace hashes). Since 4.9, in-file snapshots per declaration and tactic step. Module system (Mathlib, Nov 2025): edits to private content do not rebuild importers [S] | Mathlib full build Nov 2023, M1: 1 h 02 m wall, 21,723 s user [S]. `lake exe cache get`: 2–3 min, trusts CI with no local check [S]. Measured here in `baseline.md` |
| Rocq `-vos`/`-vok`, async (Barras, Tankink, Tassi, ITP 2015) | Statement vs opaque proof; parallel proofs | No numbers in abstract [S] |
| iCoq (Çelik, Palmskog, Gligoric, ASE 2017) | Definitions, lemmas, proofs | Up to 10x over from-scratch, 3x over make [S] |
| piCoq (ISSTA 2018) | iCoq + 4-way parallel | Up to 28.6x over from-scratch, 2.8x over make [S] |
| Boogie/Dafny caching (Leino, Wüstholz, CAV 2015) | Procedure checksums + Merkle-style dependency checksums; fine-grained per assertion | Basic cache >10x on IDE sessions (session 3: 13,978 s → 1,735 s); fine-grained adds up to 42%, avg 17% [P] |
| Verification modulo versions (Logozzo et al., PLDI 2014) | Report only alarms the new version introduces | Reduction figure [U] |
| Regression verification (Godlin, Strichman), SymDiff, DAC (Lahiri et al., FSE 2013) | Equivalence or relative correctness of two versions | No re-check cost figures gathered [U] |

## 3. Trusted caches without certificates

Bazel's action cache keys on a digest of command, inputs and environment; the docs warn that
tools outside the workspace are not in the key and that caches get poisoned [P]. Nix
content-addressed derivations (RFC 62, experimental) give early cutoff on unchanged outputs [S].
Debian trixie: ~96.5% of amd64 source packages reproducible [S]. Each of these skips work on a
hash match and trusts whoever wrote the cache entry. None carries a checkable reason the cached
output is correct. Mathlib's `cache get` is the same model.

## 4. Deterministic GPU execution

| Source | Result |
|---|---|
| cuBLAS docs | Bitwise run-to-run only for same architecture, same SM count, same toolkit; breaks with multiple streams unless `CUBLAS_WORKSPACE_CONFIG` is set [P] |
| PyTorch `use_deterministic_algorithms` | Errors on CUDA ops with no deterministic kernel (scatter_add_, index_add_, …) [U: docs not fetched] |
| Thinking Machines, He et al., Sept 2025 | Cause is batch-variant kernels, not concurrency per se. Qwen3-235B, T=0, 1,000 completions: 80 unique, first divergence at token 103; batch-invariant kernels: 1 unique. Qwen3-8B, 1,000 seqs: 26 s default vs 55 s deterministic (2.1x), 42 s with better attention (1.6x) [P] |
| SGLang deterministic mode (Sept 2025) | Avg 34% slowdown [S] |
| vLLM `VLLM_BATCH_INVARIANT=1` | Beta; no overhead figure in docs [S] |
| Detent (arXiv 2611.10611) | Batch-invariant at 1.04–1.17x latency; engine modes 1.67–10.3x; not cross-GPU-type [S] |
| LLM-42 (arXiv 2601.17768) | Fast nondeterministic decode, verifier replays in fixed order and rolls back divergent tokens [S] |
| TOPLOC (Ong et al., ICML 2025) | Tolerance-based hashes of top-k activations; 258 B per 32 tokens; validation up to 100x faster than inference [S] |
| EigenAI (arXiv 2602.00182) | Byte-equality re-execution in a TEE; same SKU matches, A100 vs H100 0% [S, snippet] |
| ReproFuse (arXiv 2609.25624) | Linear layers bitwise across Ampere/Ada/Hopper [S] |
| Cankaya (arXiv 2606.00279) | Bit-exact recompute across hardware by emulating rounding, no atomics [S] |

## Gap

1. **Binary side.** Per-function binary validation (seL4 graph-refine, Alive2, Necula), Merkle
   caching of verifier results (Boogie), dependency-based proof selection (iCoq) and hash-keyed
   build caches (Bazel, Nix) all exist. No system combines them: a per-function validation
   certificate keyed on (source hash, target-code hash, callee-summary hashes, validator and
   compiler version), stored in a cache whose entries a checker re-validates cheaply, so a
   rebuild re-validates only functions whose key changed. seL4's binary check (59 min at -O1,
   4.4 h at -O2, plus 6–8 h decompilation) and Alive2 (6.4 h for SQLite) re-run in full on
   every build.
2. **Trust in the cache.** Every incremental system above (Lake, Bazel, Boogie, iCoq) trusts
   that the cache was written honestly and that the dependency key is complete. A missing
   input in the key is a silent false "verified". Nobody states or checks key completeness;
   Bazel's docs name it as a known hole.
3. **Runtime side.** Bitwise determinism is established within one architecture, SM count and
   toolkit (cuBLAS), or within one deployment (Detent). Cross-architecture bitwise agreement
   is shown for linear layers (ReproFuse) or claimed by rounding emulation (Cankaya). No
   published system uses bitwise re-execution of a full LLM generation on a second machine as
   the checker; deployed verifiers require the same SKU (EigenAI) or accept a tolerance
   (TOPLOC).
