"""Factor 2 pilot: a cheaper-than-LLM but more realistic rewrite model, run end to end exactly as D13 (clock planted in
all four multi-day families, LSH rebuilt, D13 recovery rule, pooled long-lag test B = 99).
Edit models (same generation structure as Synth.synth_like: member i copies one of the 5 previous members):
  token        : Synth.mutate (i.i.d. token deletion/substitution/insertion; substitutes drawn from corpus vocabulary)
  block_family : K ~ Poisson(1.5 p n / Lmean) block events per copy (Lmean = 4, block length ~ Geometric):
                 50% replace a block by a contiguous block of a donor text, 25% delete a block, 25% insert a donor block.
                 Donors = the real introductions of the SAME real family (recombination with the family's own phrasing;
                 1.5 p n matches the token model's expected number of touched tokens).
  block_corpus : same, donors = random introductions from the whole corpus (novel phrases).
Also records the realised one-copy parent->child Jaccard distance (k = 3), so models can be compared at matched
per-copy divergence. Usage: python pilot_edit_model.py <model> <rates comma> <reps>"""
import sys, time
import numpy as np, pandas as pd
from common import load_R, load_D, real_fams_multiday, rng_for, plant_rows, rebuild_and_recover, fm, stt, Synth, OUT

LMEAN = 4


def block_mutate(toks, p, donors, rng):
    toks = list(toks); n = max(1, len(toks))
    K = rng.poisson(1.5 * p * n / LMEAN)
    for _ in range(K):
        u = rng.random(); L = int(rng.geometric(1 / LMEAN)); pos = int(rng.integers(0, max(1, len(toks))))
        if u < 0.75:  # replace or delete: remove a block
            del toks[pos:pos + L]
        if u < 0.5 or u >= 0.75:  # replace or insert: add a donor block
            d = donors[rng.integers(len(donors))]
            s = int(rng.integers(0, max(1, len(d) - L + 1))); toks[pos:pos] = d[s:s + L]
    return toks


def lineage(sub, p, model, S, rng, donors, window=5):
    toks0 = sub.m.iloc[0].split(); members, parents = [], []
    for i in range(len(sub)):
        pi = -1 if i == 0 else int(rng.integers(max(0, i - window), i))
        par = toks0 if i == 0 else members[pi]
        members.append(S.mutate(par, p) if model == "token" else block_mutate(par, p, donors, rng))
        parents.append(pi)
    texts = [" ".join(x) for x in members]
    sets = [fm.shingle_set(t, 3) for t in texts]; s0 = fm.shingle_set(sub.m.iloc[0], 3)
    dpc = [1 - len(sets[i] & (s0 if pi < 0 else sets[pi])) / max(1, len(sets[i] | (s0 if pi < 0 else sets[pi])))
           for i, pi in enumerate(parents)]
    return sub.assign(m=texts), float(np.mean(dpc))


def main():
    model, rates, REPS = sys.argv[1], [float(x) for x in sys.argv[2].split(",")], int(sys.argv[3])
    R = load_R(); D = load_D(); RF = real_fams_multiday(D); fids = list(RF)
    fam_donors = {f: [t.split() for t in D[D.family == f].m] for f in fids}
    corpus_donors = [t.split() for t in R.m]
    mh_real = fm.minhashes(R.m, 3); rows = []
    for p in rates:
        rng = rng_for(f"edit_{model}_{p}"); S = Synth(R, rng); t0 = time.time()
        det, rec, dpcs, dlong = [], [], [], []
        for rep in range(REPS):
            parts = []
            for li, f in enumerate(fids):
                donors = fam_donors[f] if model == "block_family" else corpus_donors
                syn, dpc = lineage(RF[f], p, model, S, rng, donors); dpcs.append(dpc)
                parts.append(plant_rows(syn, li))
            Pl = pd.concat(parts, ignore_index=True)
            got = rebuild_and_recover(R, mh_real, Pl, range(len(fids)))
            rec.append(len(got))
            for P in got.values():
                lag = np.abs(P["t"][P["i"]] - P["t"][P["j"]]); m = lag >= 6
                if m.sum() > 10:
                    dlong.append(P["d"][m].mean())
            if got:
                pv = stt.window_test(list(got.values()), 6, 1e9, rng, B=99)[1]
                det.append(bool(pv < .05) if pv == pv else False)
            else:
                det.append(False)
        rows.append({"model": model, "rate": p, "reps": REPS, "lineage_recovery": np.mean(rec) / len(fids),
                     "end_to_end_reject": float(np.mean(det)), "mean_parent_child_dist": round(float(np.mean(dpcs)), 4),
                     "mean_dist_long_lag": round(float(np.mean(dlong)), 3) if dlong else np.nan,
                     "sec_per_rep": round((time.time() - t0) / REPS, 2)})
        print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(OUT / f"edit_model_{model}_{sys.argv[2].replace(',', '_')}_r{REPS}.csv", index=False)


if __name__ == "__main__":
    main()
