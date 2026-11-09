"""swarmclock audit: does artifact content carry chronology in a multi-agent corpus?

Usage:
  swarmclock audit --input corpus.jsonl --actor agent --time ts --text body [--doc page] [--out report_dir]

Steps (the paper's frozen pipeline, generalized):
 1. mask (actor names, URL paths, dates, long tokens, hex hashes, digits); keep texts with >= 8 tokens
 2. content families: MinHash LSH on k-token shingles (default k=3, threshold 0.3), connected components
 3. lineage lifespans (families with >= 5 blocks); eligibility (>= 15 blocks); chaining check
 4. lag-window tests (short / long / very long), all pairs and cross-actor pairs, stratified permutation null
 5. sampling-matched calibration: planted accumulating clocks (power) and planted stars (size) that reuse
    each eligible family's timestamps, actors and size
Outputs: report.md plus CSV tables in --out.
"""
import argparse, json, re, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

from . import families as fm, stats as stt
from .synth import Synth
from .wiki import Masker

HEX = re.compile(r"\b[0-9a-f]{7,}\b")


def read_any(p):
    p = str(p)
    if p.endswith((".jsonl", ".jsonl.gz", ".ndjson")):
        return pd.read_json(p, lines=True)
    if p.endswith(".parquet"):
        return pd.read_parquet(p)
    if p.endswith((".csv", ".csv.gz")):
        return pd.read_csv(p)
    raise SystemExit(f"unsupported input format: {p}")


def parse_time(s, unit):
    if unit == "auto":
        if pd.api.types.is_numeric_dtype(s):
            v = pd.to_numeric(s)
            unit = "ms" if v.median() > 1e11 else "s"
            return pd.to_datetime(v, unit=unit, utc=True)
        return pd.to_datetime(s, utc=True, errors="coerce")
    return pd.to_datetime(pd.to_numeric(s), unit=unit, utc=True)


def prepare(df, actor, tcol, text, doc, time_unit, min_tokens=8):
    X = pd.DataFrame({"label": df[actor].astype(str), "t": parse_time(df[tcol], time_unit), "raw": df[text].astype(str)})
    X["page_id"] = df[doc].astype(str) if doc else [f"r{i}" for i in range(len(df))]
    X["rev_id"] = [f"r{i}" for i in range(len(df))]
    X = X[X.t.notna()]
    mk = Masker(X.label.unique())
    X["m"] = [re.sub(r"\s+", " ", HEX.sub(" <HASH> ", mk(t))).strip() for t in X.raw]
    X = X[X.m.str.split().str.len() >= min_tokens].reset_index(drop=True)
    return X


def run_audit(X, k=3, thr=0.3, min_blocks=15, windows_h=(6, 24), B=999, reps=50, seed=20261108, rates=(0.005, 0.01, 0.02, 0.05, 0.1)):
    rng = np.random.default_rng(seed)
    out = {"n_texts": len(X), "n_actors": int(X.label.nunique()), "span_h": float((X.t.max() - X.t.min()).total_seconds() / 3600)}
    fam = fm.assign_families(fm.minhashes(X.m, k), thr)
    D, g = fm.family_table(X, fam)
    share = g.blocks.max() / g.blocks.sum()
    f5 = g[g.blocks >= 5]
    out["families_ge5"] = len(f5)
    out["lifespan_h_quantiles_ge5"] = {q: round(float(f5.span_h.quantile(q)), 3) for q in (.5, .75, .9)} if len(f5) else {}
    out["largest_family_share"] = round(float(share), 3)
    out["chaining_warning"] = bool(share > .2)
    el = g[g.blocks >= min_blocks].sort_values("blocks", ascending=False)
    out["eligible_families"] = len(el)
    tables = {"families": g.reset_index(), "eligible": el.reset_index()}
    if len(el) == 0:
        out["verdict"] = "no eligible families: content lineages too small to test"
        return out, tables
    Xr = fm.reps_with_strata(D, el.index, "length")
    Ps = [fm.fam_pairs(Xr[Xr.family == f]) for f in Xr.family.unique()]
    lo_w, vl_w = windows_h
    wins = [(f"short (<{lo_w}h)", 0, lo_w), (f"long (>={lo_w}h)", lo_w, 1e9), (f"very long (>={vl_w}h)", vl_w, 1e9)]
    WT = []
    for cross in (False, True):
        for wname, lo, hi in wins:
            T, p, v = stt.window_test(Ps, lo, hi, rng, B=B, cross=cross)
            WT.append({"pairs": "cross-actor" if cross else "all", "window": wname, "T": T, "p": p,
                       "families_with_pairs": int(np.sum(~np.isnan(v)))})
    tables["window_tests"] = pd.DataFrame(WT)
    # sampling-matched calibration on the long window
    S = Synth(X, rng)
    subs = [Xr[Xr.family == f].sort_values("t").reset_index(drop=True) for f in Xr.family.unique()]
    CAL = []
    for kind in ("clock", "star"):
        for p in rates:
            ha, hx = [], []
            for _ in range(reps):
                Pp = [fm.fam_pairs(S.synth_like(s, p) if kind == "clock" else S.star_like(s, p)) for s in subs]
                ha.append(stt.window_test(Pp, lo_w, 1e9, rng, B=99)[1] < .05)
                hx.append(stt.window_test(Pp, lo_w, 1e9, rng, B=99, cross=True)[1] < .05)
            CAL.append({"planted": kind, "edit_rate": p, "reject_long_all": float(np.mean(ha)), "reject_long_cross_actor": float(np.mean(hx)), "reps": reps})
    tables["calibration"] = pd.DataFrame(CAL)
    long_x = tables["window_tests"].query("pairs == 'cross-actor'").iloc[1]
    pw = tables["calibration"].query("planted == 'clock'")
    excl = pw[pw.reject_long_cross_actor >= .8].edit_rate.tolist()
    size = tables["calibration"].query("planted == 'star'").reject_long_cross_actor.max()
    if np.isnan(long_x["T"]):
        out["verdict"] = "long-lag cross-actor test undefined (no eligible family has long-lag cross-actor pairs with varying distance)"
    elif long_x["p"] < .05:
        out["verdict"] = f"cross-actor long-lag temporal signal detected (T={long_x['T']:.3f}, p={long_x['p']:.3f}); check calibration size before interpreting"
    elif excl:
        out["verdict"] = (f"no cross-actor long-lag signal (T={long_x['T']:.3f}, p={long_x['p']:.3f}); accumulating clocks with per-copy edit "
                          f"rates in [{min(excl)}, {max(excl)}] would be detected with >= 80% power, conditional on the lineage still forming one family")
    else:
        out["verdict"] = f"no cross-actor long-lag signal (T={long_x['T']:.3f}, p={long_x['p']:.3f}) but power < 80% at every tested edit rate: inconclusive"
    out["max_star_false_positive_rate"] = float(size)
    return out, tables


