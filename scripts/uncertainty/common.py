"""Shared helpers for the uncertainty pilots. Imports the frozen project code read-only; writes only to this folder.
SAFETY: reads only data/interim/wiki_intros.parquet and D_primary.parquet (masked wiki introductions)."""
import sys, time, zlib
from pathlib import Path
PROJ = Path("/Volumes/MacMiniExt/dev/research/SwarmAlignmentHackathon/swarm-clock-project")
sys.path.insert(0, str(PROJ / "src"))
import numpy as np
import pandas as pd
from swarmclock import families as fm, stats as stt, wiki
from swarmclock.io import INTERIM, SEED
from swarmclock.synth import Synth

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)


def load_R():  # identical to scripts/run_stage.py::load_R
    F = pd.read_parquet(INTERIM / "wiki_intros.parquet")
    R = F[~F.page_id.isin(wiki.HUBS)].reset_index(drop=True)[["rev_id", "page_id", "label", "t", "m"]]
    R["t"] = pd.to_datetime(R.t, utc=True)
    return R


def load_D(name="D_primary"):
    D = pd.read_parquet(INTERIM / f"{name}.parquet")
    D["t"] = pd.to_datetime(D.t, utc=True)
    return D


def elig_ids(D, min_blocks=15):
    _, g = fm.family_table(D.drop(columns="family"), D.family.values)
    return g[g.blocks >= min_blocks].sort_values("blocks", ascending=False).index


def real_fams_multiday(D, min_blocks=15):  # identical to run_stage._real_fams_multiday (parametrised)
    X = fm.reps_with_strata(D, elig_ids(D, min_blocks), "length")
    RF = {f: X[X.family == f].sort_values("t").reset_index(drop=True) for f in X.family.unique()}
    return {f: s for f, s in RF.items() if s.t.dt.date.nunique() >= 2}


def rng_for(tag):
    """Documented offset: SEED + crc32(tag) % 1000 (same convention as power_end_to_end)."""
    return np.random.default_rng(SEED + zlib.crc32(tag.encode()) % 1000)


def plant_rows(syn, li):
    return pd.DataFrame({"rev_id": [f"E2E{li}_{i}" for i in range(len(syn))], "page_id": [f"E2E/{li}_{i}" for i in range(len(syn))],
                         "label": syn.label.values, "t": pd.to_datetime(syn.t.values, utc=True), "m": syn.m.values, "lin": li})


def rebuild_and_recover(R, mh_real, Pl, lins, k=3, thr=0.3, min_blocks=15, mh_fn=None):
    """Exactly the D13 recovery rule: >= 80% of planted members in one family with >= min_blocks blocks;
    returns {lin: pair arrays of planted members only (length strata recomputed)} for recovered lineages."""
    A = pd.concat([R.assign(lin=-1), Pl], ignore_index=True)
    fam = fm.assign_families(mh_real + fm.minhashes(Pl.m, k), thr)
    D, g = fm.family_table(A[["rev_id", "page_id", "label", "t", "m"]], fam)
    D["lin"] = A.lin.values
    out = {}
    for li in lins:
        mem = D[D.lin == li]; f = mem.family.mode().iloc[0]
        if (mem.family == f).mean() >= .8 and g.loc[f, "blocks"] >= min_blocks:
            only = D[(D.lin == li) & (D.family == f)]
            out[li] = fm.fam_pairs(fm.reps_with_strata(only, [f], "length"))
    return out


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))
