"""Publication figures for the paper (tueplots sizing, STIX serif, Okabe-Ito palette, vector PDF + 600 dpi PNG).

Every value is read from outputs/tables. Identity is carried by marker and line style as well as color, so the
figures remain legible in grayscale.
"""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from tueplots import figsizes, fontsizes
from .io import TABLES, FIGS

# Okabe-Ito (colorblind safe)
OI = {"black": "#000000", "orange": "#E69F00", "sky": "#56B4E9", "green": "#009E73", "yellow": "#F0E442",
      "blue": "#0072B2", "vermillion": "#D55E00", "purple": "#CC79A7", "grey": "#7F7F7F"}
INK, MUTED, GRID, SHADE = "#1a1a1a", "#5c5c5c", "#e6e6e6", "#f2f2f2"
TEXTW = 6.75  # inches, two-column ML venue full width (ICML/NeurIPS); fits a Word page with 1-inch margins

FAM = {5455: "data-link lists", 6843: "default-page text", 2842: "round-status reports",
       1979: "endpoint pages", 2378: "archival link lists", 5207: "exact-copy burst"}
LAG_BINS = ["<10m", "10-30m", "30m-1h", "1-3h", "3-6h", "6-12h", "12-24h", "1-3d", ">3d"]
LAG_TICKS = ["<10 m", "10-30 m", "0.5-1 h", "1-3 h", "3-6 h", "6-12 h", "12-24 h", "1-3 d", ">3 d"]


def style():
    plt.rcParams.update(fontsizes.icml2024())
    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["STIXGeneral", "STIX Two Text", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8.5, "legend.fontsize": 6.6,
        "xtick.labelsize": 7, "ytick.labelsize": 7,
        "axes.linewidth": 0.6, "axes.edgecolor": INK, "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": INK, "ytick.color": INK, "xtick.direction": "in", "ytick.direction": "in",
        "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.minor.width": 0.4, "ytick.minor.width": 0.4,
        "xtick.major.size": 3, "ytick.major.size": 3, "xtick.minor.size": 1.6, "ytick.minor.size": 1.6,
        "xtick.top": False, "ytick.right": False,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.titlelocation": "left", "axes.titleweight": "bold", "axes.titlepad": 4,
        "lines.linewidth": 1.3, "lines.markersize": 3.6, "patch.linewidth": 0.6,
        "legend.frameon": False, "legend.handlelength": 1.8, "legend.borderaxespad": 0.3,
        "legend.labelspacing": 0.3, "legend.handletextpad": 0.5,
        "figure.dpi": 150, "savefig.dpi": 600, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "figure.constrained_layout.use": True,
    })


def wilson(k, n, z=1.96):
    if n == 0:
        return np.nan, np.nan
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def _save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(FIGS / f"{name}.{ext}")
    plt.close(fig)
    print(f"[fig] outputs/figs/{name}.png/.pdf")


def _panel_label(ax, text):
    ax.set_title(text)


