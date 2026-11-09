"""Aggregate pilot CSVs into summary tables with Wilson 95% intervals."""
import glob, json
import numpy as np, pandas as pd
from common import OUT, wilson

NAMES = {5455: "data-link lists", 6843: "default-page text", 2842: "round-status reports", 2378: "archival link lists"}
rows = []
for f in sorted(glob.glob(str(OUT / "single_family_*_r*.csv"))):
    X = pd.read_csv(f)
    for (fam, p), g in X.groupby(["family", "rate"]):
        n = len(g)
        def rate(col, a=0.05):
            k = int((g[col].fillna(1) < a).sum()) if col in g else 0
            return f"{k / n:.2f} {wilson(k, n)}"
        def brate(col):
            k = int(g[col].sum()); return f"{k / n:.2f} {wilson(k, n)}"
        rows.append({"clock_in": NAMES.get(fam, fam), "rate": p, "reps": n, "recovered": round(g.clock_recovered.mean(), 2),
                     "pooled_equal_realistic": rate("p_eq_real"), "pooled_pairweighted_realistic": rate("p_pw_real"),
                     "per_family_a0.05": rate("p_clock_family"), "holm4_lowerbound_(p<=0.0125)": rate("p_clock_family", 0.0125),
                     "pooled_equal_generic": rate("p_eq_gen"), "pooled_pairweighted_generic": rate("p_pw_gen"),
                     "holm4_generic": brate("holm4_clock"), "holm4_FWER_from_stars": brate("holm4_any_star"),
                     "rho_clock_median": round(g.rho_clock.median(), 3) if "rho_clock" in g else np.nan,
                     "null_sd_rho_clock": round(g.null_sd_clock.median(), 3) if "null_sd_clock" in g else np.nan})
S1 = pd.DataFrame(rows); S1.to_csv(OUT / "summary_single_family.csv", index=False)
print(S1.to_string(index=False))

# star null SD per family sampling (noise scale of a per-family long-lag rho with no clock)
sds = {}
for f in sorted(glob.glob(str(OUT / "single_family_*_r*.csv"))):
    for s in pd.read_csv(f).star_null_sd.dropna():
        for k, v in json.loads(s).items():
            sds.setdefault(NAMES.get(int(k), k), []).append(v)
print("\nnull SD of long-lag rho under no clock (median over star lineages):",
      {k: round(float(np.nanmedian(v)), 3) for k, v in sds.items()})

rows = []
for f in sorted(glob.glob(str(OUT / "edit_model_*.csv"))):
    for _, r in pd.read_csv(f).iterrows():
        k = int(round(r.end_to_end_reject * r.reps))
        rows.append({**r.to_dict(), "ci": wilson(k, int(r.reps))})
if rows:
    S2 = pd.DataFrame(rows).sort_values(["model", "rate"]); S2.to_csv(OUT / "summary_edit_model.csv", index=False)
    print(S2.to_string(index=False))

rows = []
for f in sorted(glob.glob(str(OUT / "grid_power_*.csv"))):
    for _, r in pd.read_csv(f).iterrows():
        k = int(round(r.end_to_end_reject * r.reps))
        rows.append({**r.to_dict(), "ci": wilson(k, int(r.reps))})
if rows:
    S3 = pd.DataFrame(rows); S3.to_csv(OUT / "summary_grid_power.csv", index=False)
    print(S3.to_string(index=False))
