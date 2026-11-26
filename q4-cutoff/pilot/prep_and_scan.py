"""Pilot: scan one pre-1900 shard for post-cutoff canaries, then write nanochat parquet shards.
usage: python prep_and_scan.py IN.parquet OUT_DIR SCAN.json
"""
import json, re, sys, collections
import pyarrow as pa, pyarrow.parquet as pq

src, out_dir, scan_path = sys.argv[1:4]
# Strong canaries: coined or attached to their physics sense after 1900.
STRONG = [r"\bphotons?\b", r"\bspace-time\b", r"\bspacetime\b", r"\bquantum of action\b",
          r"\bPlanck'?s constant\b", r"\btheory of relativity\b", r"\bspecial relativity\b",
          r"\bgeneral relativity\b", r"\bEinstein\b", r"\bLorentz transformation", r"\bBohr\b",
          r"\bHeisenberg\b", r"\bSchr[oö]dinger\b", r"\bquantum mechanics\b", r"\bquantum theory\b",
          r"\bisotopes?\b", r"\bproton\b", r"\bneutron\b", r"\btransistor\b", r"\btelevision\b",
          r"\bWorld War\b", r"\bTitanic\b", r"\bWright brothers\b", r"\bBolshevik", r"\bLeague of Nations\b"]
# Weak canaries: legitimate before 1900 but rise sharply after; tracked, not filtered.
WEAK = [r"\bquant(um|a)\b", r"\brelativity\b", r"\belectrons?\b", r"\bradio-?activ", r"\bX-rays?\b",
        r"\bether\b", r"\baether\b", r"\bMichelson\b", r"\bLorentz\b", r"\bPlanck\b"]
YEAR = re.compile(r"\b19[0-9]{2}\b")
# Lowercase once; substring prefilter (fast), regex only to confirm word boundaries.
ALL = STRONG + WEAK
def key(p):  # longest literal run in the pattern
    lit = re.sub(r"\\b|.\?|\(.*?\)|\[.*?\]|'", " ", p.lower()).replace("-", " ").split()
    return max(lit, key=len)
RXS = [(p, key(p), re.compile(p.lower())) for p in ALL]

pf = pq.ParquetFile(src)
n_docs = n_chars = 0
strong_docs, weak_docs, years = collections.Counter(), collections.Counter(), collections.Counter()
by_source = collections.Counter()
postyear_docs = 0
examples = collections.defaultdict(list)
chunks, shard_i, CH, ROWS_PER_SHARD = [], 0, 8000, 50_000

def flush(final=False):
    global chunks, shard_i
    if not chunks: return
    t = pa.table({"text": chunks})
    pq.write_table(t, f"{out_dir}/shard_{shard_i:05d}.parquet", row_group_size=1024)
    shard_i += 1; chunks = []

for rg in range(pf.num_row_groups):
    t = pf.read_row_group(rg, columns=["text", "year", "title", "source"]).to_pylist()
    for d in t:
        txt = d["text"] or ""
        n_docs += 1; n_chars += len(txt); years[d["year"]] += 1; by_source[d["source"]] += 1
        low = txt.lower(); seen = {}
        for p, k, rx in RXS:
            if k in low:
                m = rx.search(low)
                if m: seen[p] = m.start()
        for p, pos in seen.items():
            if p in STRONG:
                strong_docs[p] += 1
                if len(examples[p]) < 3:
                    examples[p].append({"year": d["year"], "title": (d["title"] or "")[:80], "source": d["source"], "ctx": txt[max(0, pos - 120):pos + 160]})
            else:
                weak_docs[p] += 1
        if len(YEAR.findall(txt)) >= 5: postyear_docs += 1
        for i in range(0, len(txt), CH):
            chunks.append(txt[i:i + CH])
        if len(chunks) >= ROWS_PER_SHARD: flush()
flush()
json.dump({"docs": n_docs, "chars": n_chars, "shards_written": shard_i,
           "year_min": min(years), "year_max": max(years),
           "docs_by_decade": dict(sorted(collections.Counter((y // 10) * 10 for y in years.elements()).items())),
           "docs_by_source": dict(by_source), "docs_with_5plus_19xx_years": postyear_docs,
           "strong_canary_docs": dict(strong_docs), "weak_canary_docs": dict(weak_docs),
           "examples": examples}, open(scan_path, "w"), indent=1, ensure_ascii=False)
print("done", n_docs, n_chars, shard_i)
