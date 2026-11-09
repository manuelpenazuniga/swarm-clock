"""EXPLORATORY power check for line D (written after the D confirmation, to interpret it).
Planted clusters of near-duplicates rooted at real introductions, cluster sizes drawn from the real r2 near-duplicate components.
Models: 'peer' (member i copies one of the previous <= 5 members, token edits rate p; times in copy order)
        'star' (each member an independent edit of the root at 3p; times random) -> scores must sit at 0.5.
Scores S0..S3 exactly as in d_direction.py; df' over real corpus (planted roots removed) + all planted members, minus the pair."""
import json
from collections import Counter
from common import *
from swarmclock.synth import Synth

rng = np.random.default_rng(20261108)
D = load_wiki()
R = D[(~D.burst & ~D.tmpl).values].reset_index(drop=True)
syn = Synth(R, rng)
pairs1 = pd.read_csv(OUT / "d_pairs_split0_r2.csv"); pairs2 = pd.read_csv(OUT / "d_pairs_split1_r2.csv")
P = pd.concat([pairs1, pairs2])
sizes = np.array([len(set(g.a) | set(g.b)) for _, g in P.groupby("comp")])
print("real component sizes: median", np.median(sizes), "max", sizes.max())
real_sets = [fm.shingle_set(t, 3) for t in D.m]
roots_pool = R[R.m.str.split().str.len().between(15, 200)].reset_index(drop=True)


def run(model, p, ncl=150):
    clusters = []
    for ci in range(ncl):
        k = int(sizes[rng.integers(len(sizes))]); k = max(k, 3)
        ridx = rng.integers(len(roots_pool)); toks0 = roots_pool.m.iloc[ridx].split()
        mem = []
        for i in range(k):
            if model == "peer":
                par = toks0 if i == 0 else mem[rng.integers(max(0, i - 5), i)]
                mem.append(syn.mutate(par, p))
            else:
                mem.append(syn.mutate(toks0, 3 * p))
        order = np.arange(k) if model == "peer" else rng.permutation(k)  # time rank of each member
        clusters.append((roots_pool.rev_id.iloc[ridx], [" ".join(x) for x in mem], order))
    root_ids = {c[0] for c in clusters}
    cnt = Counter()
    for s, rid in zip(real_sets, D.rev_id.values):
        if rid not in root_ids:
            cnt.update(s)
    csets = [[fm.shingle_set(t, 3) for t in c[1]] for c in clusters]
    for cs in csets:
        for s in cs:
            cnt.update(s)
    rows = []
    for ci, ((rid, texts, order), cs) in enumerate(zip(clusters, csets)):
        k = len(cs)
        Jm = np.array([[len(cs[a] & cs[b]) / max(1, len(cs[a] | cs[b])) for b in range(k)] for a in range(k)])
        # centrality within the planted cluster (relatives outside it are not planted)
        for a in range(k):
            for b in range(a + 1, k):
                if not (0.3 <= Jm[a, b] < 0.999):
                    continue
                Sa, Sb = cs[a], cs[b]
                df = {x: cnt[x] - (x in Sa) - (x in Sb) for x in Sa | Sb}
                F = lambda S: float(np.mean([np.log1p(df[x]) for x in S])) if S else None
                Fs = F(Sa & Sb); Fa = F(Sa - Sb); Fb = F(Sb - Sa)
                Fa = Fs if Fa is None else Fa; Fb = Fs if Fb is None else Fb
                nov_a = np.mean([df[x] == 0 for x in Sa]); nov_b = np.mean([df[x] == 0 for x in Sb])
                cen_a = int((Jm[a] >= 0.3).sum() - 2); cen_b = int((Jm[b] >= 0.3).sum() - 2)
                a_first = order[a] < order[b]
                pr = lambda v: 0.5 if v == 0 else float(v > 0)
                p_ = {"S0_length": pr(len(texts[b]) - len(texts[a])), "S1_polarity": pr(Fa - Fb),
                      "S2_novelty": pr(nov_b - nov_a), "S3_centrality": pr(cen_a - cen_b)}
                rows.append({"comp": ci, **{q: (v if a_first else 1 - v) for q, v in p_.items()}})
    Rr = pd.DataFrame(rows)
    out = {"model": model, "p": p, "pairs": len(Rr), "clusters_with_pairs": int(Rr.comp.nunique()) if len(Rr) else 0}
    if len(Rr):
        w = 1 / Rr.groupby("comp").comp.transform("size").values
        for q in ["S0_length", "S1_polarity", "S2_novelty", "S3_centrality"]:
            out[q] = round(float(np.sum(w * Rr[q]) / w.sum()), 3)
    return out


donors = [t.split() for t in R.m.tolist()]
def block_mutate(toks, p):
    toks = list(toks); n = max(1, len(toks))
    K = rng.poisson(1.5 * p * n / 4)
    for _ in range(K):
        bl = int(rng.geometric(1 / 4)); d = donors[rng.integers(len(donors))]
        st = rng.integers(0, max(1, len(d) - bl + 1)); blk = d[st:st + bl]
        pos = rng.integers(0, max(1, len(toks)))
        u = rng.random()
        if u < 0.5: toks[pos:pos + bl] = blk
        elif u < 0.75: del toks[pos:pos + bl]
        else: toks[pos:pos] = blk
    return toks
syn.mutate = block_mutate
res = []
for model in ("peer", "star"):
    for p in (0.05, 0.10, 0.20):
        r = run(model, p); r["edit"] = "donor_block"; print(r); res.append(r)
pd.DataFrame(res).to_csv(OUT / "d_positive_control_donor.csv", index=False)
