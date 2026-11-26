"""Run prompts.jsonl through a Claude model with the Message Batches API (50% price).

Two short commands, no long-running process:
  submit  -- send the next chunk of unfinished jobs as one batch, unless its projected cost
             would push the shared ledger (spend.jsonl) past --cap dollars
  collect -- for each pending batch that has ended, write rows (same format as run.py) to its
             --out file and its billed tokens and dollar cost to spend.jsonl
"""
import argparse, json, os, time
import anthropic

# $/1M tokens, standard API rates (claude-api skill, cached 2026-11-03); batches bill half.
PRICE = {"claude-fable-5-2": (8, 40), "claude-opus-5-5": (4, 20), "claude-sonnet-5-5": (2, 10)}
HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER, PENDING = os.path.join(HERE, "spend.jsonl"), os.path.join(HERE, "out", "claude-pending.json")


def cost(model, tin, tout):
    pin, pout = PRICE[model]
    return 0.5 * (tin * pin + tout * pout) / 1e6


def load(path, default):
    return json.load(open(path)) if os.path.exists(path) else default


def ledger():
    return [json.loads(l) for l in open(LEDGER)] if os.path.exists(LEDGER) else []


def client():
    return anthropic.Anthropic()  # reads ANTHROPIC_API_KEY


def submit(a):
    pending = load(PENDING, {})
    rows = [json.loads(l) for l in open(a.prompts)]
    if a.items:
        keep = sorted({r["item"] for r in rows})[: a.items]
        rows = [r for r in rows if r["item"] in keep]
    done = {(d["item"], d["cond"], d["sample"]) for d in map(json.loads, open(a.out))} if os.path.exists(a.out) else set()
    inflight = {tuple(j) for p in pending.values() if p["out"] == a.out for j in p["jobs"]}
    jobs = [(r["item"], r["cond"], k) for k in range(a.n) for r in rows
            if (r["item"], r["cond"], k) not in done | inflight][: a.chunk]
    if not jobs:
        print(f"{a.name}: nothing to submit"); return
    seen = [e for e in ledger() if e["model"] == a.model and e["effort"] == a.effort]
    n_ok = sum(e["requests"] - e["errored"] for e in seen)
    per = sum(e["out"] for e in seen) / n_ok if n_ok else a.est_out
    proj = cost(a.model, 300 * len(jobs), per * len(jobs))
    committed = sum(e["usd"] for e in ledger()) + sum(p["proj"] for p in pending.values())
    if committed + proj > a.cap:
        print(f"{a.name}: stop, committed ${committed:.2f} + projected ${proj:.2f} > cap ${a.cap:.2f}"); return
    prompt = {(r["item"], r["cond"]): r["prompt"] for r in rows}
    reqs = [{"custom_id": f"j{i}", "params": {
                "model": a.model, "max_tokens": a.max_tokens,
                "thinking": {"type": "adaptive"}, "output_config": {"effort": a.effort},
                "messages": [{"role": "user", "content": prompt[(it, c)]}]}}
            for i, (it, c, k) in enumerate(jobs)]
    b = client().messages.batches.create(requests=reqs)
    stamps = {r.get("manifest") for r in rows}
    assert len(stamps) == 1, "prompts file mixes item manifests"
    pending[b.id] = {"model": a.model, "name": a.name, "effort": a.effort, "out": a.out, "jobs": jobs, "proj": round(proj, 4),
                     "manifest": stamps.pop()}
    json.dump(pending, open(PENDING, "w"))
    print(f"{a.name}: batch {b.id}, {len(jobs)} requests, projected ${proj:.2f} at {per:.0f} out tok/request")


def collect(a):
    pending, c = load(PENDING, {}), client()
    for bid, p in list(pending.items()):
        b = c.messages.batches.retrieve(bid)
        if b.processing_status != "ended":
            print(f"{p['name']}: {bid} {b.processing_status} {b.request_counts}"); continue
        tin = tout = err = 0
        with open(p["out"], "a") as f:
            for res in c.messages.batches.results(bid):
                it, cond, k = p["jobs"][int(res.custom_id[1:])]
                if res.result.type != "succeeded":
                    err += 1; continue
                m = res.result.message
                tin += m.usage.input_tokens; tout += m.usage.output_tokens
                f.write(json.dumps({"model": p["name"], "item": it, "cond": cond, "sample": k,
                                    "text": "".join(bl.text for bl in m.content if bl.type == "text"),
                                    "finish": {"max_tokens": "length", "refusal": "refusal"}.get(m.stop_reason, "stop"),
                                    "ntok": m.usage.output_tokens,
                                    **({"manifest": p["manifest"]} if p.get("manifest") else {})}) + "\n")
        usd = cost(p["model"], tin, tout)
        with open(LEDGER, "a") as f:
            f.write(json.dumps({"batch": bid, "model": p["model"], "effort": p["effort"], "requests": len(p["jobs"]),
                                "errored": err, "in": tin, "out": tout, "usd": round(usd, 4),
                                "time": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
        del pending[bid]
        json.dump(pending, open(PENDING, "w"))
        print(f"{p['name']}: {bid} ended, {len(p['jobs']) - err} ok, {err} errored, out {tout} tok, ${usd:.2f}")
    print(f"ledger ${sum(e['usd'] for e in ledger()):.2f}; pending {len(pending)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["submit", "collect"])
    ap.add_argument("--model", choices=sorted(PRICE))
    ap.add_argument("--name")
    ap.add_argument("--prompts", default=os.path.join(HERE, "prompts.jsonl"))
    ap.add_argument("--out")
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--items", type=int, default=0, help="first N items only (0 = all)")
    ap.add_argument("--effort", default="high")
    ap.add_argument("--max-tokens", type=int, default=64000)
    ap.add_argument("--chunk", type=int, default=100)
    ap.add_argument("--cap", type=float, help="total dollars across spend.jsonl plus pending projections")
    ap.add_argument("--est-out", type=float, default=8000, help="output tokens per request until measured")
    a = ap.parse_args()
    if a.cmd == "submit" and not (a.model and a.name and a.out and a.cap):
        ap.error("submit needs --model --name --out --cap")
    submit(a) if a.cmd == "submit" else collect(a)


if __name__ == "__main__":
    main()
