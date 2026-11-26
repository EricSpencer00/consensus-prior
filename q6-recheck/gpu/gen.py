# Greedy generation, record tokens and logits hashes. Usage: gen.py {hf|vllm|vllm-bi|vllm-bi-eager} OUTDIR
import hashlib, json, os, sys, time
import numpy as np
os.environ.setdefault("HF_HUB_OFFLINE", "1")
MODEL = "meta-llama/Llama-3.1-8B-Instruct"
N_NEW = 128
EOS = {128001, 128008, 128009}
PROMPTS = [
    "Explain why the sky is blue in three sentences.",
    "Write a Python function that checks whether a number is prime.",
    "What is the capital of Australia, and why is it not Sydney?",
    "Summarize the causes of the First World War.",
    "Prove that the square root of 2 is irrational.",
    "List five uses of a paperclip other than holding paper.",
    "Translate 'the quick brown fox jumps over the lazy dog' into French and German.",
    "Describe the difference between TCP and UDP.",
]
mode, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
h = lambda a: hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()[:16]
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained(MODEL)
chats = [tok.apply_chat_template([{"role": "user", "content": p}], tokenize=False, add_generation_prompt=True) for p in PROMPTS]
res = {"mode": mode, "host": os.uname().nodename}

if mode == "hf":
    import torch
    from transformers import AutoModelForCausalLM
    res["versions"] = {"torch": torch.__version__, "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(0)}
    tok.padding_side = "left"; tok.pad_token = tok.eos_token
    m = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16).cuda().eval()
    def run(batch):
        enc = tok(batch, return_tensors="pt", padding=True, add_special_tokens=False).to("cuda")
        with torch.no_grad():
            g = m.generate(**enc, max_new_tokens=N_NEW, do_sample=False, temperature=None, top_p=None,
                           output_logits=True, return_dict_in_generate=True, pad_token_id=tok.eos_token_id)
        L = torch.stack(g.logits, 1).float().cpu().numpy()  # [B, T, V]
        seqs = g.sequences[:, enc.input_ids.shape[1]:].cpu().numpy()
        rows = []
        for i in range(len(batch)):
            t = seqs[i].tolist()
            n = next((j + 1 for j, x in enumerate(t) if x in EOS), len(t))
            rows.append((t[:n], L[i, :n]))
        return rows
    for bs in (1, 8):
        t = time.time(); rows = []
        for i in range(0, 8, bs):
            rows += run(chats[i:i + bs])
        res[f"bs{bs}"] = {"time": time.time() - t,
                          "tokens": [r[0] for r in rows],
                          "logit_hash": [[h(r[1][s]) for s in range(r[1].shape[0])] for r in rows]}
        np.save(f"{out}/hf_bs{bs}_run{os.environ.get('RUN','0')}_logits.npy", np.stack([np.stack([r[1][0], r[1][-1]]) for r in rows]))
else:
    os.environ["VLLM_ENABLE_V1_MULTIPROCESSING"] = "0"  # in-process engine; no spawn
    if mode.startswith("vllm-bi"):
        os.environ["VLLM_BATCH_INVARIANT"] = "1"; os.environ["VLLM_ATTENTION_BACKEND"] = "FLASH_ATTN"
    import torch, vllm
    from vllm import LLM, SamplingParams
    res["versions"] = {"torch": torch.__version__, "cuda": torch.version.cuda, "vllm": vllm.__version__, "gpu": torch.cuda.get_device_name(0)}
    llm = LLM(model=MODEL, dtype="bfloat16", max_model_len=2048, gpu_memory_utilization=0.8, seed=0, max_logprobs=20,
              enforce_eager=mode.endswith("eager"), enable_prefix_caching=not mode.startswith("vllm-bi"))
    ids = [{"prompt_token_ids": tok(c, add_special_tokens=False).input_ids} for c in chats]  # same tokens as HF
    sp = SamplingParams(temperature=0.0, max_tokens=N_NEW, logprobs=20, ignore_eos=False)
    for bs in (1, 8):
        t = time.time(); outs = []
        for i in range(0, 8, bs):
            outs += llm.generate(ids[i:i + bs], sp, use_tqdm=False)
        toks, lp_hash, lp_first = [], [], []
        for o in outs:
            c = o.outputs[0]; toks.append(list(c.token_ids))
            steps = [np.array(sorted((k, v.logprob) for k, v in d.items()), dtype=np.float64) for d in c.logprobs]
            lp_hash.append([h(s) for s in steps]); lp_first.append(steps[0].tolist())
        res[f"bs{bs}"] = {"time": time.time() - t, "tokens": toks, "logit_hash": lp_hash, "top20_step0": lp_first}
json.dump(res, open(f"{out}/{mode}_{os.environ.get('RUN','0')}.json", "w"))
print("done", mode, {k: res[k]["time"] for k in ("bs1", "bs8")})
