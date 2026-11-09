"""L2 within-document order (PREREG_POSITIVE_LINE.md). Usage: python l2_order.py <wiki_half 0|1>
Read-only on the project; writes only to ./out/."""
import sys, json, zlib
from pathlib import Path
PROJ = Path("/Volumes/MacMiniExt/dev/research/SwarmAlignmentHackathon/swarm-clock-project")
sys.path.insert(0, str(PROJ / "src"))
import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.stats import spearmanr, pearsonr, wilcoxon
from swarmclock import io as sio, wiki, families as fm
from swarmclock.io import RAW, hours

OUT = Path(__file__).resolve().parent / "out"; OUT.mkdir(exist_ok=True)
HALF = int(sys.argv[1])


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


# identical construction to stage positive_control_bodies (PREREG_EXTENSIONS2 P)
cw = list(sio.read_jsonl_gz(RAW / "cw_revisions.jsonl.gz"))
I = wiki.intro_frame(cw); F = wiki.window_filter(I)
msk = wiki.Masker(F.label)
body = {r["rev_id"]: wiki.get_body(r) for r in cw}
F = F.assign(m=[msk(body[r]) for r in F.rev_id])
F = F[F.m.str.split().str.len() >= 8]
cnt = F.page_id.value_counts(); pages = cnt[cnt >= 15].index
pages = [p for p in pages if zlib.crc32(p.encode()) % 2 == HALF]
rows = []
for p in pages:
    X = F[F.page_id == p].sort_values(["t", "rev_id"]).reset_index(drop=True)
    th = hours(X.t); th = th - th[0]
    J = jaccard_matrix(X.m.tolist())
    S = J.copy(); np.fill_diagonal(S, 0)
    Lap = np.diag(S.sum(1)) - S
    w, V = np.linalg.eigh(Lap)
    fied = V[:, 1]
    L = X.m.str.len().values.astype(float)
    r_ser = spearmanr(fied, th).correlation
    r_len = spearmanr(L, th).correlation
    d0 = 1 - J[0]
    idx = np.arange(len(X))
    r_time = pearsonr(d0[1:], th[1:])[0] if np.ptp(d0[1:]) > 0 else np.nan
    r_index = pearsonr(d0[1:], idx[1:])[0] if np.ptp(d0[1:]) > 0 else np.nan
    rows.append({"page": p, "n_rev": len(X), "span_h": float(th[-1]), "labels": X.label.nunique(),
                 "rho_ser": r_ser, "rho_len": r_len, "abs_ser": abs(r_ser) if r_ser == r_ser else np.nan,
                 "abs_len": abs(r_len) if r_len == r_len else np.nan,
                 "r_root_to_tip_time": r_time, "r_root_to_tip_index": r_index, "zero_conn_share": float((S.sum(1) == 0).mean())})
R = pd.DataFrame(rows)
R.to_csv(OUT / f"l2_half{HALF}_pages.csv", index=False)
ok = R.dropna(subset=["abs_ser", "abs_len"])
diff = ok.abs_ser - ok.abs_len
summ = {"half": HALF, "pages": int(len(R)), "pages_valid": int(len(ok)),
        "median_abs_rho_ser": float(ok.abs_ser.median()), "median_abs_rho_len": float(ok.abs_len.median()),
        "median_diff": float(diff.median()), "share_ser_gt_len": float((diff > 0).mean()),
        "wilcoxon_greater_p": float(wilcoxon(diff, alternative="greater").pvalue) if (diff != 0).any() else None}
sub = ok[ok.abs_len < 0.5]; dsub = sub.abs_ser - sub.abs_len
summ["subset_abs_len_lt_0.5"] = {"pages": int(len(sub)), "median_abs_rho_ser": float(sub.abs_ser.median()) if len(sub) else None,
                                 "median_abs_rho_len": float(sub.abs_len.median()) if len(sub) else None,
                                 "median_diff": float(dsub.median()) if len(sub) else None,
                                 "wilcoxon_greater_p": float(wilcoxon(dsub, alternative="greater").pvalue) if len(sub) >= 5 and (dsub != 0).any() else None}
summ["root_to_tip"] = {"median_r_time": float(R.r_root_to_tip_time.median()), "median_r_index": float(R.r_root_to_tip_index.median()),
                       "share_index_gt_time": float((R.r_root_to_tip_index > R.r_root_to_tip_time).mean())}
print(json.dumps(summ, indent=1))
(OUT / f"l2_half{HALF}.json").write_text(json.dumps(summ, indent=1))
