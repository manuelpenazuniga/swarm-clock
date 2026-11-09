"""Publication figures (300 dpi PNG + PDF). Grayscale-legible: identity carried by line style and marker, not color alone."""
import ast
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from .io import TABLES, FIGS

C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"
LS = ["-", "--", "-.", ":"]
MK = ["o", "s", "^", "D", "v", "P"]
FAM_NAMES = {5207: "exact-copy burst (5 min)", 5455: "data-link lists (30 d, 7 dates)", 6843: "default-page text (21 d, 9 dates)",
             2842: "round-status reports (3.7 d, 3 dates)", 1979: "endpoint pages (3 h)", 2378: "archival link lists (10 h)"}
plt.rcParams.update({"font.size": 8, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "font.family": "DejaVu Sans", "legend.frameon": False, "lines.linewidth": 1.6})


def _save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(FIGS / f"{name}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[fig] outputs/figs/{name}.png")


def wilson(k, n, z=1.96):
    if n == 0:
        return np.nan, np.nan
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def fig_lifespans():
    S = pd.read_csv(TABLES / "lifespans_ge5_by_config.csv")
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    for k, (cfg, sub) in enumerate(S.groupby("config", sort=False)):
        x = np.sort(np.clip(sub.span_h.values, 1 / 60, None))
        ax.step(x, np.arange(1, len(x) + 1) / len(x), where="post", color=C[k], ls=LS[k], label=f"{cfg} (n={len(x)})")
    for xv, lab, yy in [(1 / 6, "10 min", 0.93), (1, "1 h", 0.84), (24, "1 day", 0.93)]:
        ax.axvline(xv, ls=":", c=GRID, lw=1, zorder=0); ax.text(xv * 1.08, yy, lab, fontsize=7, color=INK2)
    ax.set_xscale("log"); ax.set_xlabel("lineage lifespan, first to last introduction (h, log)")
    ax.set_ylabel("ECDF, families with >= 5 pages"); ax.set_ylim(0, 1.02)
    ax.legend(fontsize=6.5, loc="lower right", bbox_to_anchor=(1.0, 0.03))
    _save(fig, "fig1_lifespans")


def fig_lag_curves():
    R = pd.read_csv(TABLES / "lag_curves_real.csv"); R = R[R.set == "primary"]
    Sy = pd.read_csv(TABLES / "lag_curves_synth.csv")
    labs = ["<10m", "10-30m", "30m-1h", "1-3h", "3-6h", "6-12h", "12-24h", "1-3d", ">3d"]
    x = np.arange(len(labs))
    fig, ax = plt.subplots(figsize=(6.6, 2.7))
    for k, (_, r) in enumerate(R[R.family != 5207].iterrows()):
        ax.plot(x, r[labs].astype(float).values, color=INK2, lw=1, marker=MK[k], ms=4, mfc="white",
                label=f"real: {FAM_NAMES.get(int(r.family), r.family)}")
    styles = {"clock p=0.02": (C[0], "-"), "clock p=0.05": (C[0], "--"), "star p=0.02": (C[1], "-"), "star p=0.05": (C[1], "--")}
    for _, r in Sy.iterrows():
        col, ls = styles[r.set]
        ax.plot(x, r[labs].astype(float).values, color=col, ls=ls, lw=2.2, label=f"synthetic {r.set}")
    ax.axvline(4.5, color=GRID, lw=1, zorder=0); ax.text(4.55, 0.03, "6 h", color=INK2, fontsize=7)
    ax.set_xlabel("time lag between two artifacts of the same family")
    ax.set_xticks(x); ax.set_xticklabels(labs); ax.set_xlabel("time lag between two artifacts of the same family")
    ax.set_ylabel("mean text distance (1 - Jaccard, k=3)"); ax.set_ylim(0, 1.02)
    ax.legend(fontsize=6.3, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.22))
    _save(fig, "fig2_lag_curves")


