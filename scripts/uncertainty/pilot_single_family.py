"""Factor 1 pilot: a token-edit clock in ONE family only, end to end (D13 machinery).
Per replicate: plant a clock lineage with family f's real times/labels/size (root = earliest introduction) AND star
lineages (no clock, rate 3p as in D13) for the other three multi-day families; one LSH rebuild of the whole corpus;
D13 recovery rule. Tests (long window >= 6 h, length strata, one shared set of B joint permutations):
  realistic  = clock lineage f + the three OTHER REAL families as observed (their published rho), equal-weight mean
               (the paper's pooled T) and pair-weighted mean;
  generic    = clock lineage f + the three recovered star lineages (equal-weight and pair-weighted);
  per-family = clock lineage f alone; reported at alpha 0.05 and 0.0125 (Bonferroni/Holm first step, m = 4);
  holm4      = Holm over {clock, 3 stars} (unrecovered lineage -> p = 1), m = 4 fixed.
A non-recovered clock counts as no detection (as in D13). Real-family per-family p-values are NOT computed.
Usage: python pilot_single_family.py <family_id> <rates comma> <reps> [B]"""
import sys, time, json
import numpy as np, pandas as pd
from scipy.stats import rankdata
from common import load_R, load_D, real_fams_multiday, rng_for, plant_rows, rebuild_and_recover, fm, stt, Synth, OUT

LO, HI = 6, 1e9


def rho_n(P, t):
    lag = np.abs(t[P["i"]] - t[P["j"]]); m = (lag >= LO) & (lag < HI); n = int(m.sum())
    if n < 10 or np.ptp(lag[m]) == 0 or np.ptp(P["d"][m]) == 0:
        return np.nan, n
    return np.corrcoef(rankdata(P["d"][m]), rankdata(lag[m]))[0, 1], n


def draws(P, rng, B):
    obs = rho_n(P, P["t"])
    null = np.array([rho_n(P, stt._permute_within(P["t"], P["strata"], rng)) for _ in range(B)], float)
    return np.array(obs, float), null  # (2,), (B, 2)


def pooled(items, weighted=False):
    """items: list of (obs(2,), null(B,2)). Returns (T_obs, p) with window_test semantics."""
    if not items:
        return np.nan, np.nan
    O = np.array([o for o, _ in items]); N = np.stack([n for _, n in items], 1)  # O (F,2), N (B,F,2)

    def agg(r, w):
        ok = ~np.isnan(r)
        if not ok.any():
            return np.nan
        return np.sum(r[ok] * w[ok]) / np.sum(w[ok]) if weighted else np.mean(r[ok])
    T = agg(O[:, 0], O[:, 1])
    if np.isnan(T):
        return np.nan, np.nan
    nb = np.array([agg(N[b, :, 0], N[b, :, 1]) for b in range(N.shape[0])]); nb = nb[~np.isnan(nb)]
    return T, (1 + np.sum(nb >= T)) / (len(nb) + 1)


def pfam(item):
    (o, n) = item
    if np.isnan(o[0]):
        return np.nan
    nb = n[:, 0][~np.isnan(n[:, 0])]
    return (1 + np.sum(nb >= o[0])) / (len(nb) + 1)


def holm_rejects(ps, idx, alpha=0.05):
    ps = np.array([1.0 if (p != p) else p for p in ps]); order = np.argsort(ps); m = len(ps)
    for r, k in enumerate(order):
        if ps[k] > alpha / (m - r):
            return False
        if k == idx:
            return True
    return False


def main():
    fam_id, rates, REPS = int(sys.argv[1]), [float(x) for x in sys.argv[2].split(",")], int(sys.argv[3])
    B = int(sys.argv[4]) if len(sys.argv) > 4 else 399
    R = load_R(); D = load_D(); RF = real_fams_multiday(D); fids = list(RF)
    assert fam_id in fids, fids
    REALP = {f: fm.fam_pairs(s) for f, s in RF.items()}
    mh_real = fm.minhashes(R.m, 3)
    rows = []
    for p in rates:
        rng = rng_for(f"single_{fam_id}_{p}"); S = Synth(R, rng)
        t0 = time.time()
        for rep in range(REPS):
            parts = []
            for li, f in enumerate(fids):
                syn = S.synth_like(RF[f], p) if f == fam_id else S.star_like(RF[f], p)
                parts.append(plant_rows(syn, li))
            Pl = pd.concat(parts, ignore_index=True)
            rec = rebuild_and_recover(R, mh_real, Pl, range(len(fids)))
            ci = fids.index(fam_id)
            dr = {li: draws(P, rng, B) for li, P in rec.items()}
            real_other = [draws(REALP[f], rng, B) for f in fids if f != fam_id]
            row = {"family": fam_id, "rate": p, "rep": rep, "clock_recovered": ci in rec,
                   "stars_recovered": sum(li in rec for li in range(len(fids)) if li != ci)}
            if ci in rec:
                c = dr[ci]
                row.update(rho_clock=c[0][0], npairs_clock=c[0][1], p_clock_family=pfam(c),
                           null_sd_clock=float(np.nanstd(c[1][:, 0])))
                row["T_eq_real"], row["p_eq_real"] = pooled([c] + real_other)
                row["T_pw_real"], row["p_pw_real"] = pooled([c] + real_other, weighted=True)
            stars = [dr[li] for li in rec if li != ci]
            gen = ([dr[ci]] if ci in rec else []) + stars
            row["p_eq_gen"] = pooled(gen)[1]; row["p_pw_gen"] = pooled(gen, weighted=True)[1]
            ps4 = [pfam(dr[li]) if li in rec else 1.0 for li in range(len(fids))]
            row["p_all4"] = json.dumps([None if x != x else round(float(x), 4) for x in ps4])
            row["holm4_clock"] = holm_rejects(ps4, ci) if ci in rec else False
            row["holm4_any_star"] = any(holm_rejects(ps4, li) for li in range(len(fids)) if li != ci)
            row["star_null_sd"] = json.dumps({str(fids[li]): round(float(np.nanstd(dr[li][1][:, 0])), 4) for li in rec if li != ci})
            rows.append(row)
        el = time.time() - t0
        X = pd.DataFrame([r for r in rows if r["rate"] == p])
        det = lambda col, a=0.05: float(np.mean(X[col].fillna(1) < a)) if col in X else 0.0
        print({"family": fam_id, "rate": p, "reps": REPS, "B": B, "recovered": X.clock_recovered.mean(),
               "pooled_eq_real": det("p_eq_real"), "pooled_pw_real": det("p_pw_real"),
               "per_family_a05": det("p_clock_family"), "per_family_a0125": det("p_clock_family", 0.0125),
               "pooled_eq_gen": det("p_eq_gen"), "pooled_pw_gen": det("p_pw_gen"),
               "holm4_clock": X.holm4_clock.mean(), "holm4_any_star_FWER": X.holm4_any_star.mean(),
               "sec_per_rep": round(el / REPS, 2)}, flush=True)
    pd.DataFrame(rows).to_csv(OUT / f"single_family_{fam_id}_{sys.argv[2].replace(',', '_')}_r{REPS}.csv", index=False)


if __name__ == "__main__":
    main()
