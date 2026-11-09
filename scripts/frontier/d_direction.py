"""Line D (PREREG_FRONTIER.md): can time-blind content tell which near-duplicate came first?
Usage: python d_direction.py <split 0|1> [set r2|all]
Split 1 reads the selected score C from out/d_pilot_selection.json (written by split 0, set r2)."""
import json
from collections import Counter, defaultdict
from scipy.sparse.csgraph import connected_components
from common import *

SPLIT = int(sys.argv[1]); SET = sys.argv[2] if len(sys.argv) > 2 else "r2"
rng = np.random.default_rng(20261108)
D = load_wiki()
n = len(D)
X, sets, vocab = shingle_matrix(D.m.tolist())
Xf = X.astype(np.float32)
inter = (Xf @ Xf.T).toarray(); sz = np.asarray(Xf.sum(1)).ravel().astype(np.float32)
J = inter / np.maximum(1, sz[:, None] + sz[None, :] - inter); del inter
pg = D.page_id.values; lb = D.label.values; h = D.h.values
L = D.m.str.len().values.astype(float)
cnt = Counter(); [cnt.update(s) for s in sets]
by_label = defaultdict(list); by_page = defaultdict(list)
for i in range(n):
    by_label[lb[i]].append(i); by_page[pg[i]].append(i)

keep = np.ones(n, bool) if SET == "all" else (~D.burst & ~D.tmpl).values
el = (pg[:, None] != pg[None, :]) & (lb[:, None] != lb[None, :]) & keep[:, None] & keep[None, :]
G = el & (J >= 0.3) & (J < 0.999)
A = sp.csr_matrix(np.triu(G, 1))
nc, comp = connected_components(A + A.T, directed=False)
r, c = A.nonzero()
cmin = {}
for i in np.unique(np.concatenate([r, c])):
    cmin[comp[i]] = min(cmin.get(comp[i], "~"), pg[i])
ckey = np.array([zlib.crc32(cmin[comp[i]].encode()) % 2 for i in r])
sel = ckey == SPLIT
r, c = r[sel], c[sel]
lag = np.abs(h[r] - h[c])
ok = lag >= 1 / 3600
r, c, lag = r[ok], c[ok], lag[ok]
print(f"split {SPLIT} set {SET}: pairs {len(r)} (dropped {int((~ok).sum())} same-second)")


def excl(a, b):
    return set(by_label[lb[a]]) | set(by_label[lb[b]]) | set(by_page[pg[a]]) | set(by_page[pg[b]])


def dfp(xs, E):
    out = {}
    for x in xs:
        out[x] = cnt[x] - sum(1 for e in E if x in sets[e])
    return out


def F(S, df):
    return float(np.mean([np.log1p(df[x]) for x in S])) if S else None


rows = []
for a, b, lg in zip(r, c, lag):
    E = excl(a, b)
    Sa, Sb = sets[a], sets[b]
    df = dfp(Sa | Sb, E)
    sh = Sa & Sb
    Fa = F(Sa - Sb, df); Fb = F(Sb - Sa, df); Fs = F(sh, df)
    Fa = Fs if Fa is None else Fa; Fb = Fs if Fb is None else Fb
    pol = Fa - Fb  # >0 -> a earlier
    nov_a = np.mean([df[x] == 0 for x in Sa]); nov_b = np.mean([df[x] == 0 for x in Sb])
    Emask = np.zeros(n, bool); Emask[list(E)] = True
    cen_a = int(((J[a] >= 0.3) & ~Emask).sum()); cen_b = int(((J[b] >= 0.3) & ~Emask).sum())
    a_first = h[a] < h[b]
    def pred(v):  # v > 0 means "a earlier"
        return 0.5 if v == 0 else float(v > 0)
    p = {"S0_length": pred(L[b] - L[a]), "S1_polarity": pred(pol), "S2_novelty": pred(nov_b - nov_a), "S3_centrality": pred(cen_a - cen_b)}
    rows.append({"a": a, "b": b, "comp": comp[a], "s": float(J[a, b]), "lag_h": lg,
                 "bal": abs(np.log(L[a] / L[b])) <= 0.1, "a_first": a_first,
                 "pol": pol, "dnov": nov_b - nov_a, "dcen": cen_a - cen_b, "dlogL": np.log(L[b] / L[a]),
                 **{k: (v if a_first else 1 - v) for k, v in p.items()}})
R = pd.DataFrame(rows)
R.to_csv(OUT / f"d_pairs_split{SPLIT}_{SET}.csv", index=False)
SC = ["S0_length", "S1_polarity", "S2_novelty", "S3_centrality"]


def acc(sub, col, B=2000, diff_with=None):
    if len(sub) == 0:
        return None
    w = 1 / sub.groupby("comp").comp.transform("size").values
    comps = sub.comp.values; uc, inv = np.unique(comps, return_inverse=True)
    v = sub[col].values if diff_with is None else sub[col].values - sub[diff_with].values
    est = float(np.sum(w * v) / w.sum())
    bs = []
    for _ in range(B):
        k = np.bincount(rng.integers(0, len(uc), len(uc)), minlength=len(uc))[inv]
        ww = w * k
        bs.append(np.sum(ww * v) / ww.sum())
    return {"acc": round(est, 3), "ci": [round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)],
            "unweighted": round(float(v.mean()), 3), "pairs": int(len(sub)), "components": int(len(uc))}


res = {"split": SPLIT, "set": SET, "pairs": len(R)}
subsets = {"all_pairs": R, "length_balanced": R[R.bal], "lag<1h": R[R.lag_h < 1], "lag>=1h": R[R.lag_h >= 1], "s>=0.5": R[R.s >= 0.5]}
for nm, sub in subsets.items():
    res[nm] = {k: acc(sub, k) for k in SC}
print(json.dumps(res, indent=1))
if SPLIT == 0 and SET == "r2":
    bal = {k: res["length_balanced"][k]["acc"] for k in SC[1:]}
    C = max(bal, key=lambda k: (bal[k], k == "S1_polarity"))
    (OUT / "d_pilot_selection.json").write_text(json.dumps({"C": C, "balanced_acc": bal}))
    print("SELECTED C =", C)
if SPLIT == 1:
    C = json.loads((OUT / "d_pilot_selection.json").read_text())["C"]
    res["C"] = C
    res["D1_primary_balanced"] = acc(R[R.bal], C)
    res["D2_all"] = acc(R, C)
    res["D2_C_minus_S0"] = acc(R, C, diff_with="S0_length")
    print("CONFIRMATORY", C, json.dumps({k: res[k] for k in ("D1_primary_balanced", "D2_all", "D2_C_minus_S0")}))
(OUT / f"d_direction_split{SPLIT}_{SET}.json").write_text(json.dumps(res, indent=1, default=float))
