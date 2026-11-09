"""Line T (PREREG_FRONTIER_T.md): terminus post quem dating. Usage: python t_tpq.py <pilot|confirm> [set all|r2] [nd allow|exclude]
pilot: targets q = 1, selects variant -> out/t_pilot_selection.json. confirm: targets q = 3 with the selected variant."""
import json
from collections import defaultdict
from common import *

MODE = "confirm"; SET = "all"; ND = "exclude"  # EXPLORATORY follow-ups on confirmation targets
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
ha = h[anc]; la = lb[anc]; pa = pg[anc]


def build(m):
    """Concatenated eligible-anchor indices per (target, feature)."""
    idx, feat_start, feat_tg = [], [], []
    pos = 0
    for r, i in enumerate(tg):
        elig = (la != lb[i]) & (pa != pg[i])
        if ND == "exclude":
            elig &= Jta[r] < 0.3
        for s in sets[i]:
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



t = h[tg]; day = pd.to_datetime(t * 3.6e12).floor("D")
idx, fs, ft = build(2)
T = tpq(ha, idx, fs, ft, "q90"); ok = ~np.isnan(T); d = t - T; succ = (d >= -1) & (d <= 24)
print("CONFIRM q90 m2: coverage", ok.mean().round(4), "success", succ[ok].mean().round(4))
# per-day concentration
Dd = pd.DataFrame({"day": day[ok], "succ": succ[ok]})
g = Dd.groupby("day").succ.agg(["size", "mean"]).sort_values("size", ascending=False)
print("targets by day (top 6):"); print(g.head(6).round(3).to_string())
top2 = g.index[:2]; m = ~Dd.day.isin(top2)
nullsucc = []
for _ in range(200):
    Tn = tpq(rng.permutation(ha), idx, fs, ft, "q90"); dn = t - Tn
    nullsucc.append((((dn >= -1) & (dn <= 24))[ok])[m.values].mean())
print("excluding the 2 busiest days: n", int(m.sum()), "success", Dd.succ[m].mean().round(3), "null mean", np.mean(nullsucc).round(3), "p975", np.percentile(nullsucc, 97.5).round(3))
# nearest-anchor baseline (J < 0.3, other label/page): date = time of the most similar eligible anchor with J > 0
el = (la[None, :] != lb[tg][:, None]) & (pa[None, :] != pg[tg][:, None]) & (Jta < 0.3) & (Jta > 0)
Jm = np.where(el, Jta, -1); best = Jm.argmax(1); okk = Jm.max(1) > 0
dk = t - ha[best]
print("kNN (J<0.3) dated", okk.mean().round(3), "success [-1h,+24h]", (((dk >= -1) & (dk <= 24))[okk]).mean().round(3),
      "| |err|<24h", (np.abs(dk[okk]) < 24).mean().round(3), "| TPQ on same targets", succ[okk & ok].mean().round(3))
# anchor density: subsample anchors to a share f of ALL introductions
for f in (0.02, 0.05, 0.10, 0.25):
    res = []
    for rep in range(5):
        keep = np.zeros(len(anc), bool); keep[rng.choice(len(anc), int(round(f * len(D))), replace=False)] = True
        hh = np.where(keep, ha, np.nan)
        # drop features whose eligible anchors are all dropped: recompute with nan-aware min (nan -> +inf)
        hv = np.where(np.isnan(hh), np.inf, hh)
        fmin = np.minimum.reduceat(hv[idx], fs); good = np.isfinite(fmin)
        # need >= 2 kept eligible anchors per feature (m = 2)
        cntk = np.add.reduceat(keep[idx].astype(int), fs); good &= cntk >= 2
        out = np.full(len(tg), np.nan)
        dfm = pd.DataFrame({"g": ft[good], "v": fmin[good]})
        q = dfm.groupby("g").v.apply(lambda s: np.sort(s.values)[int(np.floor(0.9 * (len(s) - 1)))])
        out[q.index.values] = q.values
        o = ~np.isnan(out); dd = t[o] - out[o]
        sn = []
        for _ in range(50):
            hp = hv.copy(); kk = np.where(keep)[0]; hp[kk] = rng.permutation(hv[kk])
            fm2 = np.minimum.reduceat(hp[idx], fs)[good]
            qn = pd.DataFrame({"g": ft[good], "v": fm2}).groupby("g").v.apply(lambda s: np.sort(s.values)[int(np.floor(0.9 * (len(s) - 1)))])
            dn = t[qn.index.values] - qn.values; sn.append(((dn >= -1) & (dn <= 24)).mean())
        res.append((o.mean(), ((dd >= -1) & (dd <= 24)).mean(), np.mean(sn)))
    r = np.array(res).mean(0)
    print(f"anchor share {f}: coverage {r[0]:.3f} success {r[1]:.3f} null {r[2]:.3f}")
