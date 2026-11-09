"""L1 co-time (PREREG_POSITIVE_LINE.md). Usage: python l1_cotime.py <wiki_half 0|1> <mantiq_split practice|hidden>
Read-only on the project; writes only to ./out/."""
import sys, json, zlib
from pathlib import Path
PROJ = Path("/Volumes/MacMiniExt/dev/research/SwarmAlignmentHackathon/swarm-clock-project")
sys.path.insert(0, str(PROJ / "src"))
import numpy as np
import pandas as pd
import scipy.sparse as sp
from swarmclock import families as fm, wiki
from swarmclock.io import hours

OUT = Path(__file__).resolve().parent / "out"; OUT.mkdir(exist_ok=True)
HALF = int(sys.argv[1]); MSPLIT = sys.argv[2]
rng = np.random.default_rng(20261108)


def jaccard_matrix(texts, k=3):
    vocab, rows, cols = {}, [], []
    for i, t in enumerate(texts):
        for s in fm.shingle_set(t, k):
            rows.append(i); cols.append(vocab.setdefault(s, len(vocab)))
    X = sp.csr_matrix((np.ones(len(rows), dtype=np.float32), (rows, cols)), shape=(len(texts), len(vocab)))
    X.data[:] = 1.0
    inter = (X @ X.T).toarray()
    sz = np.asarray(X.sum(1)).ravel()
    return inter / np.maximum(1, sz[:, None] + sz[None, :] - inter)


_INV = {}
def wauc(s, y, w=None):
    """Weighted AUC with ties counted 1/2 (unique-value inverse cached per score array)."""
    w = np.ones_like(s, dtype=float) if w is None else w
    key = (id(s), len(s))
    if key not in _INV:
        _INV[key] = np.unique(np.round(s, 6), return_inverse=True)
    u, inv = _INV[key]
    pos = np.bincount(inv, weights=w * y, minlength=len(u)); neg = np.bincount(inv, weights=w * (1 - y), minlength=len(u))
    P, N = pos.sum(), neg.sum()
    if P == 0 or N == 0:
        return np.nan
    cneg = np.cumsum(neg) - neg
    return float(np.sum(pos * (cneg + 0.5 * neg)) / (P * N))