def write_report(out, tables, outdir, args):
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    for name, t in tables.items():
        t.to_csv(outdir / f"{name}.csv", index=False)
    (outdir / "summary.json").write_text(json.dumps(out, indent=1, default=str))
    L = ["# swarmclock audit report", "", f"Input: `{args.input}` (actor=`{args.actor}`, time=`{args.time}`, text=`{args.text}`, doc=`{args.doc}`)", "",
         f"**Verdict:** {out['verdict']}", "", "## Corpus", "",
         f"- texts after masking (>= 8 tokens): {out['n_texts']}; actors: {out['n_actors']}; span: {out['span_h']:.1f} h",
         f"- families with >= 5 blocks: {out['families_ge5']}; lifespan quantiles (h): {out['lifespan_h_quantiles_ge5']}",
         f"- eligible families (>= {args.min_blocks} blocks): {out['eligible_families']}; largest family share: {out['largest_family_share']}"
         + (" **(chaining warning: raise the threshold)**" if out["chaining_warning"] else ""), ""]
    if "window_tests" in tables:
        L += ["## Lag-window tests (mean within-family Spearman of distance vs lag; stratified permutation null)", "",
              tables["window_tests"].to_markdown(index=False, floatfmt=".3f"), "",
              "## Sampling-matched calibration (long window; planted lineages reuse each family's times, actors, size)", "",
              tables["calibration"].to_markdown(index=False, floatfmt=".3f"), "",
              f"Max false-positive rate of planted no-clock stars (cross-actor): {out['max_star_false_positive_rate']:.2f} (nominal 0.05).", ""]
    L += ["## How to read this", "",
          "- A positive short-lag statistic that vanishes for cross-actor pairs means similarity comes from actors revising their own text.",
          "- A clock requires a positive long-lag cross-actor statistic AND adequate calibrated power; a null without power is inconclusive.",
          "- Similarity is not transmission: families are candidate reuse, not proof of copying. Actor labels may not be identities.", ""]
    (outdir / "report.md").write_text("\n".join(L))
    return outdir / "report.md"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="swarmclock")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("audit", help="content-chronology audit of a multi-agent corpus")
    a.add_argument("--input", required=True); a.add_argument("--actor", required=True)
    a.add_argument("--time", required=True); a.add_argument("--text", required=True)
    a.add_argument("--doc", default=None, help="optional document/page column: one representative per (family, doc)")
    a.add_argument("--time-unit", default="auto", choices=["auto", "s", "ms", "us", "ns"])
    a.add_argument("--k", type=int, default=3); a.add_argument("--threshold", type=float, default=0.3)
    a.add_argument("--min-blocks", type=int, default=15)
    a.add_argument("--short-window-h", type=float, default=6); a.add_argument("--very-long-window-h", type=float, default=24)
    a.add_argument("--B", type=int, default=999); a.add_argument("--reps", type=int, default=50)
    a.add_argument("--seed", type=int, default=20261108); a.add_argument("--out", default="swarmclock_report")
    args = ap.parse_args(argv)
    t0 = time.time()
    X = prepare(read_any(args.input), args.actor, args.time, args.text, args.doc, args.time_unit)
    out, tables = run_audit(X, args.k, args.threshold, args.min_blocks, (args.short_window_h, args.very_long_window_h), args.B, args.reps, args.seed)
    p = write_report(out, tables, args.out, args)
    print(out["verdict"]); print(f"report: {p}  ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
