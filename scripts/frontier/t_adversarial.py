"""Line T (PREREG_FRONTIER_T.md): terminus post quem dating. Usage: python t_tpq.py <pilot|confirm> [set all|r2] [nd allow|exclude]
pilot: targets q = 1, selects variant -> out/t_pilot_selection.json. confirm: targets q = 3 with the selected variant."""
import json
from collections import defaultdict
from common import *

MODE = sys.argv[1]; SET = "all"; ND = "exclude"; ADV = sys.argv[2]  # EXPLORATORY adversarial variants
import re
DATE_RE = re.compile(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|mon|tue|wed|thu|fri|sat|sun|today|yesterday|tomorrow|date|utc|gmt|time|day|hour|week|night|morning)", re.I)
rng = np.random.default_rng(20261108)
D = load_wiki(); D["q"] = [zlib.crc32(p.encode()) % 4 for p in D.page_id]
if SET == "r2":
    D = D[(~D.burst & ~D.tmpl).values].reset_index(drop=True)
X, sets, vocab = shingle_matrix(D.m.tolist())
anc = np.where(D.q.isin([0, 2]).values)[0]
tq = 1 if MODE == "pilot" else 3
tg = np.where(D.q.values == tq)[0]
h = D.h.values; lb = D.label.values; pg = D.page_id.values
Xa = X[anc]; Xt = X[tg]
inter = (Xt @ Xa.T).toarray(); sa = np.asarray(Xa.sum(1)).ravel(); st = np.asarray(Xt.sum(1)).ravel()
Jta = inter / np.maximum(1, st[:, None] + sa[None, :] - inter); del inter
# inverted index over anchors (local anchor positions)
inv = defaultdict(list)
for k, i in enumerate(anc):
    for s in sets[i]:
        inv[s].append(k)
inv = {s: np.array(v) for s, v in inv.items() if len(v) <= 50}
ha = h[anc]; la = lb[anc]; pa = pg[anc]; fam = D.family.values; fa = fam[anc]


def build(m):
    """Concatenated eligible-anchor indices per (target, feature)."""
    idx, feat_start, feat_tg = [], [], []
    pos = 0
    for r, i in enumerate(tg):
        elig = (la != lb[i]) & (pa != pg[i])
        if ND == "exclude":
            elig &= Jta[r] < 0.3
        if "fam" in ADV or ADV == "all3":
            elig &= fa != fam[i]
        if "prefix" in ADV or ADV == "all3":
            elig &= np.array([x[:6] != lb[i][:6] for x in la])
        for s in sets[i]:
            if ("date" in ADV or ADV == "all3") and DATE_RE.search(s):
                continue
            a = inv.get(s)
            if a is None:
                continue
            a = a[elig[a]]
            if len(a) >= m:
                feat_start.append(pos); feat_tg.append(r); idx.append(a); pos += len(a)
    return (np.concatenate(idx) if idx else np.array([], int)), np.array(feat_start, int), np.array(feat_tg, int)


def tpq(times, idx, fs, ft, stat):
    if len(fs) == 0:
        return np.full(len(tg), np.nan)
    fmin = np.minimum.reduceat(times[idx], fs)
    out = np.full(len(tg), np.nan)
    order = np.lexsort((fmin, ft)); g = ft[order]; v = fmin[order]
    starts = np.r_[0, np.where(np.diff(g) != 0)[0] + 1]; ends = np.r_[starts[1:], len(g)]
    for s0, e0 in zip(starts, ends):
        n = e0 - s0
        out[g[s0]] = v[e0 - 1] if stat == "max" else v[s0 + int(np.floor(0.9 * (n - 1)))]
    return out


def metrics(T):
    t = h[tg]; ok = ~np.isnan(T)
    d = t[ok] - T[ok]
    succ = (d >= -1) & (d <= 24)
    return {"coverage": float(ok.mean()), "success": float(succ.mean()) if ok.any() else np.nan,
            "validity": float((d >= -1).mean()) if ok.any() else np.nan,
            "median_t_minus_tpq_h": float(np.median(d)) if ok.any() else np.nan,
            "share_success_dayscale": float(((d >= 1) & (d <= 24)).mean()) if ok.any() else np.nan}


B = 200
variants = [("max", 2), ("max", 1), ("q90", 2), ("q90", 1)]
if True:
    sel = json.loads((OUT / f"t_pilot_selection_{SET}_{ND}.json").read_text()) if (OUT / f"t_pilot_selection_{SET}_{ND}.json").exists() \
        else json.loads((OUT / "t_pilot_selection_all_exclude.json").read_text())
    variants = [("q90", 2)]
res = []
for stat, m in variants:
    idx, fs, ft = build(m)
    real = metrics(tpq(ha, idx, fs, ft, stat))
    nulls = [metrics(tpq(rng.permutation(ha), idx, fs, ft, stat)) for _ in range(B)]
    ns = np.array([x["success"] for x in nulls]); nv = np.array([x["validity"] for x in nulls]); nd_ = np.array([x["share_success_dayscale"] for x in nulls])
    r = {"adv": ADV, "mode": MODE, "set": SET, "near_dups": ND, "stat": stat, "m": m, "targets": len(tg), **{k: round(v, 4) for k, v in real.items()},
         "null_success_mean": round(float(ns.mean()), 4), "null_success_p975": round(float(np.percentile(ns, 97.5)), 4),
         "null_validity_mean": round(float(nv.mean()), 4), "null_dayscale_mean": round(float(nd_.mean()), 4),
         "excess": round(real["success"] - float(ns.mean()), 4),
         "p_perm": round(float((1 + np.sum(ns >= real["success"])) / (B + 1)), 4)}
    r["T1"] = bool(real["success"] > np.percentile(ns, 97.5) and r["excess"] >= 0.10)
    print(json.dumps(r), flush=True); res.append(r)
pd.DataFrame(res).assign(adv=ADV).to_csv(OUT / f"t_adv_{MODE}_{ADV}.csv", index=False)
if False:
    best = max(res, key=lambda r: (r["excess"], r["stat"] == "max" and r["m"] == 2))
    (OUT / "t_pilot_selection_all_exclude.json").write_text(json.dumps({"stat": best["stat"], "m": best["m"], "excess": best["excess"]}))
    print("SELECTED", best["stat"], best["m"])
