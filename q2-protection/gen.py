"""Generate Q2 protection items: theory + contradicting observation, MCSs checked with z3.

Usage: python3 gen.py [--n 50] [--seed 0] > items.jsonl ; prompts written by --prompts.
Needs the z3 binary on PATH (SMT-LIB via stdin).
"""
import argparse, hashlib, itertools, json, random, subprocess

ATOMS = [
    ("the valve is open", "the valve is not open"),
    ("the pump runs", "the pump does not run"),
    ("pressure rises", "pressure does not rise"),
    ("the alarm sounds", "the alarm does not sound"),
    ("the relay closes", "the relay does not close"),
    ("the lamp is lit", "the lamp is not lit"),
    ("the fan spins", "the fan does not spin"),
    ("the tank fills", "the tank does not fill"),
    ("the sensor trips", "the sensor does not trip"),
    ("the motor heats", "the motor does not heat"),
    ("the door locks", "the door does not lock"),
    ("the gauge reads high", "the gauge does not read high"),
    ("the coil is energized", "the coil is not energized"),
    ("the filter clogs", "the filter does not clog"),
]
QTY = ["p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "k"]

# Famous name and a matched invented eponym of the same grammatical form.
NAMES = [
    ("Conservation of Energy", "Conservation of Ledrin"),
    ("Newton's Second Law", "Halvorsen's Second Law"),
    ("Ohm's Law", "Varnum's Law"),
    ("the Second Law of Thermodynamics", "the Second Law of Brekkmann"),
    ("Conservation of Charge", "Conservation of Tavish"),
    ("the Pythagorean Theorem", "the Okonkwo-Lind Theorem"),
    ("Fermat's Little Theorem", "Dasquier's Little Theorem"),
    ("Conservation of Mass", "Conservation of Pellar"),
    ("Kirchhoff's Current Law", "Mirabeau's Current Law"),
    ("the Central Limit Theorem", "the Strand-Iyer Limit Theorem"),
    ("Hooke's Law", "Yarrow's Law"),
    ("Coulomb's Law", "Ferrand's Law"),
]


def z3_sat_table(decls, formulas, obs):
    """Return {frozenset(kept indices): sat} for every subset of formulas, with obs asserted."""
    n = len(formulas)
    lines = list(decls) + [f"(declare-const b{i} Bool)" for i in range(n)]
    lines += [f"(assert (=> b{i} {f}))" for i, f in enumerate(formulas)]
    lines.append(f"(assert {obs})")
    subsets = [frozenset(c) for k in range(n + 1) for c in itertools.combinations(range(n), k)]
    for s in subsets:
        lits = " ".join(f"b{i}" if i in s else f"(not b{i})" for i in range(n))
        lines.append(f"(check-sat-assuming ({lits}))")
    out = subprocess.run(["z3", "-in"], input="\n".join(lines), capture_output=True, text=True, check=True).stdout.split()
    assert len(out) == len(subsets) and set(out) <= {"sat", "unsat"}, out[:5]
    return {s: r == "sat" for s, r in zip(subsets, out)}


def mcs_mus(table, n):
    full = frozenset(range(n))
    sat = [s for s, v in table.items() if v]
    mss = [s for s in sat if not any(s < t for t in sat)]
    mcs = sorted((sorted(full - s) for s in mss), key=lambda d: (len(d), d))
    unsat = [s for s, v in table.items() if not v]
    mus = sorted((sorted(s) for s in unsat if not any(t < s for t in unsat)), key=lambda d: (len(d), d))
    return mcs, mus


# ---- families: each returns (decls, [(smt, text, is_rule)], obs_smt, obs_text) ----

def prop_atoms(rng, k):
    return rng.sample(range(len(ATOMS)), k)


def fam_chain(rng):
    k = rng.randint(3, 5)  # rules in the chain
    a = prop_atoms(rng, k + 1 + 3)
    chain, extra = a[: k + 1], a[k + 1:]
    asm = [(f"a{chain[0]}", f"{ATOMS[chain[0]][0].capitalize()}.", False)]
    for i in range(k):
        asm.append((f"(=> a{chain[i]} a{chain[i+1]})", f"If {ATOMS[chain[i]][0]}, then {ATOMS[chain[i+1]][0]}.", True))
    for j in range(rng.randint(1, 2)):  # distractors off the conflict
        asm.append((f"(=> a{extra[j]} a{extra[j+1]})", f"If {ATOMS[extra[j]][0]}, then {ATOMS[extra[j+1]][0]}.", True))
    used = chain + extra
    return [f"(declare-const a{i} Bool)" for i in used], asm, f"(not a{chain[-1]})", ATOMS[chain[-1]][1].capitalize() + "."


def fam_diamond(rng):
    a = prop_atoms(rng, 7)
    f, p, q, s, z, d1, d2 = a
    T = lambda i: ATOMS[i][0]
    asm = [
        (f"a{f}", T(f).capitalize() + ".", False),
        (f"(=> a{f} a{p})", f"If {T(f)}, then {T(p)}.", True),
        (f"(=> a{p} a{q})", f"If {T(p)}, then {T(q)}.", True),
        (f"(=> a{q} a{z})", f"If {T(q)}, then {T(z)}.", True),
        (f"(=> a{p} a{s})", f"If {T(p)}, then {T(s)}.", True),
        (f"(=> a{s} a{z})", f"If {T(s)}, then {T(z)}.", True),
        (f"(=> a{d1} a{d2})", f"If {T(d1)}, then {T(d2)}.", True),
    ]
    return [f"(declare-const a{i} Bool)" for i in a], asm, f"(not a{z})", ATOMS[z][1].capitalize() + "."


def fam_arith_chain(rng):
    v = rng.sample(QTY, 6)
    x, y, zz, w, d1, d2 = v
    cw, cz, m = rng.randint(2, 9), rng.randint(2, 9), rng.randint(2, 4)
    pred = m * cw + cz
    obs = pred + rng.choice([-3, -2, -1, 1, 2, 3])
    asm = [
        (f"(= {w} {cw})", f"{w} = {cw}.", False),
        (f"(= {zz} {cz})", f"{zz} = {cz}.", False),
        (f"(= {y} (* {m} {w}))", f"{y} = {m}·{w}.", True),
        (f"(= {x} (+ {y} {zz}))", f"{x} = {y} + {zz}.", True),
        (f"(= {d1} (+ {d2} 1))", f"{d1} = {d2} + 1.", True),
    ]
    decls = [f"(declare-const {c} Real)" for c in v]
    return decls, asm, f"(= {x} {obs})", f"{x} is measured to be {obs}."


def fam_arith_diamond(rng):
    v = rng.sample(QTY, 6)
    x, y, zz, w, d1, d2 = v
    c, m, n2, a = rng.randint(2, 6), rng.randint(2, 4), rng.randint(5, 7), rng.randint(1, 9)
    b = m * c + a - n2 * c  # both paths predict the same x
    pred = m * c + a
    obs = pred + rng.choice([-3, -2, -1, 1, 2, 3])
    sb = f"{zz} + {b}" if b >= 0 else f"{zz} - {-b}"
    asm = [
        (f"(= {w} {c})", f"{w} = {c}.", False),
        (f"(= {y} (* {m} {w}))", f"{y} = {m}·{w}.", True),
        (f"(= {zz} (* {n2} {w}))", f"{zz} = {n2}·{w}.", True),
        (f"(= {x} (+ {y} {a}))", f"{x} = {y} + {a}.", True),
        (f"(= {x} (+ {zz} {b}))", f"{x} = {sb}.", True),
        (f"(= {d1} (* 2 {d2}))", f"{d1} = 2·{d2}.", True),
    ]
    decls = [f"(declare-const {q} Real)" for q in v]
    return decls, asm, f"(= {x} {obs})", f"{x} is measured to be {obs}."


FAMILIES = {"chain": fam_chain, "diamond": fam_diamond, "arith_chain": fam_arith_chain, "arith_diamond": fam_arith_diamond}


def make_item(idx, fam, rng):
    decls, asm, obs, obs_text = FAMILIES[fam](rng)
    order = list(range(len(asm)))
    rng.shuffle(order)
    asm = [asm[i] for i in order]
    n = len(asm)
    table = z3_sat_table(decls, [a[0] for a in asm], obs)
    assert not table[frozenset(range(n))], "theory+obs must be inconsistent"
    mcs, mus = mcs_mus(table, n)
    assert len(mcs) >= 2
    in_mcs = {i for d in mcs for i in d}
    # targets: two rules from one conflict (MUS), each in some MCS; prefer singleton MCSs
    single = {d[0] for d in mcs if len(d) == 1}
    pairs = [p for m in mus for p in itertools.combinations(m, 2) if all(asm[i][2] and i in in_mcs for i in p)]
    pairs = sorted(set(pairs))
    best = [p for p in pairs if set(p) <= single] or pairs
    a, b = rng.choice(best)
    famous, obscure = NAMES[rng.randrange(len(NAMES))]
    return {
        "id": f"q2-{idx:03d}", "family": fam,
        "assumptions": [{"id": f"A{i+1}", "text": t, "smt": s, "rule": r} for i, (s, t, r) in enumerate(asm)],
        "observation": obs_text, "obs_smt": obs, "decls": decls,
        "mcs": [[f"A{i+1}" for i in d] for d in mcs],
        "mus": [[f"A{i+1}" for i in d] for d in mus],
        "targets": [f"A{a+1}", f"A{b+1}"],
        "famous": famous, "obscure": obscure,
    }


PROMPT = """You are given a set of assumptions about a system and an observation. The observation is reliable. Together with the assumptions it is inconsistent, so some assumptions must be given up.

Choose which assumptions to give up. Requirements:
1. The remaining assumptions must be consistent with the observation.
2. Give up nothing unnecessary: no proper subset of your choice may also restore consistency.
Several choices can satisfy both requirements. Pick the one you consider most reasonable.

Assumptions:
{assumptions}

Observation: {observation}

End your answer with exactly one line of the form
GIVE UP: <comma-separated assumption IDs>"""


def render(item, cond):
    """cond: N | F0 | F1 | O0 | O1 (F/O = famous/obscure name on targets[0|1])."""
    named = {}
    if cond != "N":
        named[item["targets"][int(cond[1])]] = item["famous"] if cond[0] == "F" else item["obscure"]
    lines = []
    for a in item["assumptions"]:
        tag = f" ({named[a['id']]})" if a["id"] in named else ""
        lines.append(f"{a['id']}{tag}. {a['text']}")
    return PROMPT.format(assumptions="\n".join(lines), observation=item["observation"])


CONDS = ["N", "F0", "F1", "O0", "O1"]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--items", default="items.jsonl")
    ap.add_argument("--prompts", default="prompts.jsonl")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    fams = list(FAMILIES)
    items = [make_item(i, fams[i % len(fams)], rng) for i in range(args.n)]
    with open(args.items, "w") as f:
        for it in items:
            f.write(json.dumps(it) + "\n")
    sha = hashlib.sha256(open(args.items, "rb").read()).hexdigest()  # binds every prompt to this manifest
    with open(args.prompts, "w") as f:
        for it in items:
            for c in CONDS:
                f.write(json.dumps({"item": it["id"], "cond": c, "prompt": render(it, c), "manifest": sha}) + "\n")
    print(f"{len(items)} items, {len(items) * len(CONDS)} prompts")