def fig_forest():
    W = pd.read_csv(TABLES / "window_tests_real.csv"); X = pd.read_csv(TABLES / "window_tests_crosslabel.csv")
    W = W[W.data == "primary"].assign(pairs="all pairs"); X = X[X.data == "primary"].assign(pairs="cross-label pairs")
    syn = pd.read_csv(TABLES / "power_sampling_matched_reps200.csv")
    pw = {"all pairs": syn.set_index("edit_rate_per_copy").loc[0.01, "power_long_lag_all_pairs"],
          "cross-label pairs": syn.set_index("edit_rate_per_copy").loc[0.01, "power_long_lag_cross_label"]}
    rows = []
    for D in (W, X):
        for _, r in D.iterrows():
            rows.append((r.window, r.pairs, r["T"], r.p, ast.literal_eval(r.per_family.replace("nan", "None"))))
    fig, ax = plt.subplots(figsize=(5.0, 2.6))
    ylabels = []
    for i, (w, pr, T, p, pf) in enumerate(rows):
        y = len(rows) - 1 - i
        vals = [v for v in pf if v is not None]
        ax.scatter(vals, [y] * len(vals), s=12, facecolor="white", edgecolor=INK2, lw=0.8, zorder=2)
        col = C[0] if pr == "all pairs" else C[1]
        ax.scatter([T], [y], s=46, marker="D" if pr == "all pairs" else "s", color=col, zorder=3)
        txt = f"T = {T:+.3f}, p = {p:.3f}"
        if w.startswith("long"):
            txt += f"\n(power {pw[pr] + 1e-9:.2f} at edit rate 0.01)"
        ax.text(1.02, y, txt, va="center", fontsize=6.3, color=INK, transform=ax.get_yaxis_transform())
        ylabels.append(f"{pr}, {w}")
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels(ylabels[::-1], fontsize=7)
    ax.set_xlim(-1, 1); ax.set_xlabel("Spearman rho(distance, lag)\nopen circles = families; filled = mean T")
    ax.axhline(2.5, color=GRID, lw=1)
    _save(fig, "fig3_window_forest")


def fig_power():
    P = pd.read_csv(TABLES / "power_sampling_matched_reps200.csv")
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    for k, (col, lab) in enumerate([("power_long_lag_all_pairs", "wiki, all pairs"), ("power_long_lag_cross_label", "wiki, cross-label pairs")]):
        n = P.reps.values; kk = np.round(P[col].values * n)
        lo, hi = zip(*[wilson(a, b) for a, b in zip(kk, n)])
        ax.fill_between(P.edit_rate_per_copy, lo, hi, color=C[k], alpha=.15, lw=0)
        ax.plot(P.edit_rate_per_copy, P[col], color=C[k], ls=LS[k], marker=MK[k], ms=4, label=lab)
    try:
        M = pd.read_csv(TABLES / "mantiq_power.csv")
        m = M[(M.unit == "U-F") & (M.kind == "clock")]
        if len(m):
            col = "reject_long_cross_agent_a025" if "reject_long_cross_agent_a025" in m else "reject_long_cross_agent"
            ax.plot(m.edit_rate_per_copy, m[col], color=C[2], ls="-.", marker="^", ms=4,
                    label="Mantiq files, cross-agent (pre-reg. α = 0.025)")
    except FileNotFoundError:
        pass
    ax.axhline(.8, ls=":", c=INK2, lw=1); ax.text(0.0026, 0.81, "80%", fontsize=7, color=INK2)
    ax.set_xscale("log"); ax.set_ylim(0, 1.02)
    ax.set_xlabel("per-copy edit rate of a planted clock (log)"); ax.set_ylabel("power, long-lag test")
    ax.legend(fontsize=6.3, loc="lower right")
    _save(fig, "fig4_power")