# --------------------------------------------------------------------------------------------- Figure 1
def fig_three_times():
    """Figure 1: (a) no clock, (b) sensitivity, (c) co-time, (d) calendar."""
    R = pd.read_csv(TABLES / "lag_curves_real.csv"); R = R[R.set == "primary"]
    PC = pd.read_csv(TABLES / "positive_control_bodies_lag_curve.csv")
    Sy = pd.read_csv(TABLES / "lag_curves_synth.csv")
    E = pd.read_csv(TABLES / "power_end_to_end.csv")
    Fx = pd.read_csv(TABLES / "power_sampling_matched_reps200.csv")
    CT = pd.read_csv(TABLES / "cotime_L1_both_halves.csv")
    fr = TABLES / "frontier"

    fig, axs = plt.subplots(2, 2, figsize=(TEXTW, 4.55))
    (a, b), (c, d) = axs

    # (a) No clock ----------------------------------------------------------------------------
    x = np.arange(len(LAG_BINS))
    a.axvspan(4.5, len(x) - 0.5, color=SHADE, lw=0, zorder=0)
    a.text(len(x) - 0.6, 0.035, r"lag $\geq$ 6 h", ha="right", va="bottom", fontsize=6.6, color=MUTED)
    a.plot(x, PC.mean_distance.values, color=OI["green"], marker="^", ms=3.8, lw=1.5, label="whole page bodies (grow)", zorder=4)
    clk = Sy[Sy.set == "clock p=0.02"].iloc[0][LAG_BINS].astype(float).values
    a.plot(x, clk, color=OI["blue"], ls=(0, (4, 2)), lw=1.4, label="planted clock (simulated)", zorder=3)
    for fam, mk in [(5455, "o"), (6843, "s")]:
        r = R[R.family == fam].iloc[0][LAG_BINS].astype(float).values
        a.plot(x, r, color=INK, marker=mk, mfc="white", mew=0.8, ms=3.4, lw=0.9,
               label=f"added text: {FAM[fam]}", zorder=5)
    a.set_xticks(x); a.set_xticklabels(LAG_TICKS, rotation=40, ha="right", rotation_mode="anchor")
    a.set_xlim(-0.4, len(x) - 0.6); a.set_yticks([0, .25, .5, .75, 1])
    a.set_ylabel(r"mean distance (1 $-$ Jaccard)"); a.set_xlabel("time lag between two texts")
    a.text(0.15, 0.985, "added text, two longest-lived families", fontsize=6.6, color=INK, va="bottom")
    a.text(2.35, 0.58, "whole page bodies\n(grow by accumulation)", fontsize=6.6, color=OI["green"], va="top")
    a.text(5.1, 0.27, "planted clock\n(simulated)", fontsize=6.6, color=OI["blue"], va="top")
    a.legend(handles=[Line2D([], [], color=INK, marker="o", mfc="white", mew=0.8, ms=3.4, lw=0.9, label=FAM[5455]),
                      Line2D([], [], color=INK, marker="s", mfc="white", mew=0.8, ms=3.4, lw=0.9, label=FAM[6843])],
             loc="lower left", bbox_to_anchor=(0.0, 0.0), fontsize=6.3)
    a.set_ylim(0, 1.08)
    _panel_label(a, "(a) No clock in what agents pass on")

    # (b) Sensitivity -------------------------------------------------------------------------
    ck = E[E.kind == "clock"].sort_values("edit_rate_per_copy"); st = E[E.kind == "star"].sort_values("edit_rate_per_copy")
    b.axhline(0.8, color=MUTED, lw=0.6, ls=":", zorder=1); b.text(0.0021, 0.815, "80%", fontsize=6.3, color=MUTED, va="bottom")
    b.axhline(0.05, color=MUTED, lw=0.6, ls=":", zorder=1); b.text(0.0021, 0.065, "5%", fontsize=6.3, color=MUTED, va="bottom")
    b.plot(Fx.edit_rate_per_copy, Fx.power_long_lag_all_pairs, color=OI["sky"], ls=(0, (4, 2)), marker="o", mfc="white", mew=0.8,
           label="families held fixed")
    lo, hi = zip(*[wilson(round(v * n), n) for v, n in zip(ck.end_to_end_reject, ck.reps)])
    b.fill_between(ck.edit_rate_per_copy, lo, hi, color=OI["vermillion"], alpha=.16, lw=0)
    b.plot(ck.edit_rate_per_copy, ck.end_to_end_reject, color=OI["vermillion"], marker="s", label="end to end (families rebuilt)")
    b.plot(st.edit_rate_per_copy, st.end_to_end_reject, color=INK, marker="x", ls="none", ms=4, mew=0.9, label="no-clock control (size)")
    b.set_xscale("log"); b.set_ylim(-0.02, 1.02); b.set_xlim(0.002, 0.25)
    b.set_xlabel("edit rate per copy of the planted clock"); b.set_ylabel(r"detection rate (lag $\geq$ 6 h)")
    b.legend(loc="center left", bbox_to_anchor=(0.0, 0.33), fontsize=6.3)
    _panel_label(b, "(b) ...although a clock would usually show")

    # (c) Co-time -----------------------------------------------------------------------------
    sub = CT[(CT.set == "r2_no_burst_no_template") & (CT.thr == 0.5)].sort_values("half")
    groups = ["most similar\npartner", "closest-length\npartner", "random\npartner"]
    cols = ["content", "length", "random"]; colors = [OI["blue"], OI["orange"], OI["grey"]]
    width = 0.34
    for h_i, (_, row) in enumerate(sub.iterrows()):
        n = int(row.covered)
        for g_i, (col, colr) in enumerate(zip(cols, colors)):
            v = row[col]; xpos = g_i + (h_i - 0.5) * width
            hatch = None if h_i == 1 else "////"
            c.bar(xpos, v, width * 0.92, color=colr if h_i == 1 else "white", edgecolor=colr, hatch=hatch, lw=0.8, zorder=2)
            top = v
            if col != "random":
                l_, u_ = wilson(round(v * n), n)
                c.errorbar(xpos, v, yerr=[[v - l_], [u_ - v]], color=INK, lw=0.7, capsize=1.6, capthick=0.7, zorder=3)
                top = u_
            c.text(xpos, top + 0.02, f"{v:.2f}", ha="center", va="bottom", fontsize=5.9, color=INK)
    c.set_xticks(range(3)); c.set_xticklabels(groups, fontsize=6.6)
    c.set_ylim(0, 1.12); c.set_yticks([0, .25, .5, .75, 1]); c.set_ylabel("share written within 1 h")
    n0, n1 = int(sub.iloc[0].covered), int(sub.iloc[1].covered)
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor="white", edgecolor=MUTED, hatch="////", lw=0.8),
               plt.Rectangle((0, 0), 1, 1, facecolor=MUTED, edgecolor=MUTED, lw=0.8)]
    c.legend(handles, [f"pilot half (n = {n0})", f"held-out half (n = {n1})"], loc="upper right", fontsize=6.3)
    _panel_label(c, "(c) Co-time: near-duplicates are contemporaneous")

    # (d) Calendar ----------------------------------------------------------------------------
    rows = [("pre-registered", "t_tpq_confirm_all_exclude.csv", None),
            ("burst, template removed", "t_tpq_confirm_r2_exclude.csv", None),
            ("date-like features dropped", "t_adv_confirm_date.csv", None),
            ("same-family anchors excluded", "t_adv_confirm_fam.csv", None),
            ("similar-label anchors excluded", "t_adv_confirm_prefix.csv", None),
            ("all three exclusions", "t_adv_confirm_all3.csv", None)]
    vals = []
    for name, f, _ in rows:
        r = pd.read_csv(fr / f).iloc[-1]
        vals.append((name, float(r.success), float(r.null_success_mean), float(r.null_success_p975), float(r.coverage), int(r.targets)))
    y = np.arange(len(vals))[::-1]
    for yi, (name, sv, nm, n975, cov, ntar) in zip(y, vals):
        d.plot([nm, n975], [yi, yi], color=MUTED, lw=2.6, solid_capstyle="butt", alpha=0.55, zorder=2)
        d.plot(nm, yi, marker="o", mfc="white", mec=MUTED, mew=0.9, ms=4.2, zorder=3)
        d.plot([n975, sv], [yi, yi], color=OI["blue"], lw=0.7, ls=":", zorder=1)
        k = round(sv * cov * ntar); n = round(cov * ntar); l_, u_ = wilson(k, n)
        d.errorbar(sv, yi, xerr=[[sv - l_], [u_ - sv]], color=OI["blue"], lw=0.8, capsize=1.6, capthick=0.7, zorder=4)
        d.plot(sv, yi, marker="D", color=OI["blue"], ms=4.2, zorder=5)
        d.text(1.0, yi, f"{cov:.0%}", ha="right", va="center", fontsize=6.0, color=MUTED)
    d.text(1.0, len(vals) - 0.45, "covered", ha="right", va="bottom", fontsize=6.0, color=MUTED, style="italic")
    d.set_yticks(y); d.set_yticklabels([v[0] for v in vals], fontsize=6.6)
    d.set_xlim(0, 1.0); d.set_ylim(-0.6, len(vals) + 0.75)
    d.set_xlabel(r"share dated to the day before (window $[-1\,\mathrm{h}, +24\,\mathrm{h}]$)")
    d.legend(handles=[Line2D([], [], marker="D", color=OI["blue"], ls="none", ms=4.2, label="real anchor times"),
                      Line2D([], [], marker="o", mfc="white", mec=MUTED, ls="-", color=MUTED, lw=2.6, alpha=.7, ms=4.2,
                             label="permuted times: mean to 97.5th pct.")],
             loc="upper left", bbox_to_anchor=(0.0, 1.0), ncol=2, fontsize=6.2, columnspacing=1.0)
    d.spines["left"].set_visible(False); d.tick_params(axis="y", length=0)
    _panel_label(d, "(d) Calendar: shared material dates held-out text")
    _save(fig, "fig1_three_times")


