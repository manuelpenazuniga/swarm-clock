"""Content families (MinHash LSH + union-find), dependency blocks, representatives, pair arrays."""
import numpy as np
import pandas as pd
from datasketch import MinHash, MinHashLSH
from scipy.stats import rankdata
from .io import hours

NPERM = 128


def shingle_set(t, k):
    toks = t.split()
    return {" ".join(toks[j:j + k]) for j in range(max(1, len(toks) - k + 1))}


def minhash(s):
    m = MinHash(num_perm=NPERM)
    for x in s:
        m.update(x.encode())
    return m


def minhashes(texts, k):
    return [minhash(shingle_set(t, k)) for t in texts]


def assign_families(mhs, thr):
    lsh = MinHashLSH(threshold=thr, num_perm=NPERM)
    for i, m in enumerate(mhs):
        lsh.insert(str(i), m)
    par = list(range(len(mhs)))

    def fd(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for i, m in enumerate(mhs):
        for j in lsh.query(m):
            a, b = fd(i), fd(int(j))
            if a != b:
                par[a] = b
    return np.array([fd(i) for i in range(len(mhs))])


def family_table(df, fam):
    """blocks = distinct pages per family (2b definition)."""
    D = df.assign(family=fam)
    g = D.groupby("family").agg(blocks=("page_id", "nunique"), labels=("label", "nunique"),
                                t0=("t", "min"), t1=("t", "max"))
    g["span_h"] = (g.t1 - g.t0).dt.total_seconds() / 3600
    g["days"] = D.groupby("family").t.apply(lambda s: s.dt.date.nunique())
    return D, g


def reps_with_strata(D, fam_ids, mode="length"):
    """One date-blind representative per (family, page): the longest introduction."""
    X = D[D.family.isin(fam_ids)].copy()
    X["len"] = X.m.str.len()
    X = X.sort_values(["family", "page_id", "len", "rev_id"], ascending=[True, True, False, True]).drop_duplicates(["family", "page_id"])
    lt = X.groupby("family")["len"].transform(
        lambda s: pd.qcut(s.rank(method="first"), 3, labels=False) if len(s) >= 6 else 0).astype(int).astype(str)
    day = X.t.dt.strftime("%Y-%m-%d")
    X["stratum"] = {"length": lt, "day": day, "day_length": day + "_" + lt}[mode].values
    return X


def jaccard_dist(sets, i, j):
    return np.array([1 - len(sets[a] & sets[b]) / max(1, len(sets[a] | sets[b])) for a, b in zip(i, j)])


def family_arrays(X, k=3):
    """Arrays for the whole-family statistic (Part 2b/2c)."""
    out = []
    for f, sub in X.groupby("family"):
        sets = [shingle_set(t, k) for t in sub.m]; n = len(sets)
        iu = np.triu_indices(n, 1)
        d = jaccard_dist(sets, *iu)
        out.append({"f": f, "rd": rankdata(d), "t": hours(sub.t), "strata": sub.stratum.values, "iu": iu})
    return out


def fam_pairs(sub, k=3, dist=None):
    """Pair arrays for window tests (Part 2d/3a). dist(texts, i, j) overrides Jaccard."""
    n = len(sub)
    i, j = np.triu_indices(n, 1)
    if dist is None:
        sets = [shingle_set(t, k) for t in sub.m]
        d = jaccard_dist(sets, i, j)
    else:
        d = dist(sub.m.values, i, j)
    lab = sub.label.values
    return {"d": d, "t": hours(sub.t), "i": i, "j": j, "same_label": lab[i] == lab[j],
            "strata": sub.stratum.values if "stratum" in sub else np.zeros(n)}
