"""Derive each assumption's forecasts, score them, compare to the market (consensus).
Inputs: data/markets.csv, data/btc_hourly.csv. Output: data/forecasts.csv, stdout tables."""
import csv, math, random, statistics as st
from bisect import bisect_right

CLIP = 0.01
rows = list(csv.DictReader(open("data/markets.csv")))
hourly = [(int(t), float(c)) for t, c in csv.reader(open("data/btc_hourly.csv")) if t != "t_open"]
T = [t + 3600 for t, _ in hourly]  # candle close times
C = [c for _, c in hourly]

Phi = lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2)))


def t_cdf(x, df=3):  # Student-t CDF, df=3 closed form
    return 0.5 + (math.atan(x / math.sqrt(3)) + x * math.sqrt(3) / (3 + x * x)) / math.pi


def features(t_fc):
    i = bisect_right(T, t_fc) - 1  # last closed candle at or before t_fc
    S = C[i]
    lr = [math.log(C[j] / C[j - 1]) for j in range(i - 720 + 1, i + 1)]
    return S, st.pstdev(lr), st.pstdev(lr[-24:]), math.log(S / C[i - 24])


def assumptions(S, K, h, sd30, sd24, r24):
    x = math.log(S / K); s = sd30 * math.sqrt(h)
    return {
        "random_walk": Phi(x / s),
        "trend": Phi((x + r24 * h / 24) / s),
        "mean_reversion": Phi((x - r24 * h / 24) / s),
        "status_quo": 1.0 if S > K else 0.0,
        "fat_tails": t_cdf(x / (s * math.sqrt(1 / 3))),
        "vol_clustering": Phi(x / (sd24 * math.sqrt(h))),
    }


rec = []
for r in rows:
    t_fc, t_res, K = int(r["t_fc"]), int(r["t_res"]), float(r["strike"])
    S, sd30, sd24, r24 = features(t_fc)
    f = assumptions(S, K, (t_res - t_fc) / 3600, sd30, sd24, r24)
    f["market"] = float(r["p_mkt"])
    rec.append(dict(date=r["date"], strike=K, spot=S, y=int(r["y"]), **f))

NAMES = ["market", "random_walk", "trend", "mean_reversion", "status_quo", "fat_tails", "vol_clustering"]
with open("data/forecasts.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rec[0])); w.writeheader()
    w.writerows({k: (round(v, 5) if isinstance(v, float) else v) for k, v in x.items()} for x in rec)

clip = lambda p: min(1 - CLIP, max(CLIP, p))
logs = lambda p, y: math.log(clip(p) if y else 1 - clip(p))
brier = lambda p, y: (clip(p) - y) ** 2


def by_day(sample):
    d = {}
    for x in sample: d.setdefault(x["date"], []).append(x)
    return d


def report(name, sample, B=5000):
    days = by_day(sample); keys = sorted(days)
    # per-day sums so the bootstrap resamples days (strikes on one day share one outcome path)
    L = {n: [sum(logs(x[n], x["y"]) for x in days[k]) for k in keys] for n in NAMES}
    Bs = {n: [sum(brier(x[n], x["y"]) for x in days[k]) for k in keys] for n in NAMES}
    N = len(sample); D = len(keys)
    rng = random.Random(0); boot = {n: [] for n in NAMES}; top = {n: 0 for n in NAMES}
    for _ in range(B):
        idx = [rng.randrange(D) for _ in range(D)]
        m = {n: sum(L[n][i] for i in idx) for n in NAMES}
        for n in NAMES: boot[n].append((m[n] - m["market"]) / N)
        best = max((n for n in NAMES if n != "market"), key=m.get); top[best] += 1
    gap = {n: st.mean(abs(x[n] - x["market"]) for x in sample) for n in NAMES}
    print(f"\n## {name}: {N} questions, {D} days, base rate {st.mean(x['y'] for x in sample):.3f}\n")
    print("| forecaster | mean log score | Δ vs market (95% CI) | mean Brier | P(best assumption) | mean abs gap to market |")
    print("|---|---|---|---|---|---|")
    for n in sorted(NAMES, key=lambda n: -sum(L[n])):
        b = sorted(boot[n]); lo, hi = b[int(0.025 * B)], b[int(0.975 * B)]
        print(f"| {n} | {sum(L[n])/N:.4f} | {sum(L[n])/N - sum(L['market'])/N:+.4f} ({lo:+.4f}, {hi:+.4f}) "
              f"| {sum(Bs[n])/N:.4f} | {top[n]/B if n!='market' else float('nan'):.3f} | {gap[n]:.3f} |")
    # posterior credence among assumptions (uniform prior, market excluded)
    tot = {n: sum(L[n]) for n in NAMES if n != "market"}; mx = max(tot.values())
    z = sum(math.exp(v - mx) for v in tot.values())
    print("\nPosterior credence (uniform prior, market excluded): " +
          ", ".join(f"{n} {math.exp(v - mx)/z:.3g}" for n, v in sorted(tot.items(), key=lambda kv: -kv[1])))
    cons = sorted((n for n in NAMES if n != "market"), key=gap.get)
    score = sorted((n for n in NAMES if n != "market"), key=lambda n: -sum(L[n]))
    print("Consensus ranking (closest to market first): " + " > ".join(cons))
    print("Proper-score ranking: " + " > ".join(score))
    return L


# Primary set: one question per day, strike nearest spot at forecast time.
primary = [min(v, key=lambda x: abs(x["strike"] - x["spot"])) for v in by_day(rec).values()]
report("Primary (nearest-the-money strike, one per day)", primary)
report("All strikes (day-block bootstrap)", rec)


def paired(a, b, sample, B=5000):
    days = by_day(sample); keys = sorted(days); D = len(keys)
    d = [sum(logs(x[a], x["y"]) - logs(x[b], x["y"]) for x in days[k]) for k in keys]
    rng = random.Random(1); n = len(sample)
    bs = sorted(sum(d[rng.randrange(D)] for _ in range(D)) / n for _ in range(B))
    return sum(d) / n, bs[int(0.025 * B)], bs[int(0.975 * B)]


def disagreements(sample, thr=0.10):
    print(f"\nQuestions where an assumption departs from the market by more than {thr}:")
    print("| assumption | n | assumption closer to outcome | mean log-score Δ vs market on these |")
    print("|---|---|---|---|")
    for n in NAMES[1:]:
        s = [x for x in sample if abs(x[n] - x["market"]) > thr]
        if not s: continue
        win = sum(abs(clip(x[n]) - x["y"]) < abs(clip(x["market"]) - x["y"]) for x in s)
        dl = st.mean(logs(x[n], x["y"]) - logs(x["market"], x["y"]) for x in s)
        print(f"| {n} | {len(s)} | {win}/{len(s)} | {dl:+.3f} |")


for label, s in [("Primary", primary), ("All strikes", rec)]:
    print(f"\n## Paired log-score differences, {label} (95% day-block bootstrap CI)\n")
    for a, b in [("fat_tails", "random_walk"), ("random_walk", "vol_clustering"), ("trend", "mean_reversion"),
                 ("random_walk", "trend"), ("random_walk", "status_quo")]:
        m, lo, hi = paired(a, b, s)
        print(f"- {a} − {b}: {m:+.4f} ({lo:+.4f}, {hi:+.4f})")
    disagreements(s)