def fig_schematic():
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.2))
    rng = np.random.default_rng(1)
    # (a) cross-agent exact-copy burst
    ax = axs[0]
    t = np.sort(rng.uniform(0, 5, 14))
    ax.plot([0, 5], [0.0, 0.0], color=GRID, lw=1, zorder=1)
    ax.scatter(t, np.zeros(14), marker="s", s=26, color=C[1], zorder=3, clip_on=False)
    ax.set_title("(a) Schematic: cross-agent exact-copy burst", fontsize=8, loc="left")
    ax.text(0.02, 0.12, "many agents within minutes; every copy at distance 0", fontsize=6.5, color=INK2, transform=ax.transAxes)
    ax.set_xlabel("time (minutes); each square = one agent's copy"); ax.set_ylabel("distance to first copy (illustrative)"); ax.set_ylim(-0.05, 1)
    # (b) self-revision saturating
    ax = axs[1]
    lag = np.linspace(0, 12, 100)
    ax.plot(lag, 0.95 * (1 - np.exp(-lag / 1.2)), color=C[0], lw=2, label="same-label revision (saturating shape)")
    ax.plot(lag, 0.08 * lag, color=INK2, ls="--", lw=1.4, label="accumulating clock (not observed)")
    ax.set_ylim(0, 1); ax.set_xlabel("lag (hours)"); ax.set_ylabel("distance (illustrative)")
    ax.set_title("(b) Schematic: same-label revision saturates", fontsize=8, loc="left")
    ax.legend(fontsize=6.3, loc="lower right")
    fig.subplots_adjust(wspace=0.32)
    _save(fig, "fig5_regimes")


def fig_wiki_vs_mantiq():
    L = pd.read_csv(TABLES / "same_vs_diff_label_lt1h.csv")
    Cc = pd.read_csv(TABLES / "mantiq_copy_channels.csv").iloc[0]
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.4))
    ax = axs[0]
    L = L[L.family != 5207].reset_index(drop=True)
    y = np.arange(len(L))
    ax.scatter(L.d_same, y, marker="o", s=30, color=C[0], label="same label")
    ax.scatter(L.d_diff, y, marker="s", s=30, facecolor="white", edgecolor=C[1], lw=1.4, label="different labels")
    for i, r in L.iterrows():
        ax.plot([r.d_same, r.d_diff], [i, i], color=GRID, lw=1, zorder=0)
    ax.set_yticks(y); ax.set_yticklabels([f"{FAM_NAMES.get(int(f), f)}\nN = {a} / {b} pairs" for f, a, b in zip(L.family, L.pairs_lt1h_same, L.pairs_lt1h_diff)], fontsize=6)
    ax.set_xlim(0, 1); ax.set_xlabel("mean distance, pairs < 1 h apart")
    ax.set_title("(a) collusion.wiki: short-lag similarity is self-revision", fontsize=8, loc="left")
    ax.legend(fontsize=6.3, loc="lower left", bbox_to_anchor=(0.0, 1.06), ncol=2, borderaxespad=0)
    ax.set_title("(a) collusion.wiki: same vs different label, pairs < 1 h", fontsize=8, loc="left", pad=16)
    ax = axs[1]
    vals = [Cc.ws_made_by_git / Cc.ws_versions, Cc.share_git_from_other_agent, Cc.share_same_agent_given_prev_agent_made]
    labs = [f"workspace file versions delivered\nby git, exact bytes (N = {int(Cc.ws_versions):,})",
            f"git-delivered versions first written\nby another agent (N = {int(Cc.git_versions_with_agent_author):,})",
            f"agent edits on an agent-written base\nby the same agent (N = {int(Cc.agent_edits_base_agent):,})"]
    ax.barh(range(3), vals, color=[C[1], C[1], C[0]], height=.55)
    for i, v in enumerate(vals):
        ax.text(v + .01, i, f"{v:.0%}", va="center", fontsize=7, color=INK)
    ax.set_yticks(range(3)); ax.set_yticklabels(labs, fontsize=6.5); ax.set_xlim(0, 1.1); ax.invert_yaxis()
    ax.set_title("(b) Mantiq (true identity, descriptive)", fontsize=8, loc="left", pad=16)
    ax.set_xlabel("share")
    fig.tight_layout()
    _save(fig, "fig6_wiki_vs_mantiq")


