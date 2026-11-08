#!/usr/bin/env python
"""Run one pipeline stage. Each stage reads/writes artifacts on disk (data/interim, outputs/tables).

Usage: python scripts/run_stage.py <stage> [<stage> ...]
Stages: fetch swarmtraces_anchors wiki_intros lifespans tests_real calibration lag_windows crosslabel
        power ablations controls
"""
import sys, time, collections, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd
from swarmclock import io as sio
from swarmclock.io import INTERIM, RAW, save, rng as new_rng
from swarmclock import anchors as anc, wiki, families as fm, stats as stt
from swarmclock.synth import Synth

STAGES = {}


def stage(fn):
    STAGES[fn.__name__] = fn
    return fn


def load_R():
    F = pd.read_parquet(INTERIM / "wiki_intros.parquet")
    R = F[~F.page_id.isin(wiki.HUBS)].reset_index(drop=True)[["rev_id", "page_id", "label", "t", "m"]]
    R["t"] = pd.to_datetime(R.t, utc=True)
    return R


def load_D(name):
    D = pd.read_parquet(INTERIM / f"{name}.parquet")
    D["t"] = pd.to_datetime(D.t, utc=True)
    return D


def elig_ids(D, min_blocks=15):
    _, g = fm.family_table(D.drop(columns="family"), D.family.values)
    return g[g.blocks >= min_blocks].sort_values("blocks", ascending=False).index


def r3(x):
    return round(float(x), 3) if x == x else x


# ---------------------------------------------------------------- Part 1
@stage
def fetch():
    print(sio.fetch().to_string(index=False))