# --------------------------------------------------------------------------------------------- Figure 2
def fig_copy_modes():
    """Figure 2: how agents copy. (a) wiki same vs different label; (b) Mantiq channels; (c) model exposure tail."""
    L = pd.read_csv(TABLES / "same_vs_diff_label_lt1h.csv"); L = L[L.family != 5207].reset_index(drop=True)
    Cc = pd.read_csv(TABLES / "mantiq_copy_channels.csv").iloc[0]
    X = json.load(open(TABLES / "ext_a_prime_model_exposure.json"))
    fig = plt.figure(figsize=(TEXTW, 2.25))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.3, 1.2, 0.9])
    a, b, c = fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), fig.add_subplot(gs[2])

    order = L.sort_values("d_diff").reset_index(drop=True)
    y = np.arange(len(order))
    for i, r in order.iterrows():
        a.plot([r.d_same, r.d_diff], [i, i], color=GRID, lw=2.2, zorder=1, solid_capstyle="round")
    a.scatter(order.d_same, y, marker="o", s=20, color=OI["blue"], zorder=3, label="same label", lw=0)
    a.scatter(order.d_diff, y, marker="s", s=20, facecolor="white", edgecolor=OI["vermillion"], lw=1.0, zorder=3, label="different labels")
    a.set_yticks(y); a.set_yticklabels([f"{FAM.get(int(f), f)}  ({int(s)} / {int(d)})" for f, s, d in
                                        zip(order.family, order.pairs_lt1h_same, order.pairs_lt1h_diff)], fontsize=6.4)
    a.set_xlim(0, 1); a.set_xlabel("mean distance, pairs < 1 h apart")
    a.spines["left"].set_visible(False); a.tick_params(axis="y", length=0)
    a.legend(loc="lower left", bbox_to_anchor=(-0.02, 1.0), ncol=2, fontsize=6.3, columnspacing=1.0)
    a.set_title("(a) collusion.wiki (N same / different pairs)", pad=16)

    vals = [Cc.ws_made_by_git / Cc.ws_versions, Cc.share_git_from_other_agent, Cc.share_same_agent_given_prev_agent_made]
    labs = ["workspace versions written\nby git as exact copies",
            "git copies first written\nby another agent",
            "edits on an agent-written\nbase by the same agent"]
    ns = [int(Cc.ws_versions), int(Cc.git_versions_with_agent_author), int(Cc.agent_edits_base_agent)]
    colors = [OI["vermillion"], OI["vermillion"], OI["blue"]]
    yb = np.arange(3)[::-1]
    for yi, v, n, col in zip(yb, vals, ns, colors):
        b.barh(yi, v, height=0.56, color=col, alpha=0.9, lw=0)
        l_, u_ = wilson(round(v * n), n)
        b.text(v + 0.02, yi, f"{v:.0%}", va="center", fontsize=6.6)
        b.text(0.025, yi, f"N = {n:,}", va="center", ha="left", fontsize=5.8, color="white")
    b.set_yticks(yb); b.set_yticklabels(labs, fontsize=6.4); b.set_xlim(0, 1.12); b.set_xticks([0, .5, 1])
    b.set_xticklabels(["0", "50%", "100%"]); b.spines["left"].set_visible(False); b.tick_params(axis="y", length=0)
    b.set_title("(b) Mantiq copy channels", pad=16)

    seen, unseen = X["share_exposed_pairs_c_ge_0.5"], X["share_unexposed_pairs_c_ge_0.5"]
    ne, nu = X["exposed_pairs"], X["pairs"] - X["exposed_pairs"]
    for xi, v, n, col, lab in [(0, seen, ne, OI["blue"], "seen by\nthe model"), (1, unseen, nu, OI["grey"], "not seen")]:
        c.bar(xi, v * 100, 0.6, color=col, lw=0)
        l_, u_ = wilson(round(v * n), n)
        c.errorbar(xi, v * 100, yerr=[[(v - l_) * 100], [(u_ - v) * 100]], color=INK, lw=0.7, capsize=1.6)
        c.text(xi, v * 100 + 0.35, f"{v:.1%}", ha="center", fontsize=6.6)
    c.set_xticks([0, 1]); c.set_xticklabels(["seen", "not seen"], fontsize=6.8)
    c.set_xlabel("source in the writer's model context", fontsize=6.8)
    c.set_ylabel(r"share with containment $\geq 0.5$ (%)"); c.set_ylim(0, 5)
    c.set_title("(c) Copying from context", pad=16)
    _save(fig, "fig2_copy_modes")


