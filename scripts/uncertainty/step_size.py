"""Descriptive anchor for factor 2: per-copy step size in real families = Jaccard (k=3) distance from each
representative to its most similar EARLIER representative in the same family (an upper bound on a parent-child
distance). No lag-association statistic is computed."""
import numpy as np, pandas as pd
from common import load_D, real_fams_multiday, fm, OUT
NAMES = {5455: "data-link lists", 6843: "default-page text", 2842: "round-status reports", 2378: "archival link lists"}
rows = []
for f, s in real_fams_multiday(load_D()).items():
    sets = [fm.shingle_set(t, 3) for t in s.m]
    nn = [min(1 - len(sets[i] & sets[j]) / max(1, len(sets[i] | sets[j])) for j in range(i)) for i in range(1, len(sets))]
    nn = np.array(nn)
    rows.append({"family": NAMES[f], "reps": len(s), "median_nn_earlier_dist": round(float(np.median(nn)), 3),
                 "mean": round(float(nn.mean()), 3), "share_exact_0": round(float((nn == 0).mean()), 3),
                 "q25": round(float(np.quantile(nn, .25)), 3), "q75": round(float(np.quantile(nn, .75)), 3)})
S = pd.DataFrame(rows); print(S.to_string(index=False)); S.to_csv(OUT / "real_step_size.csv", index=False)
