"""Factors 3 and 4, STRUCTURE ONLY (no distance-vs-lag statistic is computed on real data, so a later
pre-registration of the real-data grid test stays clean). For each (k, threshold): families, eligible families
(>= 15 and >= 10 pages), chaining flag (largest family > 20% of blocks), multi-day eligible families, and how many
eligible families have >= 10 representative pairs at lag >= 6 h (i.e. would enter the long-lag window test)."""
import time, json
import numpy as np, pandas as pd
from common import load_R, fm, OUT

GRID = [(k, t) for k in (3, 4, 5) for t in (0.25, 0.3, 0.35, 0.4)] + [(3, 0.2)]
R = load_R(); rows = []; cache = {}
for k, thr in GRID:
    t0 = time.time()
    if k not in cache:
        cache[k] = fm.minhashes(R.m, k)
    tm = time.time() - t0
    fam = fm.assign_families(cache[k], thr)
    D, g = fm.family_table(R, fam)
    tl = time.time() - t0 - tm
    largest = g.blocks.idxmax(); share = g.blocks.max() / g.blocks.sum()
    for minb in (15, 10):
        el = g[g.blocks >= minb].sort_values("blocks", ascending=False)
        for excl_giant in ((False, True) if share > 0.2 else (False,)):
            ids = [f for f in el.index if not (excl_giant and f == largest)]
            X = fm.reps_with_strata(D, ids, "length") if ids else None
            longfams, info = 0, {}
            for f in ids:
                sub = X[X.family == f]; th = (sub.t - sub.t.min()).dt.total_seconds().values / 3600
                i, j = np.triu_indices(len(sub), 1); lag = np.abs(th[i] - th[j]); nl = int((lag >= 6).sum())
                info[int(f)] = {"pages": int(len(sub)), "dates": int(sub.t.dt.date.nunique()), "long_pairs": nl}
                longfams += nl >= 10
            rows.append({"k": k, "thr": thr, "min_blocks": minb, "exclude_giant": excl_giant, "families": len(g),
                         "largest_share": round(share, 3), "chaining": share > 0.2, "eligible": len(ids),
                         "multiday_eligible": sum(v["dates"] >= 2 for v in info.values()),
                         "fams_with_ge10_long_pairs": longfams, "minhash_s": round(tm, 1), "lsh_s": round(tl, 1),
                         "families_detail": json.dumps(info)})
            print({k_: v for k_, v in rows[-1].items() if k_ != "families_detail"}, flush=True)
S = pd.DataFrame(rows); S.to_csv(OUT / "structure_grid.csv", index=False)
print(S.drop(columns="families_detail").to_string(index=False))
