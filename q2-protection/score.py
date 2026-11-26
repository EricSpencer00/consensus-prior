"""Score Q2 completions against ONE item manifest.

Usage: python3 score.py --items items_rep.jsonl out/<model>.rep.jsonl > results.json
       (Q2_ITEMS=<manifest> selects it too; legacy default: items.jsonl)

Item IDs repeat across cohorts (pilot items.jsonl and replication items_rep.jsonl both start at
q2-000 with different MCS lists), so a row means nothing without its manifest. Rows carry
"manifest" = SHA-256 of the items file they were generated from (gen.py stamps prompts, runners
copy it). Scoring refuses: a stamped row whose SHA differs from the selected manifest; rows with
no stamp unless the manifest was selected explicitly (--items or Q2_ITEMS); an item ID missing
from the manifest; and a repeated (model, item, cond, sample), which is what mixing two cohorts'
outputs for one model produces.

Per sample: parse the last 'GIVE UP:' line -> drop set D.
  valid_min    D is a minimal correction set (in item MCS list)
  valid_nonmin D contains an MCS but is not one (fixes consistency, gives up too much)
  invalid      D hits no MCS-superset (contradiction remains) or is empty
  unparsed     no GIVE UP line
Protection effect for label L in {F (famous), O (obscure)}, per item with targets T0, T1:
  delta_L = 1/2 [ (d(T0|L on T1) - d(T0|L on T0)) + (d(T1|L on T0) - d(T1|L on T1)) ]
where d(T|cond) = share of samples whose drop set contains T. Positive = the named assumption
is kept more often than the same assumption when the name sits on the other target (the swap).
Reported over all parsed samples and over valid-minimal samples only. Net reputation = delta_F - delta_O.
95% CIs: percentile bootstrap over items (10,000 resamples).
"""
import hashlib, json, os, random, re, sys
from collections import defaultdict


class ManifestError(ValueError):
    pass


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_items(path):
    with open(path) as f:
        return {json.loads(l)["id"]: json.loads(l) for l in f}


def load_rows(paths, manifest, explicit):
    """Group rows by model after checking every row belongs to `manifest`."""
    sha, items = sha256(manifest), load_items(manifest)
    by_model, seen = defaultdict(list), set()
    for path in paths:
        with open(path) as f:
            lines = f.readlines()
        for n, l in enumerate(lines, 1):
            r = json.loads(l)
            where = f"{path}:{n}"
            stamp = r.get("manifest")
            if stamp is None and not explicit:
                raise ManifestError(f"{where}: row has no manifest stamp; select the manifest with --items or Q2_ITEMS")
            if stamp is not None and stamp != sha:
                raise ManifestError(f"{where}: row manifest {stamp[:12]} != selected {os.path.basename(manifest)} {sha[:12]}")
            if r["item"] not in items:
                raise ManifestError(f"{where}: item {r['item']} not in {os.path.basename(manifest)}")
            key = (r["model"], r["item"], r["cond"], r["sample"])
            if key in seen:
                raise ManifestError(f"{where}: repeated {key}: outputs from two cohorts or runs mixed for one model")
            seen.add(key)
            by_model[r["model"]].append(r)
    return items, sha, by_model

ID = re.compile(r"\bA(\d+)\b")


def parse(text):
    hits = re.findall(r"GIVE UP:\s*([^\n]*)", text.replace("*", ""))
    if not hits:
        return None
    return frozenset(f"A{m}" for m in ID.findall(hits[-1]))


def classify(item, D):
    if D is None:
        return "unparsed"
    mcs = [frozenset(m) for m in item["mcs"]]
    if D in mcs:
        return "valid_min"
    if any(m < D for m in mcs):
        return "valid_nonmin"
    return "invalid"


def boot(vals, reps=10000, seed=0):
    rng = random.Random(seed)
    n = len(vals)
    if n == 0:
        return None
    means = sorted(sum(rng.choice(vals) for _ in range(n)) / n for _ in range(reps))
    return [round(means[int(0.025 * reps)], 4), round(means[int(0.975 * reps) - 1], 4)]


def summarize(rows, ITEMS):
    cells = defaultdict(list)  # (item, cond) -> list of (cls, D)
    counts = defaultdict(lambda: defaultdict(int))
    for r in rows:
        it = ITEMS[r["item"]]
        D = parse(r["text"])
        c = classify(it, D)
        cells[(r["item"], r["cond"])].append((c, D))
        counts[r["cond"]][c] += 1
    out = {"n_samples": len(rows), "by_cond": {k: dict(v) for k, v in sorted(counts.items())}}
    for subset in ("parsed", "valid_min"):
        for L in ("F", "O"):
            deltas, vs_neutral = {}, []
            for iid, it in ITEMS.items():
                T = it["targets"]

                def d(t, cond):
                    s = [D for c, D in cells.get((iid, cond), []) if (c != "unparsed" if subset == "parsed" else c == "valid_min")]
                    return None if not s else sum(t in D for D in s) / len(s)

                v = [d(T[0], L + "1"), d(T[0], L + "0"), d(T[1], L + "0"), d(T[1], L + "1"), d(T[0], "N"), d(T[1], "N")]
                if None not in v[:4]:
                    deltas[iid] = ((v[0] - v[1]) + (v[2] - v[3])) / 2
                if None not in v:
                    vs_neutral.append(((v[4] - v[1]) + (v[5] - v[3])) / 2)
            key = f"{subset}_{L}"
            dv = list(deltas.values())
            out[key] = {"delta": round(sum(dv) / len(dv), 4) if dv else None, "ci95": boot(dv), "n_items": len(dv),
                        "vs_neutral": round(sum(vs_neutral) / len(vs_neutral), 4) if vs_neutral else None,
                        "vs_neutral_ci95": boot(vs_neutral), "n_items_neutral": len(vs_neutral),
                        "_per_item": deltas}
        F, O = out[f"{subset}_F"].pop("_per_item"), out[f"{subset}_O"].pop("_per_item")
        net = [F[i] - O[i] for i in F if i in O]
        out[f"{subset}_net"] = {"delta": round(sum(net) / len(net), 4) if net else None, "ci95": boot(net), "n_items": len(net)}
    return out


def main(argv):
    manifest, explicit = os.environ.get("Q2_ITEMS"), "Q2_ITEMS" in os.environ
    if argv[:1] == ["--items"]:
        manifest, explicit, argv = argv[1], True, argv[2:]
    items, sha, by_model = load_rows(argv, manifest or "items.jsonl", explicit)
    out = {m: summarize(rs, items) for m, rs in sorted(by_model.items())}
    for v in out.values():
        v["manifest"] = sha
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except ManifestError as e:
        sys.exit(f"score.py: {e}")
