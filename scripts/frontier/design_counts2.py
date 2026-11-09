"""Outcome-blind: full-corpus components of the cross-label near-duplicate graph, split by component."""
from common import *
from scipy.sparse.csgraph import connected_components
D = load_wiki()
for name, keep in [("all", np.ones(len(D), bool)), ("r2", (~D.burst & ~D.tmpl).values)]:
    W = D[keep].reset_index(drop=True)
    X, sets, _ = shingle_matrix(W.m.tolist()); J = jaccard_from(X)
    pg, lb = W.page_id.values, W.label.values
    el = (pg[:, None] != pg[None, :]) & (lb[:, None] != lb[None, :])
    L = W.m.str.len().values.astype(float); bal = np.abs(np.log(L[:, None] / L[None, :])) <= 0.1
    iu = np.triu_indices(len(W), 1)
    for lo in (0.2, 0.3, 0.5):
        m = el & (J >= lo) & (J < 0.999)
        A = sp.csr_matrix(np.triu(m, 1)); nc, lab = connected_components(A + A.T, directed=False)
        r, c = A.nonzero(); comps = lab[r]
        # component split key: crc32 of smallest page_id in component
        cmin = {}
        for i in np.unique(np.concatenate([r, c])):
            cmin[lab[i]] = min(cmin.get(lab[i], "~"), pg[i])
        ck = np.array([zlib.crc32(cmin[x].encode()) % 2 for x in comps])
        sizes = np.bincount(comps)
        print(name, lo, "pairs", len(r), "balanced", int(bal[r, c].sum()), "components", len(np.unique(comps)),
              "pairs half0/1", int((ck == 0).sum()), int((ck == 1).sum()),
              "comps half0/1", len(np.unique(comps[ck == 0])), len(np.unique(comps[ck == 1])), "max comp pairs", int(sizes.max()))
