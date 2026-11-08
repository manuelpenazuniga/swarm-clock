"""Temporal-association statistics and stratified permutation nulls (frozen methodology)."""
import numpy as np
from scipy.stats import rankdata

BINS = [0, 1 / 6, 0.5, 1, 3, 6, 12, 24, 72, 1e9]
BIN_LABELS = ["<10m", "10-30m", "30m-1h", "1-3h", "3-6h", "6-12h", "12-24h", "1-3d", ">3d"]
WIN = [("short (<6h)", 0, 6), ("long (>=6h)", 6, 1e9), ("very long (>=24h)", 24, 1e9)]


def _permute_within(t, strata, rng):
    t = t.copy()
    for s in np.unique(strata):
        idx = np.where(strata == s)[0]
        t[idx] = t[rng.permutation(idx)]
    return t


# ---- whole-family statistic (Part 2b/2c) ----
def stat(arrs, times=None):
    vals = []
    for a, t in zip(arrs, times or [a["t"] for a in arrs]):
        dt_ = np.abs(t[a["iu"][0]] - t[a["iu"][1]])
        if np.ptp(dt_) == 0 or np.ptp(a["rd"]) == 0:
            continue
        vals.append(np.corrcoef(a["rd"], rankdata(dt_))[0, 1])
    return (np.mean(vals) if vals else np.nan), vals


def perm_test(arrs, rng, B=999):
    obs, per_family = stat(arrs)
    if np.isnan(obs):
        return np.nan, np.nan, per_family
    null = np.empty(B)
    for b in range(B):
        null[b] = stat(arrs, [_permute_within(a["t"], a["strata"], rng) for a in arrs])[0]
    null = null[~np.isnan(null)]
    return obs, (1 + np.sum(null >= obs)) / (len(null) + 1), per_family


# ---- lag-window statistic (Part 2d/3a) ----
def lag_curve(P):
    lag = np.abs(P["t"][P["i"]] - P["t"][P["j"]])
    b = np.digitize(lag, BINS) - 1
    return np.array([P["d"][b == k].mean() if (b == k).sum() >= 5 else np.nan for k in range(len(BIN_LABELS))])


def rho_window(P, t, lo, hi, cross=False):
    lag = np.abs(t[P["i"]] - t[P["j"]])
    m = (lag >= lo) & (lag < hi)
    if cross:
        m &= ~P["same_label"]
    if m.sum() < 10 or np.ptp(lag[m]) == 0 or np.ptp(P["d"][m]) == 0:
        return np.nan
    return np.corrcoef(rankdata(P["d"][m]), rankdata(lag[m]))[0, 1]


def window_test(Ps, lo, hi, rng, B=999, cross=False):
    obs_v = [rho_window(P, P["t"], lo, hi, cross) for P in Ps]
    obs = np.nanmean(obs_v) if np.any(~np.isnan(obs_v)) else np.nan
    if np.isnan(obs):
        return np.nan, np.nan, obs_v
    null = []
    for _ in range(B):
        vals = [rho_window(P, _permute_within(P["t"], P["strata"], rng), lo, hi, cross) for P in Ps]
        if np.any(~np.isnan(vals)):
            null.append(np.nanmean(vals))
    null = np.array(null)
    return obs, (1 + np.sum(null >= obs)) / (len(null) + 1), obs_v


def sig_rate(s):
    s = s.dropna()
    return round(float(np.mean(s < .05)), 2) if len(s) else np.nan