def analyse(texts, t, group, actor, unit_of_boot, thr_y, tag, extra_excl=None, nboot=200):
    """group: page/path (pairs must differ), actor: label/agent (pairs must differ), unit_of_boot: cluster ids for bootstrap.
    t in hours (wiki) or fraction of run (Mantiq). Pairs are only formed within the same 'block' if block given via group prefix."""
    n = len(texts); _INV.clear()
    J = jaccard_matrix(texts)
    lag = np.abs(t[:, None] - t[None, :])
    elig = (group[:, None] != group[None, :]) & (actor[:, None] != actor[None, :])
    np.fill_diagonal(elig, False)
    L = np.array([len(x) for x in texts], dtype=float)
    res = {"tag": tag, "n_items": int(n)}
    iu = np.triu_indices(n, 1)
    m = elig[iu]
    s = J[iu][m]; lg = lag[iu][m]
    res["pairs"] = int(m.sum())
    cl = unit_of_boot
    ci_, cj_ = cl[iu[0]][m], cl[iu[1]][m]
    ucl, cinv_i = np.unique(cl, return_inverse=True)
    idx_i = cinv_i[iu[0]][m]; idx_j = cinv_i[iu[1]][m]
    lensim = -np.abs(np.log(L[iu[0]][m]) - np.log(L[iu[1]][m]))
    for thr in thr_y:
        y = (lg < thr).astype(float)
        a = wauc(s, y); al = wauc(lensim, y)
        boots = []
        for _ in range(nboot):
            wc = np.bincount(rng.integers(0, len(ucl), len(ucl)), minlength=len(ucl)).astype(float)
            w = wc[idx_i] * wc[idx_j]
            boots.append(wauc(s, y, w))
        res[f"y<{thr}"] = {"base_rate": float(y.mean()), "auc_content": a, "auc_ci": [float(np.nanpercentile(boots, 2.5)), float(np.nanpercentile(boots, 97.5))],
                           "auc_length_only": al,
                           "P(y|s>=0.5)": float(y[s >= 0.5].mean()) if (s >= 0.5).any() else None, "n_pairs_s>=0.5": int((s >= 0.5).sum()),
                           "P(y|s>=0.9)": float(y[s >= 0.9].mean()) if (s >= 0.9).any() else None, "n_pairs_s>=0.9": int((s >= 0.9).sum()),
                           "P(y|0<s<0.3)": float(y[(s > 0) & (s < 0.3)].mean()) if ((s > 0) & (s < 0.3)).any() else None,
                           "P(y|s==0)": float(y[s == 0].mean())}
    # L1b nearest neighbours, each item once
    logL = np.log(L)
    nn = {}
    for th in (0.3, 0.5, 0.9):
        rows = []
        for i in range(n):
            e = np.where(elig[i])[0]
            if len(e) == 0:
                continue
            si = J[i, e]; mx = si.max()
            if mx < th:
                continue
            cand = e[si == mx]
            dl = np.abs(logL[cand] - logL[i]); cand = cand[dl == dl.min()]
            jc = cand[rng.integers(len(cand))]
            dlen = np.abs(logL[e] - logL[i]); lc = e[dlen == dlen.min()]; jl = lc[rng.integers(len(lc))]
            rows.append((i, lag[i, jc], lag[i, jl], [float((lag[i, e] < thr).mean()) for thr in thr_y]))
        if not rows:
            nn[str(th)] = {"covered": 0}; continue
        lc_ = np.array([r[1] for r in rows]); ll_ = np.array([r[2] for r in rows]); rb = np.array([r[3] for r in rows])
        d = {"covered": len(rows), "coverage_share": len(rows) / n,
             "median_lag_content_nn": float(np.median(lc_)), "median_lag_length_nn": float(np.median(ll_))}
        for k, thr in enumerate(thr_y):
            d[f"y<{thr}"] = {"content_nn": float((lc_ < thr).mean()), "length_nn": float((ll_ < thr).mean()), "random_partner": float(rb[:, k].mean())}
        # bootstrap CI for (content - length) at the primary threshold, over items' clusters
        items = np.array([r[0] for r in rows]); icl = cinv_i[items]; uc = np.unique(icl)
        diffs = []
        thr0 = thr_y[0]
        dc = (lc_ < thr0).astype(float) - (ll_ < thr0).astype(float)
        for _ in range(nboot):
            pick = rng.choice(uc, len(uc), replace=True)
            cnt = np.bincount(np.searchsorted(uc, pick), minlength=len(uc))
            w = cnt[np.searchsorted(uc, icl)]
            diffs.append(np.sum(w * dc) / max(1, w.sum()))
        d[f"diff_content_minus_length_y<{thr0}_ci"] = [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))]
        nn[str(th)] = d
    res["L1b"] = nn
    return res


out = {}
# ---------------- wiki
D = pd.read_parquet(PROJ / "data/interim/D_primary.parquet"); D["t"] = pd.to_datetime(D.t, utc=True)
D["half"] = [zlib.crc32(p.encode()) % 2 for p in D.page_id]
fam_pages = D.groupby("family").page_id.nunique()
burst = fam_pages[fam_pages == 314].index.tolist()
print("burst family:", burst)
W = D[D.half == HALF].reset_index(drop=True)
tmpl = W.m.str.contains(wiki.TEMPLATE)
variants = {"all": np.ones(len(W), bool), "r1_no_burst": ~W.family.isin(burst).values,
            "r2_no_burst_no_template": (~W.family.isin(burst) & ~tmpl).values}
for name, keep in variants.items():
    X = W[keep].reset_index(drop=True)
    r = analyse(X.m.tolist(), hours(X.t), X.page_id.values, X.label.values, X.page_id.values,
                [1.0, 1 / 6, 6.0], f"wiki half {HALF} {name}")
    print(json.dumps(r, indent=1)); out[f"wiki_{name}"] = r