def fig_summary():
    """Figure 0: the result at a glance (three panels)."""
    S = pd.read_csv(TABLES / "lifespans_ge5_by_config.csv")
    R = pd.read_csv(TABLES / "lag_curves_real.csv"); R = R[R.set == "primary"]
    Sy = pd.read_csv(TABLES / "lag_curves_synth.csv")
    P = pd.read_csv(TABLES / "power_sampling_matched_reps200.csv")
    labs = ["<10m", "10-30m", "30m-1h", "1-3h", "3-6h", "6-12h", "12-24h", "1-3d", ">3d"]
    fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.25))
    ax = axs[0]
    x = np.sort(np.clip(S[S.config.str.contains("primary")].span_h.values, 1 / 60, None))
    ax.step(x, np.arange(1, len(x) + 1) / len(x), where="post", color=C[0])
    med = np.median(x); ax.axvline(med, ls=":", c=INK2, lw=1); ax.text(med * 1.15, 0.08, f"median\n{med*60:.0f} min", fontsize=6.5, color=INK2)
    ax.set_xscale("log"); ax.set_xlabel("lineage lifespan (h, log)"); ax.set_ylabel("ECDF (60 families)")
    ax.set_title("(a) Lineages die within hours", fontsize=8, loc="left")
    ax = axs[1]
    xi = np.arange(len(labs))
    ax.axvspan(4.5, len(labs) - 0.5, color="#f0efec", zorder=0); ax.text(4.65, 0.70, "lag >= 6 h", fontsize=6.5, color=INK2)
    for k, fam in enumerate([5455, 6843]):
        r = R[R.family == fam].iloc[0]
        ax.plot(xi, r[labs].astype(float).values, color=INK2, marker=MK[k], ms=3.5, mfc="white", lw=1.2,
                label=FAM_NAMES[fam].split(" (")[0] + " (real)")
    r = Sy[Sy.set == "clock p=0.02"].iloc[0]
    ax.plot(xi, r[labs].astype(float).values, color=C[0], lw=2, ls="--", label="planted clock (synthetic)")
    ax.set_xticks(xi[::2]); ax.set_xticklabels(labs[::2], fontsize=6.5); ax.set_ylim(0, 1.02)
    ax.set_ylabel("mean distance"); ax.set_xlabel("time lag")
    ax.set_title("(b) Real text does not drift", fontsize=8, loc="left"); ax.legend(fontsize=5.8, loc="lower left")
    ax = axs[2]
    ax.axvspan(0.01, 0.05, color="#e4e2dc", zorder=0); ax.axvspan(0.05, 0.2, color="#f6f5f2", zorder=0)
    ax.text(0.0105, 0.42, "excluded\nend to end", fontsize=6.3, color=INK2); ax.text(0.055, 0.42, "power >= 80%,\nbut lineages\nfragment", fontsize=6.0, color=INK2)
    ax.plot(P.edit_rate_per_copy, P.power_long_lag_cross_label, color=C[1], marker="s", ms=3.5, label="cross-label")
    ax.plot(P.edit_rate_per_copy, P.power_long_lag_all_pairs, color=C[0], marker="o", ms=3.5, ls="--", label="all pairs")
    ax.axhline(.8, ls=":", c=INK2, lw=1); ax.set_xscale("log"); ax.set_ylim(0, 1.02)
    ax.set_xlabel("clock edit rate per copy (log)"); ax.set_ylabel("power, lag >= 6 h")
    ax.set_title("(c) ...although a clock would show", fontsize=8, loc="left"); ax.legend(fontsize=5.8, loc="lower right")
    fig.tight_layout()
    _save(fig, "fig0_summary")


ALL = [fig_summary, fig_lifespans, fig_lag_curves, fig_forest, fig_power, fig_schematic, fig_wiki_vs_mantiq]
