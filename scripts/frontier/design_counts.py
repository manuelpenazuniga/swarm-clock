"""Outcome-blind design counts (no timestamps used)."""
from common import *
from scipy.sparse.csgraph import connected_components
D = load_wiki()
print("items", len(D), "by half", D.half.value_counts().to_dict(), "burst", D.burst.sum(), "tmpl", D.tmpl.sum())
for half in (0, 1):
    for name, keep in [("all", np.ones(len(D), bool)), ("r2", (~D.burst & ~D.tmpl).values)]:
        W = D[(D.half == half).values & keep].reset_index(drop=True)
        X, sets, _ = shingle_matrix(W.m.tolist()); J = jaccard_from(X)
        pg, lb = W.page_id.values, W.label.values
        el = (pg[:, None] != pg[None, :]) & (lb[:, None] != lb[None, :])
        L = W.m.str.len().values.astype(float)
        bal = np.abs(np.log(L[:, None] / L[None, :])) <= 0.1
        iu = np.triu_indices(len(W), 1)
        for lo in (0.3, 0.5):
            m = el & (J >= lo) & (J < 0.999)
            A = sp.csr_matrix(np.triu(m, 1))
            ncomp, lab = connected_components(A + A.T, directed=False)
            inv = np.unique(lab[np.unique(np.concatenate([A.nonzero()[0], A.nonzero()[1]]))])
            sizes = np.bincount(lab)[inv]
            print(half, name, lo, "pairs", int(m[iu].sum()), "balanced", int((m & bal)[iu].sum()),
                  "items_in_pairs", int(sizes.sum()), "components", len(inv), "max_comp", int(sizes.max()) if len(sizes) else 0,
                  "identical_pairs", int((el & (J >= 0.999))[iu].sum()))
