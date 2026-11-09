# Pre-registration: extensions A, B, C (2026-11-08 ~21:56 America/Santiago)

Committed BEFORE any of these quantities was computed. Already known at this point: everything in paper/report.md (wiki window tests, LOFO, Mantiq unit results, copy-channel descriptives). For A, only the schema of the Mantiq `links` table was inspected (link types, methods and counts for two runs, the `details` keys of `read_version`), not any similarity or timing involving reads. All three are exploratory extensions decided after the main results; they are labeled as such in the paper.

## A. Observed exposure in Mantiq: does an agent's text track what it actually read, and does that similarity carry time?

Rationale: Mantiq's text links (`text_delivered`, `same_text`) are themselves content-derived, so they cannot validate content similarity. `read_version` links are observed by the file-system recorder: agent r read the bytes of a file version v. We use them as ground-truth exposure.

- **Exposures.** `read_version` links in all 19 runs whose reader r is an agent. The read version v is mapped to its content (`file_versions.sha256`) and to the content's first author w = the agent of the earliest `made_by == "agent"` version with that sha256 in the run. Keep exposures with w != r (cross-agent) and exported text. Exposure time t_e = recorder wall time of the read event; keep the first read per (run, reader, sha256).
- **Targets.** r's U-F introductions x (pre-registered U-F definition, PREREG_MANTIQ.md section 2, with the D6 pytest-boilerplate exclusion applied to both x and v) written after t_e.
- **Similarity.** Containment c(x, v) = |S(x) ∩ S(v)| / |S(x)| with S = set of 3-token shingles of masked text (Mantiq masker). Distance = 1 - c.
- **A1 (does similarity track observed exposure?).** For each target x, sources are agent-first-authored contents (w != r) that existed in the run before t_x. Exposed = r read it before t_x; unexposed = r never read it before t_x. Statistic: AUC of c (exposed vs unexposed) over all (x, source) pairs; 95% CI by bootstrap over runs (999). Also the share of targets whose maximum containment over exposed sources is >= 0.5 vs the same over unexposed sources. Prediction: AUC > 0.5.
- **A2 (does similarity to what was read change with time since reading?).** Exposed pairs only. Lag = (t_x - t_e) / D (fraction of run duration). Same windows as PREREG_MANTIQ: short < D/3, long >= D/3. Per run: Spearman between distance and lag within the window (runs with >= 10 pairs in the window); T = mean over runs; null permutes lags among pairs within reader strata in each run, B = 999, one-sided (positive). Readings: accumulating clock -> positive long-window T; recency/exact reuse -> positive or null short-window T and null long-window T. Lag curve by the PREREG_MANTIQ bins. Decision point: fewer than 5 runs with >= 10 pairs in the long window -> long-window test not run (reported as such).

## B. Wiki cross-label recency kernel (exploratory)

The 5 eligible primary families excluding the exact-copy burst (5207, which has no textual variance); representatives as in the paper. For cross-label pairs, fit d(lag) = d_inf - (d_inf - d0) exp(-lag / tau) (lag in hours, least squares on pairs). Report tau and half-life tau ln 2 with a 95% CI from a bootstrap over families (999 resamples of the 5 families). The same fit for same-label pairs for comparison. If the fit fails to converge or the CI upper bound exceeds the corpus span (946 h), tau is reported as not estimable.

## C. Same-label-only window tests on the wiki (exploratory)

Same statistic, strata (length), families and windows as Table 2, restricted to pairs written under the same label (complement of the cross-label test). Families with fewer than 10 same-label pairs in a window are skipped (existing rule). B = 999. Prediction: positive short-lag T; long-lag T near zero or not testable (few same-label long-lag pairs).
