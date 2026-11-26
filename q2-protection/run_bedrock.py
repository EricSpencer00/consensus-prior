"""Run prompts.jsonl through a Bedrock model. Same output rows as run.py; resumes from --out."""
import argparse, json, threading, time
from concurrent.futures import ThreadPoolExecutor
import boto3
from botocore.config import Config


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--prompts", default="prompts.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--region", default="us-east-2")
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=16000)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(a.prompts)]
    if a.limit:
        rows = rows[: a.limit]
    done = set()
    try:
        done = {(d["item"], d["cond"], d["sample"]) for d in map(json.loads, open(a.out))}
    except FileNotFoundError:
        pass
    jobs = [(r, k) for r in rows for k in range(a.n) if (r["item"], r["cond"], k) not in done]
    br = boto3.client("bedrock-runtime", region_name=a.region,
                      config=Config(read_timeout=900, retries={"max_attempts": 10, "mode": "adaptive"}))
    lock, tok = threading.Lock(), [0, 0]
    f = open(a.out, "a")

    def call(job):
        r, k = job
        resp = br.converse(modelId=a.model, messages=[{"role": "user", "content": [{"text": r["prompt"]}]}],
                           inferenceConfig={"maxTokens": a.max_tokens, "temperature": a.temperature, "topP": 0.95})
        text = "".join(b.get("text", "") for b in resp["output"]["message"]["content"])
        u = resp["usage"]
        row = {"model": a.name, "item": r["item"], "cond": r["cond"], "sample": k, "text": text,
               "finish": "length" if resp["stopReason"] == "max_tokens" else "stop", "ntok": u["outputTokens"], **({"manifest": r["manifest"]} if "manifest" in r else {})}
        with lock:
            f.write(json.dumps(row) + "\n"); f.flush()
            tok[0] += u["inputTokens"]; tok[1] += u["outputTokens"]

    t0 = time.time()
    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(call, jobs))
    print(f"{a.name}: {len(jobs)} completions in {time.time() - t0:.0f}s; tokens in {tok[0]} out {tok[1]}")


if __name__ == "__main__":
    main()
