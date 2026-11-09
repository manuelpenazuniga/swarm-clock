"""Factor 3 pilot: D13 end-to-end power under other family definitions. For config (k, thr): build that config's
families on the real corpus, take ITS multi-day eligible families (>= 15 pages, >= 2 dates) as sampling templates,
plant token-edit clocks in all of them, rebuild LSH with the same (k, thr), D13 recovery rule (min_blocks), pooled
long-lag test (Jaccard k = 3 distance, length strata, B = 99). Includes k3 t0.3 as a reproduction check of D13.
No real-data distance-vs-lag statistic is computed. Usage: python pilot_grid_power.py "<k:thr,...>" <rates> <reps> [min_blocks]"""
import sys, time
import numpy as np, pandas as pd
from common import load_R, real_fams_multiday, rng_for, plant_rows, rebuild_and_recover, fm, stt, Synth, OUT


def main():
    cfgs = [(int(a), float(b)) for a, b in (c.split(":") for c in sys.argv[1].split(","))]
    rates, REPS = [float(x) for x in sys.argv[2].split(",")], int(sys.argv[3])
    minb = int(sys.argv[4]) if len(sys.argv) > 4 else 15
    R = load_R(); rows = []; mh = {}
    for k, thr in cfgs:
        if k not in mh:
            mh[k] = fm.minhashes(R.m, k)
        D, _ = fm.family_table(R, fm.assign_families(mh[k], thr))
        RF = list(real_fams_multiday(D, minb).values())
        for p in rates:
            rng = rng_for(f"grid_{k}_{thr}_{p}_{minb}"); S = Synth(R, rng); t0 = time.time(); det, rec = [], []
            for rep in range(REPS):
                Pl = pd.concat([plant_rows(S.synth_like(sub, p), li) for li, sub in enumerate(RF)], ignore_index=True)
                got = rebuild_and_recover(R, mh[k], Pl, range(len(RF)), k=k, thr=thr, min_blocks=minb)
                rec.append(len(got))
                pv = stt.window_test(list(got.values()), 6, 1e9, rng, B=99)[1] if got else np.nan
                det.append(bool(pv < .05) if pv == pv else False)
            rows.append({"k": k, "thr": thr, "min_blocks": minb, "templates": len(RF),
                         "template_pages": "/".join(str(len(s)) for s in RF), "rate": p, "reps": REPS,
                         "lineage_recovery": round(float(np.mean(rec)) / max(1, len(RF)), 3),
                         "end_to_end_reject": float(np.mean(det)), "sec_per_rep": round((time.time() - t0) / REPS, 2)})
            print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(OUT / f"grid_power_{sys.argv[1].replace(':', '-').replace(',', '_')}_{sys.argv[2].replace(',', '_')}_r{REPS}_mb{minb}.csv", index=False)


if __name__ == "__main__":
    main()