# --------------------------------------------------------------------------------------------- Appendix
def fig_c1_lag_curves():
    R = pd.read_csv(TABLES / "lag_curves_real.csv"); R = R[(R.set == "primary") & (R.family != 5207)]
    Sy = pd.read_csv(TABLES / "lag_curves_synth.csv")
    fig, ax = plt.subplots(figsize=(TEXTW * 0.62, 2.35))
    x = np.arange(len(LAG_BINS))
    ax.axvspan(4.5, len(x) - 0.5, color=SHADE, lw=0, zorder=0)
    ax.text(len(x) - 0.6, 0.03, r"lag $\geq$ 6 h", ha="right", va="bottom", fontsize=6.6, color=MUTED)
    mks = ["o", "s", "^", "D", "v"]
    for k, (_, r) in enumerate(R.iterrows()):
        ax.plot(x, r[LAG_BINS].astype(float).values, color=INK, marker=mks[k], mfc="white", mew=0.8, ms=3.3, lw=0.8,
                label=FAM.get(int(r.family), r.family))
    sty = {"clock p=0.02": (OI["blue"], "-"), "clock p=0.05": (OI["blue"], (0, (4, 2))),
           "star p=0.02": (OI["orange"], "-"), "star p=0.05": (OI["orange"], (0, (4, 2)))}
    for _, r in Sy.iterrows():
        col, ls = sty[r.set]
        ax.plot(x, r[LAG_BINS].astype(float).values, color=col, ls=ls, lw=1.6,
                label=f"planted {r.set.split()[0]}, rate {r.set.split('=')[1]}")
    ax.set_xticks(x); ax.set_xticklabels(LAG_TICKS, rotation=40, ha="right", rotation_mode="anchor")
    ax.set_ylim(0, 1.02); ax.set_ylabel(r"mean distance (1 $-$ Jaccard)"); ax.set_xlabel("time lag")
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=6.3)
    _save(fig, "figC1_lag_curves")