# ---------------- Mantiq (pairs within run only: analyse per run would lose pooling; we pool by making cross-run pairs ineligible)
U = pd.read_parquet(PROJ / "data/interim/mantiq_U-F-noboiler.parquet"); U["t"] = pd.to_datetime(U.t, utc=True)
U = U[U.run.str.startswith(MSPLIT)].reset_index(drop=True)
# cross-run pairs made ineligible by giving every run its own actor namespace and group namespace is not enough
# (different runs would still pair); handle by running per run and pooling pairs.
allres = []
texts, tt, grp, act, clu = [], [], [], [], []
offset = 0.0
for run, X in U.groupby("run"):
    # shift each run's times far apart (1e6 fractions) so cross-run pairs have huge lag and are excluded below
    texts += X.m.tolist(); tt += list(hours(X.t) + offset); grp += list(run + "|" + X.path); act += list(run + "|" + X.label); clu += [run] * len(X)
    offset += 1e6
tt = np.array(tt); grp = np.array(grp); act = np.array(act); clu = np.array(clu)
# exclude cross-run pairs: mark them as same group by masking inside analyse via group equality trick is not possible,
# so we analyse with lag threshold and drop pairs with lag > 1e5 (cross-run) by pre-filtering in a wrapper.
def analyse_mantiq():
    n = len(texts); _INV.clear()
    import types
    J = jaccard_matrix(texts)
    lag = np.abs(tt[:, None] - tt[None, :])
    same_run = clu[:, None] == clu[None, :]
    elig = same_run & (grp[:, None] != grp[None, :]) & (act[:, None] != act[None, :]); np.fill_diagonal(elig, False)
    L = np.array([len(x) for x in texts], dtype=float); logL = np.log(L)
    iu = np.triu_indices(n, 1); m = elig[iu]
    s = J[iu][m]; lg = lag[iu][m]
    ucl, cinv = np.unique(clu, return_inverse=True); ii = cinv[iu[0]][m]
    lensim = -np.abs(logL[iu[0]][m] - logL[iu[1]][m])
    res = {"tag": f"mantiq {MSPLIT} U-F-noboiler", "n_items": int(n), "runs": int(len(ucl)), "pairs": int(m.sum())}
    for thr in (0.1, 0.05, 1 / 3):
        y = (lg < thr).astype(float)
        boots = []
        for _ in range(200):
            wc = np.bincount(rng.integers(0, len(ucl), len(ucl)), minlength=len(ucl)).astype(float)
            boots.append(wauc(s, y, wc[ii]))
        res[f"y<{thr:.3f}D"] = {"base_rate": float(y.mean()), "auc_content": wauc(s, y), "auc_ci": [float(np.nanpercentile(boots, 2.5)), float(np.nanpercentile(boots, 97.5))],
                                "auc_length_only": wauc(lensim, y),
                                "P(y|s>=0.5)": float(y[s >= 0.5].mean()) if (s >= 0.5).any() else None, "n_pairs_s>=0.5": int((s >= 0.5).sum())}
    rows = []
    for i in range(n):
        e = np.where(elig[i])[0]
        if len(e) == 0:
            continue
        si = J[i, e]; mx = si.max()
        if mx < 0.5:
            continue
        cand = e[si == mx]; dl = np.abs(logL[cand] - logL[i]); cand = cand[dl == dl.min()]; jc = cand[rng.integers(len(cand))]
        dlen = np.abs(logL[e] - logL[i]); lc = e[dlen == dlen.min()]; jl = lc[rng.integers(len(lc))]
        rows.append((lag[i, jc], lag[i, jl], float((lag[i, e] < 0.1).mean())))
    if rows:
        a = np.array(rows)
        res["L1b_s>=0.5_y<0.1D"] = {"covered": len(rows), "coverage_share": len(rows) / n, "content_nn": float((a[:, 0] < 0.1).mean()),
                                    "length_nn": float((a[:, 1] < 0.1).mean()), "random_partner": float(a[:, 2].mean()),
                                    "median_lag_content_nn_D": float(np.median(a[:, 0])), "median_lag_length_nn_D": float(np.median(a[:, 1]))}
    return res
r = analyse_mantiq(); print(json.dumps(r, indent=1)); out["mantiq"] = r
(OUT / f"l1_wikihalf{HALF}_{MSPLIT}.json").write_text(json.dumps(out, indent=1, default=float))
print("done")
