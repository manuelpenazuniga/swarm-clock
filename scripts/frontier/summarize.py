"""Collect D/H direction accuracies and simulation controls into one table."""
import json
from common import *
rows = []
for s in (0, 1):
    r = json.load(open(OUT / f"d_direction_split{s}_r2.json"))
    for sub in ("all_pairs", "length_balanced", "lag<1h", "lag>=1h"):
        for sc, v in r[sub].items():
            rows.append({"line": "D (main, r2)", "split": s, "subset": sub, "score": sc, "acc": v["acc"], "ci_lo": v["ci"][0], "ci_hi": v["ci"][1], "pairs": v["pairs"], "components": v["components"]})
h = json.load(open(OUT / "h_hubs.json"))
for sub in ("all", "lag<10min", "lag>=10min"):
    for sc, v in h[sub].items():
        rows.append({"line": "H (hubs, held out)", "split": "-", "subset": sub, "score": sc, "acc": v["acc"], "ci_lo": v["ci"][0], "ci_hi": v["ci"][1], "pairs": v["pairs"], "components": v["components"]})
for f, edit in (("d_positive_control.csv", "token"), ("d_positive_control_donor.csv", "donor_block")):
    for _, x in pd.read_csv(OUT / f).iterrows():
        for sc in ("S0_length", "S1_polarity", "S2_novelty", "S3_centrality"):
            if sc in x and x[sc] == x[sc]:
                rows.append({"line": f"SIM {x['model']} ({edit})", "split": f"p={x['p']}", "subset": "all", "score": sc, "acc": x[sc], "pairs": x["pairs"], "components": x["clusters_with_pairs"]})
pd.DataFrame(rows).to_csv(OUT / "direction_summary.csv", index=False)
print(len(rows), "rows")
