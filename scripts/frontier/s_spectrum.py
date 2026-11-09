"""Line S (EXPLORATORY): time-information spectrum. For lag octaves [d, 2d) vs [2d, 4d) (d = 2^k minutes),
within-family AUC of text distance (far pairs more distant?) and plug-in mutual information (bits) between distance quintile and
near/far, bias-corrected by the mean of a within-family length-stratum time-permutation null (B = 100; 95% null band).
Units: (1) introductions: six eligible families' representatives, cross-label pairs; (2) page bodies: 115 pages with >= 15 revisions,
cross-label pairs; (3) planted sampling-matched clocks (p = 0.02) in the four multi-day families, all pairs."""
import json, gzip
from common import *
from swarmclock import stats as stt
from swarmclock.synth import Synth
sys.path.insert(0, str(PROJ / "scripts"))
from swarmclock.io import read_jsonl_gz

rng = np.random.default_rng(20261108)
K = np.arange(0, 13)  # d = 1 min ... 4096 min (2.8 d); far bin up to 4d
EDGES = [(2.0 ** k / 60, 2.0 ** (k + 1) / 60, 2.0 ** (k + 2) / 60) for k in K]


def octave_stats(Ps, times=None, cross=True):
    auc_num = np.zeros(len(K)); auc_w = np.zeros(len(K)); mi_num = np.zeros(len(K)); mi_w = np.zeros(len(K))
    for idx, P in enumerate(Ps):
        t = P["t"] if times is None else times[idx]
        lag = np.abs(t[P["i"]] - t[P["j"]]); d = P["d"]
        base = ~P["same_label"] if cross else np.ones(len(d), bool)
        for q, (a, b, c) in enumerate(EDGES):
            near = base & (lag >= a) & (lag < b); far = base & (lag >= b) & (lag < c)
            n1, n2 = near.sum(), far.sum()
            if n1 < 5 or n2 < 5:
                continue
            x = np.concatenate([d[near], d[far]]); y = np.r_[np.zeros(n1), np.ones(n2)]
            from scipy.stats import rankdata
            rk = rankdata(x); auc = (rk[n1:].sum() - n2 * (n2 + 1) / 2) / (n1 * n2)
            # MI with distance quintiles (pooled within this family-octave)
            qs = np.unique(np.quantile(x, [0.2, 0.4, 0.6, 0.8]))
            bx = np.digitize(x, qs)
            pxy = np.zeros((len(qs) + 1, 2))
            np.add.at(pxy, (bx, y.astype(int)), 1); pxy /= pxy.sum()
            px = pxy.sum(1, keepdims=True); py = pxy.sum(0, keepdims=True)
            nz = pxy > 0
            mi = float(np.sum(pxy[nz] * np.log2(pxy[nz] / (px @ py)[nz])))
            w = min(n1, n2)
            auc_num[q] += w * auc; auc_w[q] += w; mi_num[q] += w * mi; mi_w[q] += w
    with np.errstate(invalid="ignore"):
        return auc_num / auc_w, mi_num / mi_w, auc_w


def spectrum(Ps, name, cross=True, B=100):
    auc, mi, w = octave_stats(Ps, cross=cross)
    na, nm = [], []
    for _ in range(B):
        tt = [stt._permute_within(P["t"], P["strata"], rng) for P in Ps]
        a, m, _ = octave_stats(Ps, tt, cross=cross); na.append(a); nm.append(m)
    na, nm = np.array(na), np.array(nm)
    rows = []
    for q, (a, b, c) in enumerate(EDGES):
        rows.append({"unit": name, "octave_min": f"{2 ** K[q]}-{2 ** (K[q] + 1)} vs {2 ** (K[q] + 1)}-{2 ** (K[q] + 2)}",
                     "d_hours": round(a, 4), "weight": int(w[q]), "auc": round(auc[q], 3),
                     "auc_null_lo": round(np.nanpercentile(na[:, q], 2.5), 3) if np.isfinite(na[:, q]).any() else np.nan,
                     "auc_null_hi": round(np.nanpercentile(na[:, q], 97.5), 3) if np.isfinite(na[:, q]).any() else np.nan,
                     "bits_raw": round(mi[q], 4), "bits_corrected": round(mi[q] - np.nanmean(nm[:, q]), 4) if np.isfinite(nm[:, q]).any() else np.nan,
                     "bits_null_hi": round(np.nanpercentile(nm[:, q], 97.5) - np.nanmean(nm[:, q]), 4) if np.isfinite(nm[:, q]).any() else np.nan})
    return rows


rows = []
# (1) introductions
D = pd.read_parquet(PROJ / "data/interim/D_primary.parquet"); D["t"] = pd.to_datetime(D.t, utc=True)
_, g = fm.family_table(D.drop(columns="family"), D.family.values)
fams = g[g.blocks >= 15].index
X = fm.reps_with_strata(D, fams, "length")
PI = [fm.fam_pairs(X[X.family == f].sort_values("t").reset_index(drop=True)) for f in X.family.unique()]
rows += spectrum(PI, "introductions (cross-label)")
print("intro done", flush=True)
# (3) planted clocks p = 0.02 in multi-day families (sampling-matched; all pairs since labels are real)
S = Synth(D, rng)
RF = {f: X[X.family == f].sort_values("t").reset_index(drop=True) for f in X.family.unique()}
RF = {f: s for f, s in RF.items() if s.t.dt.date.nunique() >= 2}
PC = []
for rep in range(5):
    for f, sub in RF.items():
        PC.append(fm.fam_pairs(S.synth_like(sub, 0.02).assign(stratum=sub.stratum.values)))
rows += spectrum(PC, "planted clock p=0.02 (cross-label)", B=30)
print("clock done", flush=True)
# (2) page bodies
cw = list(read_jsonl_gz(PROJ / "data/raw/cw_revisions.jsonl.gz"))
I = wiki.intro_frame(cw); F = wiki.window_filter(I)
msk = wiki.Masker(F.label)
body = {r["rev_id"]: wiki.get_body(r) for r in cw}
F = F.assign(m=[msk(body[r]) for r in F.rev_id]); F = F[F.m.str.split().str.len() >= 8]
cnt = F.page_id.value_counts(); pages = cnt[cnt >= 15].index
XB = F[F.page_id.isin(pages)].copy(); XB["family"] = XB.page_id; XB["page_id"] = XB.rev_id
XB["len"] = XB.m.str.len()
XB["stratum"] = XB.groupby("family")["len"].transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=False)).astype(int)
PB = [fm.fam_pairs(XB[XB.family == f].reset_index(drop=True)) for f in pages]
rows += spectrum(PB, "page bodies (cross-label)", B=30)
R = pd.DataFrame(rows); R.to_csv(OUT / "s_spectrum.csv", index=False)
print(R.to_string(index=False))
