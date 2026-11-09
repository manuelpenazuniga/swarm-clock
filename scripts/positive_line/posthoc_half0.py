"""POST HOC (not in PREREG_POSITIVE_LINE.md), pilot half 0 only, descriptive:
(a) L1 event level: connected components of the cross-page, cross-label s >= 0.5 graph (burst and template excluded);
    span of each component, share of components spanning < 1 h, labels and pages per component.
(b) L2 time-independent subset: pages in the lowest tercile of body-length coefficient of variation (selection does not use time)."""
import sys, json, zlib
from pathlib import Path
PROJ = Path("/Volumes/MacMiniExt/dev/research/SwarmAlignmentHackathon/swarm-clock-project")
sys.path.insert(0, str(PROJ / "src")); sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from scipy.sparse.csgraph import connected_components
from scipy.sparse import csr_matrix
from scipy.stats import wilcoxon
from swarmclock import wiki, io as sio
from swarmclock.io import hours, RAW
import scipy.sparse as sp
from swarmclock import families as fm
def jaccard_matrix(texts, k=3):
    vocab, rows, cols = {}, [], []
    for i, x in enumerate(texts):
        for s in fm.shingle_set(x, k):
            rows.append(i); cols.append(vocab.setdefault(s, len(vocab)))
    X = sp.csr_matrix((np.ones(len(rows), dtype=np.float32), (rows, cols)), shape=(len(texts), len(vocab))); X.data[:] = 1.0
    inter = (X @ X.T).toarray(); sz = np.asarray(X.sum(1)).ravel()
    return inter / np.maximum(1, sz[:, None] + sz[None, :] - inter)
OUT = Path(__file__).resolve().parent / "out"
HALF = 0
D = pd.read_parquet(PROJ / "data/interim/D_primary.parquet"); D["t"] = pd.to_datetime(D.t, utc=True)
D["half"] = [zlib.crc32(p.encode()) % 2 for p in D.page_id]
fp = D.groupby("family").page_id.nunique(); burst = fp[fp == 314].index
W = D[(D.half == HALF) & ~D.family.isin(burst) & ~D.m.str.contains(wiki.TEMPLATE)].reset_index(drop=True)
J = jaccard_matrix(W.m.tolist()); t = hours(W.t)
pg, lb = W.page_id.values, W.label.values
A = (J >= 0.5) & (pg[:, None] != pg[None, :]) & (lb[:, None] != lb[None, :]); np.fill_diagonal(A, False)
nc, comp = connected_components(csr_matrix(A), directed=False)
rows = []
for c in np.unique(comp):
    idx = np.where(comp == c)[0]
    if len(idx) < 2:
        continue
    rows.append({"size": len(idx), "pages": len(set(pg[idx])), "labels": len(set(lb[idx])), "span_h": float(t[idx].max() - t[idx].min()),
                 "family": int(W.family.iloc[idx].mode().iloc[0])})
C = pd.DataFrame(rows).sort_values("size", ascending=False)
C.to_csv(OUT / "posthoc_l1_components_half0.csv", index=False)
res = {"components": int(len(C)), "items_in_components": int(C["size"].sum()),
       "share_components_span_lt_1h": float((C.span_h < 1).mean()), "share_components_span_lt_10min": float((C.span_h < 1 / 6).mean()),
       "median_component_span_min": float(C.span_h.median() * 60), "largest_component_size": int(C["size"].max()),
       "share_items_in_largest": float(C["size"].max() / C["size"].sum()),
       "components_span_gt_24h": int((C.span_h > 24).sum())}
print(json.dumps(res, indent=1)); print(C.head(15).to_string())
# (b) L2 low length-CV tercile
cw = list(sio.read_jsonl_gz(RAW / "cw_revisions.jsonl.gz"))
I = wiki.intro_frame(cw); F = wiki.window_filter(I); msk = wiki.Masker(F.label)
body = {r["rev_id"]: wiki.get_body(r) for r in cw}
F = F.assign(m=[msk(body[r]) for r in F.rev_id]); F = F[F.m.str.split().str.len() >= 8]
P = pd.read_csv(OUT / "l2_half0_pages.csv")
cv = {p: (lambda L: float(np.std(L) / np.mean(L)))(F[F.page_id == p].m.str.len().values.astype(float)) for p in P.page}
P["len_cv"] = P.page.map(cv)
q = P.len_cv.quantile(1 / 3); S = P[P.len_cv <= q]; d = S.abs_ser - S.abs_len
res2 = {"pages_low_cv_tercile": int(len(S)), "cv_cut": float(q), "median_abs_ser": float(S.abs_ser.median()), "median_abs_len": float(S.abs_len.median()),
        "median_diff": float(d.median()), "share_ser_gt_len": float((d > 0).mean()), "wilcoxon_greater_p": float(wilcoxon(d, alternative="greater").pvalue)}
print(json.dumps(res2, indent=1))
(OUT / "posthoc_half0.json").write_text(json.dumps({"L1_components": res, "L2_low_cv": res2}, indent=1))