def fig_c2_lifespans():
    S = pd.read_csv(TABLES / "lifespans_ge5_by_config.csv")
    fig, ax = plt.subplots(figsize=(TEXTW * 0.5, 2.1))
    sty = [(OI["grey"], ":"), (OI["orange"], (0, (4, 2))), (OI["blue"], "-"), (OI["green"], "-.")]
    for (cfg, sub), (col, ls) in zip(S.groupby("config", sort=False), sty):
        v = np.sort(np.clip(sub.span_h.values * 60, 0.5, None))
        ax.step(v, np.arange(1, len(v) + 1) / len(v), where="post", color=col, ls=ls, lw=1.3 if "primary" not in cfg else 1.8,
                label=f"{cfg.replace(' (primary)', ', primary')} ({len(v)})")
    for xv in (10, 60, 1440, 10080):
        ax.axvline(xv, color=GRID, lw=0.7, zorder=0)
    ax.set_xscale("log"); ax.set_xticks([1, 10, 60, 1440, 10080, 43200]); ax.minorticks_off()
    ax.set_xticklabels(["1 min", "10 min", "1 h", "1 d", "1 wk", "30 d"])
    ax.set_xlabel("lineage lifespan, first to last introduction"); ax.set_ylabel(r"ECDF (families $\geq$ 5 pages)")
    ax.set_ylim(0, 1.02); ax.legend(loc="upper left", fontsize=6.2)
    _save(fig, "figC2_lifespans")


ALL = [fig_three_times, fig_copy_modes, fig_c1_lag_curves, fig_c2_lifespans]


def main():
    style()
    for f in ALL:
        f()


if __name__ == "__main__":
    main()
