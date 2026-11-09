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




t = h[tg]
el = (la[None, :] != lb[tg][:, None]) & (pa[None, :] != pg[tg][:, None]) & (Jta < 0.3) & (Jta > 0)
Jm = np.where(el, Jta, -1); best = Jm.argmax(1); okk = Jm.max(1) > 0
def m_(tt):
    dk = t - tt[best]
    return ((dk[okk] >= -1) & (dk[okk] <= 24)).mean(), (np.abs(dk[okk]) < 24).mean(), np.median(np.abs(dk[okk]))
real = m_(ha); nl = np.array([m_(rng.permutation(ha)) for _ in range(200)])
print("kNN J<0.3 (EXPLORATORY) dated %.3f | success[-1,+24] %.3f null %.3f (p975 %.3f) | |err|<24h %.3f null %.3f (p975 %.3f) | median |err| h %.1f null %.1f" % (
    okk.mean(), real[0], nl[:,0].mean(), np.percentile(nl[:,0],97.5), real[1], nl[:,1].mean(), np.percentile(nl[:,1],97.5), real[2], nl[:,2].mean()))
