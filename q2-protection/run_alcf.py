"""Run prompts through an ALCF Inference Endpoint (free, Globus auth). Same rows as run.py; resumes from --out.

The access token is read from --token-file on every request, so it can be refreshed while running.
"""
import argparse, http.client, json, os, threading, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

API = "https://inference-api.alcf.anl.gov/resource_server/{}/api/v1/chat/completions"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cluster", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--prompts", default="prompts_rep.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=32000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--token-file", default=os.path.expanduser("~/.alcf-inference-token"))
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(a.prompts)]
    done = {(d["item"], d["cond"], d["sample"]) for d in map(json.loads, open(a.out))} if os.path.exists(a.out) else set()
    jobs = [(r, k) for k in range(a.n) for r in rows if (r["item"], r["cond"], k) not in done]
    lock, f, stats = threading.Lock(), open(a.out, "a"), {"ok": 0, "err": 0}

    def call(job):
        r, k = job
        body = json.dumps({"model": a.model, "messages": [{"role": "user", "content": r["prompt"]}],
                           "max_tokens": a.max_tokens, "temperature": a.temperature, "top_p": 0.95,
                           "stream": True, "stream_options": {"include_usage": True}}).encode()
        for attempt in range(8):
            req = urllib.request.Request(API.format(a.cluster), body, {
                "Authorization": "Bearer " + open(a.token_file).read().strip(), "Content-Type": "application/json"})
            t1 = time.time()
            try:
                # Streaming keeps the gateway from timing out on long reasoning.
                text, finish, ntok = [], None, None
                for line in urllib.request.urlopen(req, timeout=600):
                    line = line.decode().strip()
                    if not line.startswith("data:") or line == "data: [DONE]":
                        continue
                    d = json.loads(line[5:])
                    for c in d.get("choices") or []:
                        text.append((c.get("delta") or {}).get("content") or "")
                        finish = c.get("finish_reason") or finish
                    if d.get("usage"):
                        ntok = d["usage"]["completion_tokens"]
                if finish is None:
                    raise ValueError("stream ended without finish_reason")
                if "[ERROR] Error:" in "".join(text):  # the gateway writes its own errors into the stream
                    raise ValueError("gateway error in stream: " + "".join(text)[-120:])
                row = {"model": a.name, "item": r["item"], "cond": r["cond"], "sample": k,
                       "text": "".join(text), "finish": finish, "ntok": ntok, **({"manifest": r["manifest"]} if "manifest" in r else {})}
                with lock:
                    f.write(json.dumps(row) + "\n"); f.flush(); stats["ok"] += 1
                return
            except (urllib.error.URLError, OSError, http.client.HTTPException, KeyError, ValueError) as e:  # resets included
                msg = f"HTTP {e.code} {e.read().decode()[:120]!r}" if isinstance(e, urllib.error.HTTPError) else repr(e)[:200]
                print(f"retry {attempt} item {r['item']} {r['cond']} {k} after {time.time() - t1:.0f}s: {msg}", flush=True)
                time.sleep(min(600, 15 * 2 ** attempt))
        with lock:  # lost requests go to a side file so they are counted, not silently missing
            stats["err"] += 1
            with open(a.out.replace(".jsonl", ".fail.jsonl"), "a") as g:
                g.write(json.dumps({"item": r["item"], "cond": r["cond"], "sample": k}) + "\n")

    t0 = time.time()
    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(call, jobs))
    print(f"{a.name}: {stats['ok']} ok, {stats['err']} failed of {len(jobs)} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
