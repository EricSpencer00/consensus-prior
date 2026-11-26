"""Run prompts.jsonl through one model with vLLM offline. Writes raw completions as JSONL."""
import argparse, json, os, time
from vllm import LLM, SamplingParams


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--prompts", default="prompts.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--tp", type=int, default=4)
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=8192)
    ap.add_argument("--max-len", type=int, default=16384)
    ap.add_argument("--base", action="store_true", help="base model: raw completion after 'GIVE UP:'")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--gpu-util", type=float, default=0.92)
    ap.add_argument("--eager", action="store_true")
    ap.add_argument("--pp", type=int, default=1)
    ap.add_argument("--mistral", action="store_true", help="load Mistral-native consolidated weights")
    ap.add_argument("--backend", default=None, help="ray for multi-node")
    ap.add_argument("--no-weight-track", action="store_true", help="skip vLLM's loaded-weights check (Qwen3.8-Flash-Next: padding shard is never in the checkpoint)")
    ap.add_argument("--chunk", type=int, default=250, help="prompts per generate call")
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(a.prompts)]
    if a.limit:
        rows = rows[: a.limit]
    done = {(d["item"], d["cond"]) for d in map(json.loads, open(a.out))} if os.path.exists(a.out) else set()
    rows = [r for r in rows if (r["item"], r["cond"]) not in done]
    llm = LLM(model=a.model, tensor_parallel_size=a.tp, max_model_len=a.max_len, gpu_memory_utilization=a.gpu_util, enforce_eager=a.eager, seed=0,
              pipeline_parallel_size=a.pp, distributed_executor_backend=a.backend,
              **({"tokenizer_mode": "mistral", "config_format": "mistral", "load_format": "mistral"} if a.mistral else {}),
              **({"model_loader_extra_config": {"enable_weights_track": False}} if a.no_weight_track else {}))
    sp = SamplingParams(n=a.n, temperature=a.temperature, top_p=0.95, max_tokens=a.max_tokens, seed=0,
                        stop=["\n"] if a.base else None)
    t0 = time.time()
    for i in range(0, len(rows), a.chunk):  # chunks append to --out, so a killed job resumes
        part = rows[i: i + a.chunk]
        if a.base:
            outs = llm.generate([r["prompt"] + "\n\nAnswer.\nGIVE UP:" for r in part], sp)
        else:
            outs = llm.chat([[{"role": "user", "content": r["prompt"]}] for r in part], sp)
        with open(a.out, "a") as f:
            for r, o in zip(part, outs):
                for k, c in enumerate(o.outputs):
                    text = ("GIVE UP:" + c.text) if a.base else c.text
                    f.write(json.dumps({"model": a.name, "item": r["item"], "cond": r["cond"], "sample": k,
                                        "text": text, "finish": c.finish_reason, "ntok": len(c.token_ids), **({"manifest": r["manifest"]} if "manifest" in r else {})}) + "\n")
    print(f"{a.name}: {len(rows)} prompts x {a.n} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