@stage
def swarmtraces_anchors():
    st = list(sio.read_jsonl_gz(RAW / "st_redacted.jsonl.gz"))
    out = {"rows": len(st)}
    keys = collections.Counter(k for r in st for k in r.keys())
    out["fields"] = dict(keys)
    out["kind_counts"] = dict(collections.Counter(r.get("kind") for r in st))
    # control 3.2: parent_id and time_utc over the FULL file
    nn = lambda k: sum(r.get(k) not in (None, "") for r in st)
    out["parent_id_nonnull_full"] = nn("parent_id")
    out["time_utc_nonnull_full"] = nn("time_utc")
    out["tags_nonnull_full"] = nn("tags")
    A = anc.anchor_table(st)
    out["records_with_anchor"] = int(A.rec.nunique())
    out["share_with_anchor"] = A.rec.nunique() / len(st)
    out["anchor_rows_by_type"] = A.kind.value_counts().to_dict()
    inh = A.groupby(["kind", "inherited"]).rec.nunique().unstack(fill_value=0)
    save(inh.reset_index(), "st_anchor_type_by_inherited")
    day = A[~A.inherited].groupby("day").rec.nunique()
    save(day.rename("independent_records").reset_index(), "st_independent_anchors_by_day")
    fam = anc.anchor_families(st, A)
    A["family"] = A.rec.map(fam)
    indep = A[~A.inherited].drop_duplicates("rec")
    per_fam = indep.groupby("family").rec.nunique().sort_values(ascending=False)
    out["independent_anchored_records"] = int(len(indep))
    out["share_independent_of_anchored"] = len(indep) / A.rec.nunique()
    jul = sum(v for d, v in day.items() if str(d) in ("2026-07-11", "2026-07-12"))
    out["independent_on_jul11_12"] = int(jul)
    out["families_ge15"] = int((per_fam >= 15).sum())
    out["top_families"] = per_fam.head(10).to_dict()
    out["gate1_passed"] = bool(len(indep) >= 500 and (per_fam >= 15).sum() >= 5)
    # control 3.2: anchor rate by record kind
    kinds = pd.Series([r.get("kind") for r in st], name="kind")
    rec_kind = kinds.iloc[A.rec.unique()].value_counts()
    rec_kind_ind = kinds.iloc[indep.rec.values].value_counts()
    tab = pd.DataFrame({"records": kinds.value_counts(), "with_anchor": rec_kind, "with_independent_anchor": rec_kind_ind}).fillna(0).astype(int)
    tab["anchor_rate"] = (tab.with_anchor / tab.records).round(4)
    tab["independent_rate"] = (tab.with_independent_anchor / tab.records).round(4)
    save(tab.reset_index(names="kind"), "st_anchor_rate_by_kind")
    (sio.TABLES / "st_summary.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))
    print(inh.to_string()); print(tab.to_string())


# ---------------------------------------------------------------- Part 2a
@stage
def wiki_intros():
    cw = list(sio.read_jsonl_gz(RAW / "cw_revisions.jsonl.gz"))
    I = wiki.intro_frame(cw)
    print(len(cw), "revisions;", I.how.value_counts().to_dict(), "| unparseable times:", int(I.t.isna().sum()))
    nc = I[I.how == "hunks"]
    print("median intro/body ratio (hunks):", round((nc.intro.str.len() / nc.body_len.clip(lower=1)).median(), 4))
    F = wiki.window_filter(I)
    print("after filters:", len(F))
    msk = wiki.Masker(F.label)
    F["m"] = F.intro.map(msk)
    F["ntok"] = F.m.str.split().str.len()
    F = F[F.ntok >= 8].reset_index(drop=True)
    print("introductions with >= 8 tokens:", len(F))
    # 2a families (k=5, t=0.5, hubs NOT excluded) for regression
    fam = fm.assign_families(fm.minhashes(F.m, 5), 0.5)
    F["family"] = fam
    F["block"] = F.family.astype(str) + "|" + F.page_id
    F["len"] = F.m.str.len()
    reps = F.sort_values(["block", "len", "rev_id"], ascending=[True, False, True]).drop_duplicates("block")
    g = reps.groupby("family").agg(blocks=("block", "nunique"), pages=("page_id", "nunique"), labels=("label", "nunique"),
                                   t_min=("t", "min"), t_max=("t", "max"))
    g["span_h"] = (g.t_max - g.t_min).dt.total_seconds() / 3600
    el = g[(g.blocks >= 15) & (g.pages >= 2)].sort_values("blocks", ascending=False)
    print("2a: families total:", len(g), "| eligible:", len(el), "| reps in eligible:", int(el.blocks.sum()))
    print(el.to_string())
    save(el.reset_index(), "wiki_2a_k5t05_eligible")
    F[["rev_id", "page_id", "label", "t", "family", "block", "m"]].to_parquet(INTERIM / "wiki_intros.parquet")
    # all introductions incl. short ones, for the recreation positive control
    I["m"] = I.intro.map(msk)
    I[["rev_id", "page_id", "label", "t", "time_grade", "how", "m", "relation_type", "related_event_id"]].to_parquet(INTERIM / "wiki_all_intros.parquet")


# ---------------------------------------------------------------- Part 2b (Finding B)
CONFIGS = [("k5 t0.5", 5, .5), ("k5 t0.3", 5, .3), ("k3 t0.3 (primary)", 3, .3), ("k3 t0.2", 3, .2)]


@stage
def lifespans():
    R = load_R()
    print("real introductions (hubs excluded):", len(R))
    cache, summary, spans = {}, [], []
    for name, k, thr in CONFIGS:
        if k not in cache:
            cache[k] = fm.minhashes(R.m, k)
        fam = fm.assign_families(cache[k], thr)
        D, g = fm.family_table(R, fam)
        f5 = g[g.blocks >= 5]
        spans += [{"config": name, "family": f, "span_h": s, "blocks": b} for f, s, b in zip(f5.index, f5.span_h, f5.blocks)]
        summary.append({"config": name, "families_ge5": len(f5), "eligible_ge15": int((g.blocks >= 15).sum()),
                        "multi_day_ge3d_ge15": int(((g.blocks >= 15) & (g.days >= 3)).sum()),
                        "span_ge24h_ge15": int(((g.blocks >= 15) & (g.span_h >= 24)).sum()),
                        "median_span_min": round(60 * np.median(f5.span_h), 1), "p75_h": round(np.quantile(f5.span_h, .75), 2),
                        "p90_h": round(np.quantile(f5.span_h, .9), 2), "share_gt24h": round((f5.span_h > 24).mean(), 3),
                        "largest_family_share": round(g.blocks.max() / g.blocks.sum(), 3)})
        if "primary" in name:
            D.to_parquet(INTERIM / "D_primary.parquet")
            el = g[g.blocks >= 15].sort_values("blocks", ascending=False)
            save(el.reset_index(), "wiki_primary_eligible")
            print(el.to_string())
        if name == "k5 t0.3":
            D.to_parquet(INTERIM / "D_k5t03.parquet")
    S = pd.DataFrame(summary); print(S.to_string(index=False))
    save(S, "finding_B_lifespans"); save(pd.DataFrame(spans), "lifespans_ge5_by_config")
    # template ablation families (2c)
    R_ab = R.assign(m=R.m.str.replace(wiki.TEMPLATE, " ", regex=True).str.strip())
    R_ab = R_ab[R_ab.m.str.split().str.len() >= 8].reset_index(drop=True)
    fam_ab = fm.assign_families(fm.minhashes(R_ab.m, 3), 0.3)
    D_ab, G_ab = fm.family_table(R_ab, fam_ab)
    D_ab.to_parquet(INTERIM / "D_template_removed.parquet")
    el_ab = G_ab[G_ab.blocks >= 15].sort_values("blocks", ascending=False)
    save(el_ab.reset_index(), "wiki_template_removed_eligible")
    print(el_ab[["blocks", "labels", "span_h", "days"]].to_string())


# ---------------------------------------------------------------- Part 2b/2c real tests
@stage
def tests_real():
    rng = new_rng()
    rows, perfam = [], []
    for data, Dn in [("real", "D_primary"), ("real, template removed", "D_template_removed")]:
        D = load_D(Dn); el = elig_ids(D)
        modes = ["length", "day", "day_length"] if data == "real" else ["length", "day"]
        for mode in modes:
            X = fm.reps_with_strata(D, el, mode)
            arrs = fm.family_arrays(X)
            T, p, v = stt.perm_test(arrs, rng, B=999)
            rows.append({"data": data, "strata": mode, "families": len(arrs), "T": r3(T), "p": round(p, 4)})
            if mode == "length":
                for a in arrs:
                    sub = X[X.family == a["f"]]
                    dt_ = np.abs(a["t"][a["iu"][0]] - a["t"][a["iu"][1]])
                    rho = np.corrcoef(a["rd"], stt.rankdata(dt_))[0, 1] if np.ptp(dt_) > 0 and np.ptp(a["rd"]) > 0 else np.nan
                    perfam.append({"data": data, "family": a["f"], "reps": len(sub), "days": sub.t.dt.date.nunique(),
                                   "labels": sub.label.nunique(), "strata": len(np.unique(a["strata"])), "rho": r3(rho)})
    print(pd.DataFrame(perfam).to_string(index=False)); print(pd.DataFrame(rows).to_string(index=False))
    save(pd.DataFrame(rows), "temporal_tests_real"); save(pd.DataFrame(perfam), "per_family_rho")


# ---------------------------------------------------------------- calibration (2b contaminated, 2c corrected)
def _calib_condition(S, R, mh_real, kind, p, rng, B=199):
    P = S.plant(kind, p)
    A = pd.concat([R.assign(lin=-1), P], ignore_index=True)
    fam = fm.assign_families(mh_real + fm.minhashes(P.m, 3), 0.3)
    D, g = fm.family_table(A[["rev_id", "page_id", "label", "t", "m"]], fam)
    D["lin"] = A.lin.values
    res = []
    for li in range(P.lin.max() + 1):
        mem = D[D.lin == li]; f = mem.family.mode().iloc[0]
        complete = (mem.family == f).mean()
        recovered = complete >= .8 and g.loc[f, "blocks"] >= 15 and g.loc[f, "days"] >= 3
        out = {"kind": kind, "p": p, "lin": li, "completeness": complete, "recovered": recovered,
               "contaminated_real_members": int(((D.family == f) & (D.lin == -1)).sum())}
        if recovered:
            only = D[(D.lin == li) & (D.family == f)]
            for mode in ["length", "day"]:
                out[f"p_{mode}"] = stt.perm_test(fm.family_arrays(fm.reps_with_strata(only, [f], mode)), rng, B=B)[1]
            out["p_contaminated"] = stt.perm_test(fm.family_arrays(fm.reps_with_strata(D[D.family == f], [f], "length")), rng, B=B)[1]
        res.append(out)
    return pd.DataFrame(res)


@stage
def calibration():
    import os
    batches = int(os.environ.get("SWC_CAL_BATCHES", 1))
    suffix = "" if batches == 1 else f"_x{batches}"
    rng = new_rng(); R = load_R(); S = Synth(R, rng)
    mh_real = fm.minhashes(R.m, 3)
    CAL = pd.concat([_calib_condition(S, R, mh_real, kind, p, rng).assign(batch=b) for b in range(batches)
                     for kind in ["clock", "star"] for p in [0.02, 0.05, 0.10, 0.20]], ignore_index=True)
    for c in ["p_length", "p_day", "p_contaminated"]:
        if c not in CAL:
            CAL[c] = np.nan
    summ = CAL.groupby(["kind", "p"]).agg(recovery=("recovered", "mean"), completeness=("completeness", "median"),
                                          contaminated=("contaminated_real_members", "median"),
                                          sig_length=("p_length", stt.sig_rate), sig_day=("p_day", stt.sig_rate),
                                          sig_contaminated=("p_contaminated", stt.sig_rate),
                                          n_tested=("p_length", lambda s: int(s.notna().sum())))
    print(summ.to_string())
    save(CAL, "calibration_per_lineage" + suffix); save(summ.reset_index(), "calibration_summary" + suffix)


# ---------------------------------------------------------------- Part 2d
def real_pairs(D, fams, dist=None):
    X = fm.reps_with_strata(D, fams, "length")
    return [(f, fm.fam_pairs(X[X.family == f], dist=dist)) for f in X.family.unique()]


def _window_rows(Ps, rng, cross, tag, B=999):
    out = []
    for wname, lo, hi in stt.WIN:
        T, p, v = stt.window_test(Ps, lo, hi, rng, B=B, cross=cross)
        out.append({**tag, "pairs": "cross-label" if cross else "all", "window": wname,
                    "families_with_pairs": int(np.sum(~np.isnan(v))), "T": r3(T), "p": round(p, 4) if p == p else p,
                    "per_family": [r3(x) for x in v]})
    return out


@stage
def lag_windows():
    rng = new_rng()
    REAL = {n: real_pairs(load_D(d), elig_ids(load_D(d))) for n, d in [("primary", "D_primary"), ("template_removed", "D_template_removed")]}
    rows = [{"set": n, "family": f, **dict(zip(stt.BIN_LABELS, np.round(stt.lag_curve(P), 3)))} for n, FP in REAL.items() for f, P in FP]
    CURVES = pd.DataFrame(rows); print(CURVES.to_string(index=False)); save(CURVES, "lag_curves_real")
    WT = []
    for n, FP in REAL.items():
        WT += _window_rows([P for _, P in FP], rng, False, {"data": n})
    print(pd.DataFrame(WT).to_string(index=False)); save(pd.DataFrame(WT), "window_tests_real")
    # synthetic references (planted members only, 7 days)
    S = Synth(load_R(), rng)
    srows, swt = [], []
    for kind in ["clock", "star"]:
        for p in [0.02, 0.05]:
            Pl = S.plant(kind, p, n_lin=20, days=7)
            Ps = [fm.fam_pairs(sub.assign(stratum=0)) for _, sub in Pl.groupby("lin")]
            name = f"{kind} p={p}"
            srows.append({"set": name, **dict(zip(stt.BIN_LABELS, np.round(np.nanmean([stt.lag_curve(P) for P in Ps], axis=0), 3)))})
            for wname, lo, hi in stt.WIN:
                ps = [stt.window_test([P], lo, hi, rng, B=199)[1] for P in Ps]
                swt.append({"synthetic": name, "window": wname, "reject_rate": round(float(np.nanmean(np.array(ps) < .05)), 2), "n": len(ps)})
    print(pd.DataFrame(srows).to_string(index=False)); print(pd.DataFrame(swt).to_string(index=False))
    save(pd.DataFrame(srows), "lag_curves_synth"); save(pd.DataFrame(swt), "window_tests_synth")
    # same vs different label at lag < 1 h
    lab = []
    for f, P in REAL["primary"]:
        lag = np.abs(P["t"][P["i"]] - P["t"][P["j"]]); m = lag < 1
        s, o = P["d"][m & P["same_label"]], P["d"][m & ~P["same_label"]]
        lab.append({"family": f, "pairs_lt1h_same": len(s), "d_same": r3(s.mean()) if len(s) else np.nan,
                    "pairs_lt1h_diff": len(o), "d_diff": r3(o.mean()) if len(o) else np.nan,
                    "share_diff_pairs_d0": r3((o == 0).mean()) if len(o) else np.nan})
    print(pd.DataFrame(lab).to_string(index=False)); save(pd.DataFrame(lab), "same_vs_diff_label_lt1h")


@stage
def crosslabel():
    rng = new_rng()
    XL = []
    for n, d in [("primary", "D_primary"), ("template_removed", "D_template_removed")]:
        D = load_D(d)
        XL += _window_rows([P for _, P in real_pairs(D, elig_ids(D))], rng, True, {"data": n})
    print(pd.DataFrame(XL).to_string(index=False)); save(pd.DataFrame(XL), "window_tests_crosslabel")


# ---------------------------------------------------------------- Part 3a
def _real_fams_multiday():
    D = load_D("D_primary"); X = fm.reps_with_strata(D, elig_ids(D), "length")
    RF = {f: X[X.family == f].sort_values("t").reset_index(drop=True) for f in X.family.unique()}
    return {f: s for f, s in RF.items() if s.t.dt.date.nunique() >= 2}


@stage
def power():
    rng = new_rng(); R = load_R(); S = Synth(R, rng)
    RF = _real_fams_multiday()
    print({f: (len(s), s.t.dt.date.nunique()) for f, s in RF.items()})
    import os
    REPS, B = int(os.environ.get("SWC_POWER_REPS", 20)), 99
    suffix = "" if REPS == 20 else f"_reps{REPS}"
    rows = []
    for p in [0.0025, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20]:
        t0 = time.time(); ha, hx, slopes, dlong = [], [], [], []
        for _ in range(REPS):
            Ps = [fm.fam_pairs(S.synth_like(sub, p)) for sub in RF.values()]
            ha.append(stt.window_test(Ps, 6, 1e9, rng, B=B)[1] < .05)
            hx.append(stt.window_test(Ps, 6, 1e9, rng, B=B, cross=True)[1] < .05)
            for P in Ps:
                lag = np.abs(P["t"][P["i"]] - P["t"][P["j"]]) / 24; m = lag >= 0.25
                if m.sum() > 10:
                    slopes.append(np.polyfit(lag[m], P["d"][m], 1)[0]); dlong.append(P["d"][m].mean())
        rows.append({"edit_rate_per_copy": p, "distance_slope_per_day_median": round(float(np.median(slopes)), 4),
                     "mean_distance_long_lag": round(float(np.mean(dlong)), 3),
                     "power_long_lag_all_pairs": float(np.mean(ha)), "power_long_lag_cross_label": float(np.mean(hx)),
                     "reps": REPS, "B": B})
        print(rows[-1], f"{time.time()-t0:.0f}s", flush=True)
    POWER = pd.DataFrame(rows); save(POWER, "power_sampling_matched" + suffix)
    obs = []
    for f, sub in RF.items():
        P = fm.fam_pairs(sub); lag = np.abs(P["t"][P["i"]] - P["t"][P["j"]]) / 24; m = lag >= 0.25
        if m.sum() > 10:
            obs.append({"family": f, "reps": len(sub), "pairs_ge6h": int(m.sum()),
                        "slope_per_day": round(float(np.polyfit(lag[m], P["d"][m], 1)[0]), 4),
                        "mean_distance_long_lag": round(float(P["d"][m].mean()), 3)})
    print(pd.DataFrame(obs).to_string(index=False)); save(pd.DataFrame(obs), "observed_long_lag_slopes")


def _ncd_dist(texts, i, j):
    import zlib
    c = [len(zlib.compress(t.encode(), 9)) for t in texts]
    out = np.empty(len(i))
    for n, (a, b) in enumerate(zip(i, j)):
        cab = len(zlib.compress((texts[a] + " " + texts[b]).encode(), 9))
        out[n] = (cab - min(c[a], c[b])) / max(c[a], c[b])
    return out


@stage
def ablations():
    rng = new_rng(); ABL = []
    D = load_D("D_primary"); el = elig_ids(D)
    Ps = [P for _, P in real_pairs(D, el, dist=_ncd_dist)]
    for cross in [False, True]:
        ABL += _window_rows(Ps, rng, cross, {"distance": "NCD (zlib)", "families": "k3 t0.3"})
    D5 = load_D("D_k5t03"); el5 = elig_ids(D5)
    print("k5 t0.3 eligible:", list(el5))
    Ps5 = [P for _, P in real_pairs(D5, el5)]
    for cross in [False, True]:
        ABL += _window_rows(Ps5, rng, cross, {"distance": "Jaccard k3", "families": "k5 t0.3"})
    ABL = pd.DataFrame(ABL); print(ABL.to_string(index=False)); save(ABL, "ablations")


# ---------------------------------------------------------------- controls
@stage
def controls():
    """Positive control: each first_recreation_of revision vs the last revision of that page saved before
    the deletion it recreates (masked full bodies, k=3 Jaccard distance). Baseline: same recreated body vs
    random revisions of other pages. Also: Swarm Traces parent_id structure."""
    rng = new_rng()
    cw = list(sio.read_jsonl_gz(RAW / "cw_revisions.jsonl.gz"))
    ev = {e["event_id"]: e for e in sio.read_jsonl_gz(RAW / "cw_events.jsonl.gz")}
    F = wiki.window_filter(wiki.intro_frame(cw))
    msk = wiki.Masker(F.label)
    revs = pd.DataFrame([{"rev_id": r["rev_id"], "page_key": r["page_key"], "seq": r["seq"], "label": r.get("label") or "",
                          "t": r.get("time"), "rel": r.get("relation_type"), "rel_ev": r.get("related_event_id"),
                          "body": wiki.get_body(r)} for r in cw])
    revs["t"] = pd.to_datetime(revs.t, utc=True, errors="coerce")
    revs["mb"] = revs.body.map(msk)
    sh = {i: fm.shingle_set(m, 3) for i, m in zip(revs.index, revs.mb)}
    jd = lambda a, b: 1 - len(sh[a] & sh[b]) / max(1, len(sh[a] | sh[b]))
    rows = []
    for i, r in revs[revs.rel == "first_recreation_of"].iterrows():
        rel = r.rel_ev if isinstance(r.rel_ev, (list, tuple, np.ndarray)) else [r.rel_ev]
        de = next((ev[e] for e in rel if e in ev), {})
        dtime = pd.to_datetime(de.get("time"), utc=True, errors="coerce")
        prior = revs[(revs.page_key == r.page_key) & (revs.seq < r.seq)]
        if pd.notna(dtime):
            prior = prior[prior.t <= dtime]
        if not len(prior):
            rows.append({"rev_id": r.rev_id, "matched": False}); continue
        j = prior.sort_values("seq").index[-1]
        others = revs.index[(revs.page_key != r.page_key)].values
        base = [jd(i, k) for k in rng.choice(others, 50, replace=False)]
        rows.append({"rev_id": r.rev_id, "matched": True, "prior_rev": revs.rev_id[j],
                     "gap_h": (r.t - revs.t[j]).total_seconds() / 3600, "delete_found": bool(de),
                     "delete_page_matches": de.get("page_key") == r.page_key, "same_label": r.label == revs.label[j],
                     "dist_to_prior": jd(i, j), "dist_random_median": float(np.median(base)),
                     "body_tokens": len(r.mb.split())})
    C = pd.DataFrame(rows); save(C, "control_recreation_pairs")
    M = C[C.matched]
    summ = {"recreations": len(C), "matched": len(M), "dist_median": float(M.dist_to_prior.median()),
            "dist_mean": float(M.dist_to_prior.mean()), "share_dist0": float((M.dist_to_prior == 0).mean()),
            "share_dist_lt_0.1": float((M.dist_to_prior < .1).mean()),
            "random_baseline_median": float(M.dist_random_median.median()),
            "gap_h_median": float(M.gap_h.median()), "same_label_share": float(M.same_label.mean())}
    print(json.dumps(summ, indent=1)); (sio.TABLES / "control_recreation_summary.json").write_text(json.dumps(summ, indent=1))
    # Swarm Traces parent_id structure
    st = pd.DataFrame([{k: r.get(k) for k in ["id", "kind", "parent_id"]} for r in sio.read_jsonl_gz(RAW / "st_redacted.jsonl.gz")])
    st["has_parent"] = st.parent_id.notna() & (st.parent_id != "")
    kind_of = dict(zip(st.id, st.kind)); p = st[st.has_parent]
    tab = pd.crosstab(p.kind, p.parent_id.map(kind_of).fillna("missing"))
    tab["records_of_kind"] = st.kind.value_counts().reindex(tab.index)
    print(tab.to_string()); save(tab.reset_index(), "st_parent_id_structure")
    print("distinct parents:", p.parent_id.nunique(), "| children per parent:", p.parent_id.value_counts().describe().round(2).to_dict())


# ---------------------------------------------------------------- Mantiq (PREREG_MANTIQ.md)
@stage
def mantiq_build():
    from swarmclock import mantiq as mq
    units, cov = mq.build_units()
    # POST HOC sensitivity (DECISIONS D5): one introduction per identical (run, sender, masked text): earliest send
    units["U-M-dedup"] = units["U-M"].sort_values("ts_ns").drop_duplicates(["run", "label", "m"]).reset_index(drop=True)
    cov["U-M-dedup"] = cov["U-M"]
    # POST HOC sensitivity (DECISIONS D6): drop tool-generated boilerplate (pytest cache files) from U-F
    boiler = units["U-F"].path.str.contains(r"pytest-cache-files-|\.pytest_cache|CACHEDIR\.TAG", regex=True)
    units["U-F-noboiler"] = units["U-F"][~boiler].reset_index(drop=True)
    cov["U-F-noboiler"] = cov["U-F"]
    print("U-F tool-boilerplate intros dropped:", int(boiler.sum()))
    for name, U in units.items():
        U.to_parquet(INTERIM / f"mantiq_{name}.parquet")
        print(name, "coverage", round(cov[name], 3), "| intros >= 8 tokens:", len(U), "| runs:", U.run.nunique(),
              "| actors/run median:", U.groupby("run").label.nunique().median())
    (sio.TABLES / "mantiq_text_coverage.json").write_text(json.dumps(cov, indent=1))


def _mq_families(U, k, thr):
    """Families built separately within each run; ids prefixed by run."""
    parts = []
    for run, sub in U.groupby("run", sort=True):
        sub = sub.reset_index(drop=True)
        fam = fm.assign_families(fm.minhashes(sub.m, k), thr)
        parts.append(sub.assign(family=[f"{run}:{x}" for x in fam]))
    D = pd.concat(parts, ignore_index=True)
    return D


def _mq_famtable(D):
    g = D.groupby("family").agg(run=("run", "first"), blocks=("page_id", "nunique"), labels=("label", "nunique"),
                                ts0=("ts_ns", "min"), ts1=("ts_ns", "max"), D_s=("D_s", "first"), n=("m", "size"))
    g["span_s"] = (g.ts1 - g.ts0) / 1e9
    g["span_frac"] = g.span_s / g.D_s
    return g


@stage
def mantiq_families():
    rows, spans, chain = [], [], []
    for name in ["U-M", "U-M-dedup", "U-F", "U-F-noboiler"]:
        U = pd.read_parquet(INTERIM / f"mantiq_{name}.parquet")
        for cname, k, thr in [("k3 t0.3 (primary)", 3, .3), ("k5 t0.5 (fallback)", 5, .5)]:
            D = _mq_families(U, k, thr); g = _mq_famtable(D)
            tot = g.groupby("run").blocks.sum(); mx = g.groupby("run").blocks.max()
            share = (mx / tot)
            for run in share.index:
                chain.append({"unit": name, "config": cname, "run": run, "largest_share": round(float(share[run]), 3),
                              "chained": bool(share[run] > .2)})
            f5 = g[g.blocks >= 5]
            spans += [{"unit": name, "config": cname, "family": f, "span_s": s, "span_frac": sf, "blocks": b}
                      for f, s, sf, b in zip(f5.index, f5.span_s, f5.span_frac, f5.blocks)]
            el = g[g.blocks >= 15]
            rows.append({"unit": name, "config": cname, "intros": len(U), "families_ge5": len(f5), "eligible_ge15": len(el),
                         "eligible_runs": el.run.nunique(), "median_span_s_ge5": round(float(f5.span_s.median()), 1) if len(f5) else np.nan,
                         "median_span_frac_ge5": round(float(f5.span_frac.median()), 3) if len(f5) else np.nan,
                         "p90_span_frac_ge5": round(float(f5.span_frac.quantile(.9)), 3) if len(f5) else np.nan,
                         "runs_chained": int((share > .2).sum()), "max_largest_share": round(float(share.max()), 3)})
            tag = "primary" if k == 3 else "k5t05"
            D.to_parquet(INTERIM / f"mantiq_D_{name}_{tag}.parquet")
            save(el.reset_index(), f"mantiq_eligible_{name}_{tag}")
    S = pd.DataFrame(rows); print(S.to_string(index=False)); save(S, "mantiq_lifespans")
    save(pd.DataFrame(spans), "mantiq_lifespans_ge5"); C = pd.DataFrame(chain); save(C, "mantiq_chaining")
    print(C.groupby(["unit", "config"]).agg(chained=("chained", "sum"), max_share=("largest_share", "max")).to_string())


def _mq_pairs(D, el, dist=None):
    X = fm.reps_with_strata(D, el, "length")
    return [(f, fm.fam_pairs(X[X.family == f], dist=dist)) for f in X.family.unique()], X


def _mq_window_rows(Ps, rng, cross, tag, B=999):
    out = []
    for wname, lo, hi in stt.MQ_WIN:
        T, p, v = stt.window_test(Ps, lo, hi, rng, B=B, cross=cross)
        out.append({**tag, "pairs": "cross-agent" if cross else "all", "window": wname,
                    "families_with_pairs": int(np.sum(~np.isnan(v))), "T": r3(T), "p": round(p, 4) if p == p else p,
                    "per_family_median": r3(np.nanmedian(v)) if np.any(~np.isnan(v)) else np.nan})
    return out


@stage
def mantiq_tests():
    from swarmclock import mantiq as mq
    rng = new_rng(); WT, CUR, LAB, ELIG = [], [], [], []
    for name in ["U-M", "U-M-dedup", "U-F", "U-F-noboiler"]:
        for tag in ["primary", "k5t05"]:
            D = pd.read_parquet(INTERIM / f"mantiq_D_{name}_{tag}.parquet"); D["t"] = pd.to_datetime(D.t, utc=True)
            g = _mq_famtable(D)
            subsets = {"all runs": g[g.blocks >= 15].index}
            if tag == "primary":
                subsets["no-fault practice runs"] = g[(g.blocks >= 15) & g.run.isin(mq.NO_FAULT_PRACTICE)].index
                if name.startswith("U-F"):
                    Dn = D[~D.path.str.contains(mq.STATUS_FILES)]
                    gn = _mq_famtable(Dn)
                    subsets["status files excluded"] = ("refit", Dn, gn[gn.blocks >= 15].index)
            for sname, el in subsets.items():
                DD = D
                if isinstance(el, tuple):
                    _, DD, el = el
                ELIG.append({"unit": name, "config": tag, "subset": sname, "eligible": len(el)})
                if len(el) < 5:
                    print(f"{name} {tag} {sname}: {len(el)} eligible families < 5 -> not tested (decision point)")
                    WT.append({"unit": name, "config": tag, "subset": sname, "pairs": "-", "window": "-", "T": np.nan, "p": np.nan,
                               "families_with_pairs": len(el), "note": "fewer than 5 eligible families: not tested"})
                    continue
                FP, X = _mq_pairs(DD, el)
                Ps = [P for _, P in FP]
                for cross in [False, True]:
                    WT += _mq_window_rows(Ps, rng, cross, {"unit": name, "config": tag, "subset": sname, "eligible": len(el)})
                print(pd.DataFrame(WT[-6:]).to_string(index=False), flush=True)
                if sname == "all runs":
                    for f, P in FP:
                        CUR.append({"unit": name, "config": tag, "family": f, "n": len(P["t"]),
                                    **dict(zip(stt.MQ_BIN_LABELS, np.round(stt.lag_curve(P, stt.MQ_BINS), 3)))})
                        Pc = dict(P); Pc["d"] = P["d"].copy()
                        m = ~P["same_label"]
                        cc = stt.lag_curve({**P, "i": P["i"][m], "j": P["j"][m], "d": P["d"][m]}, stt.MQ_BINS)
                        CUR.append({"unit": name, "config": tag + " cross-agent", "family": f, "n": len(P["t"]),
                                    **dict(zip(stt.MQ_BIN_LABELS, np.round(cc, 3)))})
                        lag = np.abs(P["t"][P["i"]] - P["t"][P["j"]]); sm = lag < 0.05
                        s_, o_ = P["d"][sm & P["same_label"]], P["d"][sm & ~P["same_label"]]
                        LAB.append({"unit": name, "config": tag, "family": f, "pairs_same": len(s_), "d_same": r3(s_.mean()) if len(s_) else np.nan,
                                    "pairs_diff": len(o_), "d_diff": r3(o_.mean()) if len(o_) else np.nan,
                                    "share_diff_d0": r3((o_ == 0).mean()) if len(o_) else np.nan})
    save(pd.DataFrame(WT), "mantiq_window_tests"); save(pd.DataFrame(CUR), "mantiq_lag_curves")
    save(pd.DataFrame(LAB), "mantiq_same_vs_diff_agent"); save(pd.DataFrame(ELIG), "mantiq_eligibility")
    print(pd.DataFrame(WT).to_string(index=False))


@stage
def mantiq_power():
    import os
    rng = new_rng(); rows = []
    REPS = int(os.environ.get("SWC_MQ_REPS", 100))
    for name in ["U-M", "U-M-dedup", "U-F", "U-F-noboiler"]:
        D = pd.read_parquet(INTERIM / f"mantiq_D_{name}_primary.parquet"); D["t"] = pd.to_datetime(D.t, utc=True)
        g = _mq_famtable(D); el = g[g.blocks >= 15].index
        if len(el) < 5:
            continue
        X = fm.reps_with_strata(D, el, "length")
        RF = [X[X.family == f].sort_values("t").reset_index(drop=True) for f in X.family.unique()]
        S = Synth(D.assign(t=D.t), rng)
        for kind in ["clock", "star"]:
            for p in [0.0025, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20]:
                t0 = time.time(); ha, hx, dl = [], [], []
                for _ in range(REPS):
                    Ps = [fm.fam_pairs(S.synth_like(sub, p) if kind == "clock" else S.star_like(sub, p)) for sub in RF]
                    ha.append(stt.window_test(Ps, 1 / 3, 1e9, rng, B=99)[1] < .05)
                    hx.append(stt.window_test(Ps, 1 / 3, 1e9, rng, B=99, cross=True)[1] < .05)
                    dl.append(np.nanmean([P["d"][np.abs(P["t"][P["i"]] - P["t"][P["j"]]) >= 1 / 3].mean() for P in Ps]))
                rows.append({"unit": name, "kind": kind, "edit_rate_per_copy": p, "reject_long_all": float(np.mean(ha)),
                             "reject_long_cross_agent": float(np.mean(hx)), "mean_distance_long_lag": round(float(np.nanmean(dl)), 3),
                             "reps": REPS, "B": 99, "families": len(RF)})
                print(rows[-1], f"{time.time()-t0:.0f}s", flush=True)
    save(pd.DataFrame(rows), "mantiq_power")


def main(argv):
    if not argv:
        print(__doc__); return
    for s in argv:
        t0 = time.time(); print(f"===== stage {s}", flush=True)
        STAGES[s]()
        print(f"===== {s} done in {time.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
