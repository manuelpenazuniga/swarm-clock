"""Line H (PREREG_FRONTIER_H.md): relay vs broadcast polarity on held-out hub introductions."""
import json
from collections import Counter, defaultdict
from scipy.sparse.csgraph import connected_components
from common import *

rng = np.random.default_rng(20261108)
F = pd.read_parquet(PROJ / "data/interim/wiki_intros.parquet"); F["t"] = pd.to_datetime(F.t, utc=True)
F = F.reset_index(drop=True)
allsets = [fm.shingle_set(t, 3) for t in F.m]
cnt = Counter(); [cnt.update(s) for s in allsets]
by_label = defaultdict(list)
for i, l in enumerate(F.label.values):
    by_label[l].append(i)
hub_idx = np.where(F.page_id.isin(wiki.HUBS).values & ~F.m.str.contains(wiki.TEMPLATE).values)[0]
H = F.iloc[hub_idx].reset_index(drop=True)
hs = [allsets[i] for i in hub_idx]
X, _, _ = shingle_matrix(H.m.tolist()); J = jaccard_from(X)
lb = H.label.values; h = hours(H.t); L = H.m.str.len().values.astype(float)
G = (lb[:, None] != lb[None, :]) & (J >= 0.3) & (J < 0.999)
A = sp.csr_matrix(np.triu(G, 1)); nc, comp = connected_components(A + A.T, directed=False)
r, c = A.nonzero(); lag = np.abs(h[r] - h[c]); ok = lag >= 1 / 3600
r, c, lag = r[ok], c[ok], lag[ok]
print("pairs", len(r), "dropped same-second", int((~ok).sum()))
rows = []
cache = {}
for a, b, lg in zip(r, c, lag):
    ga, gb = hub_idx[a], hub_idx[b]
    E = set(by_label[lb[a]]) | set(by_label[lb[b]]) | {ga, gb}
    Sa, Sb = hs[a], hs[b]
    df = {}
    for x in Sa | Sb:
        df[x] = cnt[x] - sum(1 for e in E if x in allsets[e])
    Fn = lambda S: float(np.mean([np.log1p(df[x]) for x in S])) if S else None
    Fs = Fn(Sa & Sb); Fa = Fn(Sa - Sb); Fb = Fn(Sb - Sa)
    Fa = Fs if Fa is None else Fa; Fb = Fs if Fb is None else Fb
    nov_a = np.mean([df[x] == 0 for x in Sa]); nov_b = np.mean([df[x] == 0 for x in Sb])
    pr = lambda v: 0.5 if v == 0 else float(v > 0)
    a_first = h[a] < h[b]
    p_ = {"S0_length": pr(L[b] - L[a]), "S1_polarity": pr(Fa - Fb), "S2_novelty": pr(nov_b - nov_a)}
    rows.append({"comp": comp[a], "lag_h": lg, "s": J[a, b], "page_a": H.page_id[a], "page_b": H.page_id[b],
                 **{q: (v if a_first else 1 - v) for q, v in p_.items()}})
R = pd.DataFrame(rows); R.to_csv(OUT / "h_pairs.csv", index=False)


def acc(sub, col, B=2000):
    w = 1 / sub.groupby("comp").comp.transform("size").values
    uc, inv = np.unique(sub.comp.values, return_inverse=True); v = sub[col].values
    est = float(np.sum(w * v) / w.sum()); bs = []
    for _ in range(B):
        k = np.bincount(rng.integers(0, len(uc), len(uc)), minlength=len(uc))[inv]
        bs.append(np.sum(w * k * v) / np.sum(w * k))
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return {"acc": round(est, 3), "ci": [round(float(lo), 3), round(float(hi), 3)], "unweighted": round(float(v.mean()), 3),
            "pairs": int(len(sub)), "components": int(len(uc))}


res = {}
for nm, sub in {"all": R, "lag<10min": R[R.lag_h < 1 / 6], "lag>=10min": R[R.lag_h >= 1 / 6]}.items():
    res[nm] = {q: acc(sub, q) for q in ["S0_length", "S1_polarity", "S2_novelty"]} if len(sub) else None
p = res["all"]["S1_polarity"]
res["H1_broadcast_upperCI_lt_0.66"] = p["ci"][1] < 0.66
res["H2_relay_lowerCI_gt_0.5"] = p["ci"][0] > 0.5
res["lag_quantiles_min"] = (R.lag_h * 60).quantile([.1, .5, .9]).round(2).to_dict()
print(json.dumps(res, indent=1, default=float))
(OUT / "h_hubs.json").write_text(json.dumps(res, indent=1, default=float))
