"""Line A (PREREG_FRONTIER.md): anchor-propagated dating with split-conformal error bars.
Half 0 calibrates q_f; half 1 evaluates. Sets 'all' and 'r2'."""
import json
from common import *

rng = np.random.default_rng(20261108)
D = load_wiki()
FS = (0.016, 0.05, 0.20); NDRAW = 100; TH = 0.5


def errors(W, f, ndraw):
    X, _, _ = shingle_matrix(W.m.tolist()); J = jaccard_from(X).astype(np.float32)
    pg, lb, h = W.page_id.values, W.label.values, W.h.values
    logL = np.log(W.m.str.len().values.astype(float))
    n = len(W); na = max(1, int(round(f * n)))
    E, Eb, dated_share = [], [], []
    for _ in range(ndraw):
        perm = rng.permutation(n); a = perm[:na]; t = perm[na:]
        el = (pg[t][:, None] != pg[a][None, :]) & (lb[t][:, None] != lb[a][None, :])
        M = np.where(el, J[np.ix_(t, a)], -1.0)
        mx = M.max(1); ok = mx >= TH
        cand = M >= (mx[:, None] - 1e-6)
        dl = np.abs(logL[t][:, None] - logL[a][None, :]) + rng.random((len(t), len(a))) * 1e-9
        pick = np.argmin(np.where(cand, dl, np.inf), 1)
        err = np.abs(h[t] - h[a][pick])
        E.append(err[ok]); dated_share.append(ok.mean())
        Eb.append(np.abs(h[t] - np.median(h[a])))
    return np.concatenate(E), np.concatenate(Eb), float(np.mean(dated_share))


def conformal_q(e, alpha=0.1):
    e = np.sort(e); k = int(np.ceil((1 - alpha) * (len(e) + 1))) - 1
    return float(e[min(k, len(e) - 1)]) if len(e) else np.nan


rows = []
for SET in ("all", "r2"):
    keep = np.ones(len(D), bool) if SET == "all" else (~D.burst & ~D.tmpl).values
    W0 = D[(D.half == 0).values & keep].reset_index(drop=True)
    W1 = D[(D.half == 1).values & keep].reset_index(drop=True)
    for f in FS:
        e0, b0, c0 = errors(W0, f, NDRAW); q = conformal_q(e0); qb = conformal_q(b0)
        e1, b1, c1 = errors(W1, f, NDRAW)
        r = {"set": SET, "f": f, "q_hours": round(q, 3), "q_baseline_hours": round(qb, 1),
             "half0_dated_share": round(c0, 4), "half1_dated_share": round(c1, 4),
             "half1_n_dated_pooled": int(len(e1)), "half1_coverage_of_q": round(float((e1 <= q).mean()), 3) if len(e1) else None,
             "half1_median_abs_err_min": round(float(np.median(e1) * 60), 2) if len(e1) else None,
             "half1_share_within_1h": round(float((e1 < 1).mean()), 3) if len(e1) else None,
             "half1_baseline_coverage": round(float((b1 <= qb).mean()), 3),
             "half1_baseline_median_abs_err_h": round(float(np.median(b1)), 1),
             "A1_validity_ge_0.85": bool(len(e1) and (e1 <= q).mean() >= 0.85),
             "A2_q_le_2h_and_baseline_ge_24h": bool(q <= 2 and qb >= 24)}
        print(json.dumps(r)); rows.append(r)
pd.DataFrame(rows).to_csv(OUT / "a_anchor_dating.csv", index=False)
