# compare.py OUTDIR_A [OUTDIR_B]: bitwise comparison table of gen.py outputs
import json, sys, os, itertools
def load(d, mode, r):
    p = f"{d}/{mode}_{r}.json"
    return json.load(open(p)) if os.path.exists(p) else None
def cmp(a, b):
    tok = sum(x == y for x, y in zip(a["tokens"], b["tokens"]))
    steps = same = 0; firstdiv = []
    for ha, hb, ta, tb in zip(a["logit_hash"], b["logit_hash"], a["tokens"], b["tokens"]):
        n = min(len(ha), len(hb)); steps += n; same += sum(x == y for x, y in zip(ha[:n], hb[:n]))
        d = next((i for i, (x, y) in enumerate(zip(ta, tb)) if x != y), None)
        if d is not None: firstdiv.append(d)
    return f"{tok}/8 | {same}/{steps} | {min(firstdiv) if firstdiv else '-'}"
dirs = sys.argv[1:]
name = lambda d: os.path.basename(d.rstrip('/')).split('-')[0]
print("| comparison | identical token seqs | bitwise-identical logit steps | earliest token divergence |")
print("|---|---|---|---|")
for mode in ("hf", "vllm", "vllm-bi", "vllm-bi-eager"):
    for d in dirs:
        r1, r2 = load(d, mode, 1), load(d, mode, 2)
        if not r1: print(f"| {mode} {name(d)} | failed | | |"); continue
        for bs in ("bs1", "bs8"):
            if r2: print(f"| {mode} {name(d)} {bs}: run1 vs run2 | {cmp(r1[bs], r2[bs])} |")
        print(f"| {mode} {name(d)} run1: bs1 vs bs8 | {cmp(r1['bs1'], r1['bs8'])} |")
    if len(dirs) == 2:
        a, b = load(dirs[0], mode, 1), load(dirs[1], mode, 1)
        if a and b:
            for bs in ("bs1", "bs8"):
                print(f"| {mode} {bs}: {name(dirs[0])} vs {name(dirs[1])} | {cmp(a[bs], b[bs])} |")
print()
for d in dirs:
    for mode in ("hf", "vllm", "vllm-bi", "vllm-bi-eager"):
        r = load(d, mode, 1)
        if r: print(name(d), mode, r["versions"], {k: round(r[k]["time"], 1) for k in ("bs1", "bs8")})
# cross-engine token agreement
for d in dirs:
    h, v = load(d, "hf", 1), load(d, "vllm", 1)
    if h and v:
        for bs in ("bs1", "bs8"):
            print(name(d), bs, "hf vs vllm identical token seqs:", sum(x == y for x, y in zip(h[bs]["tokens"], v[bs]["tokens"])), "/8")
