# Pre-registration: positive lines L1 (co-time) and L2 (within-document order)

Written 2026-11-08 23:41 America/Santiago by the analysis agent, BEFORE any quantity below was computed.
Known at writing: everything in paper/report.md and outputs/tables (window tests, recency kernel, exposure, positive control P).
Never computed before: similarity-vs-lag over cross-page pairs outside eligible families; any ordering/seriation metric.

**Pilot / confirmation split (fixed now).** Wiki: page halves by `zlib.crc32(page_id) % 2`; half 0 = pilot (computed tonight
by this agent), half 1 = confirmation (computed only after this file is committed, same code, no changes).
Mantiq: practice runs = pilot, hidden runs = confirmation. Seed `numpy.random.default_rng(20261108)`.

## L1. Co-time: does lexical similarity tell that two artifacts were written close in time?
- Unit: wiki introductions as in the paper (7,964; masked; >= 8 tokens; hubs excluded), within one half.
  Pairs: different page AND different label. Score s = Jaccard on k = 3 token shingles (frozen metric).
  Outcome y = |lag| < 1 h (secondary thresholds: 10 min, 6 h).
- L1a (primary): pair-level AUC of s for y; 95% CI by bootstrap over pages (pair weight = product of page multiplicities, 200 resamples).
- L1b (primary, each artifact counted once): for each introduction with an eligible partner at s >= 0.5, its content nearest
  neighbour (max s; ties: closest length, then random) is within 1 h? Compared on the same introductions with (i) the
  length nearest neighbour (closest |log length| among all eligible partners; ties random) and (ii) a random eligible partner
  (expected share). Report coverage, success shares, and the median |lag| to the content neighbour.
- Prediction (both halves): L1a AUC > 0.5 with CI excluding 0.5; L1b content-NN success >= length-NN success + 0.20.
- Pre-specified robustness: (r1) exclude members of the exact-copy burst family (primary family with 314 pages);
  (r2) also exclude introductions matching the default-page template; thresholds s >= 0.3 and s >= 0.9 for L1b.
- L1c (replication with true identity, Mantiq U-F-noboiler introductions): pairs within a run, different agent_id and
  different path; y = lag < D/10; pair-level AUC pooled over runs with run-bootstrap CI; L1b analogue (s >= 0.5).
- Reading: success = text supplies co-time (who wrote what at about the same time), not absolute time; failure = reported.

## L2. Within-document order: does a document's own state order its revisions beyond its length?
- Unit: full masked page bodies, pages with >= 15 revisions in the analysis window (positive-control P set, hubs included), one half.
- Per page: spectral seriation (Fiedler vector of the Laplacian of the similarity matrix 1 - d, d = 1 - Jaccard k = 3).
  Metric: |Spearman(seriation position, time)|. Baseline: |Spearman(body length, time)|.
- Primary: median over pages of |rho_ser| - |rho_len| > 0, one-sided paired Wilcoxon p < 0.05 (in both halves).
  Pre-specified subset: pages with |rho_len| < 0.5. Descriptive: per-page Pearson r of distance-to-first-revision with
  wall time (hours) vs with revision index (does text tick per edit or per hour?).
- Reading: success = document state carries order beyond growth; failure = the within-document clock is mostly growth.

## Decision rule
A line enters the paper as a positive finding only if its primary predictions hold in BOTH halves; otherwise it is
reported (if at all) as a pre-registered negative. The pilot half alone is never reported as confirmatory.
