"""Shared helpers for frontier pilots. Read-only on the project."""
import sys, zlib
from pathlib import Path
PROJ = Path("/Volumes/MacMiniExt/dev/research/SwarmAlignmentHackathon/swarm-clock-project")
sys.path.insert(0, str(PROJ / "src"))
import numpy as np, pandas as pd, scipy.sparse as sp
from swarmclock import families as fm, wiki
from swarmclock.io import hours
OUT = Path(__file__).resolve().parents[1] / "out"; OUT.mkdir(exist_ok=True)

def load_wiki():
    D = pd.read_parquet(PROJ / "data/interim/D_primary.parquet"); D["t"] = pd.to_datetime(D.t, utc=True)
    D["half"] = [zlib.crc32(p.encode()) % 2 for p in D.page_id]
    fp = D.groupby("family").page_id.nunique(); burst = fp[fp == 314].index.tolist()
    D["burst"] = D.family.isin(burst); D["tmpl"] = D.m.str.contains(wiki.TEMPLATE)
    D["h"] = hours(D.t)
    return D.reset_index(drop=True)

def shingle_matrix(texts, k=3):
    vocab, rows, cols = {}, [], []
    sets = []
    for i, t in enumerate(texts):
        s = fm.shingle_set(t, k); sets.append(s)
        for x in s:
            rows.append(i); cols.append(vocab.setdefault(x, len(vocab)))
    X = sp.csr_matrix((np.ones(len(rows), dtype=np.float32), (rows, cols)), shape=(len(texts), len(vocab)))
    X.data[:] = 1.0
    return X, sets, vocab

def jaccard_from(X):
    inter = (X @ X.T).toarray(); sz = np.asarray(X.sum(1)).ravel()
    return inter / np.maximum(1, sz[:, None] + sz[None, :] - inter)
