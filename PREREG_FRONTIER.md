# Pre-registration: frontier lines D (direction of copying), A (anchor-propagated dating), S (time-information spectrum)

Written 2026-11-09 00:21 America/Santiago by an analysis agent, BEFORE any quantity below that uses time order or lag was computed.
Known at writing: paper/report.md, DECISIONS D1-D17, all outputs/tables (incl. L1 co-time both halves).
Computed before writing (time-blind design counts only, scripts/design_counts*.py): in D_primary (7,964 masked introductions),
cross-page cross-label pairs with Jaccard (k = 3) in [0.3, 0.999): 677 (all) / 563 (burst and template removed, "r2"),
in 142 / 131 connected components; with the component split below, r2 has 283 pairs / 69 components (split 0) and 280 / 62 (split 1).
No timestamp, lag or order statistic for these pairs was looked at. Seed numpy default_rng(20261108).

## D. Can content tell which of two near-duplicates was written first (direction), beyond length?
- Pairs: D_primary introductions, set r2 (exclude the 314-page exact-copy burst family and default-page-template texts);
  different page AND different label; s = Jaccard(k = 3 token shingles) in [0.3, 0.999); |lag| >= 1 s (ties dropped).
- Split (fixed now): connected components of the graph of these pairs (built on the whole corpus, time-blind);
  split key = crc32(lexicographically smallest page_id in the component) % 2. Split 0 = pilot, split 1 = confirmation.
- Truth: which member has the earlier request-log time.
- Time-blind scores (corpus statistics use all 7,964 introductions, never times). For pair (A, B), df'(x) = number of introductions
  containing shingle x, excluding introductions written under label(A) or label(B) or on page(A) or page(B).
  S0 length (baseline): the longer text (characters) is later.
  S1 rare-variant polarity: F(S) = mean log(1 + df') over shingle set S, F(empty) := F(A n B); pol = F(A \ B) - F(B \ A);
     the member whose private shingles are more frequent elsewhere is earlier (ancestral), the one with rarer private shingles later (derived).
  S2 novelty: share of a member's shingles with df' = 0; the more novel member is later.
  S3 centrality: number of other introductions (other label, other page than either member) with Jaccard >= 0.3 to the member;
     the more central member is earlier.
  Ties count 0.5.
- Metric: accuracy = share of pairs whose order the rule gets right, component-balanced (each pair weighted 1/pairs in its component);
  95% CI by bootstrap over components (2,000 resamples). Also reported: unweighted accuracy, lag strata (< 1 h, >= 1 h), s >= 0.5 subset.
- Length-balanced subset: |log(len A / len B)| <= 0.1, where S0 carries little information.
- Pilot (split 0) selects the content score C = argmax over {S1, S2, S3} of component-balanced accuracy on length-balanced pairs
  (ties -> S1); the pilot also reports everything for S0..S3. Nothing else is tuned.
- Confirmatory predictions (split 1, score C fixed by the pilot):
  D1 (primary): accuracy of C on length-balanced pairs > 0.5, 95% CI lower bound > 0.5.
  D2 (secondary): accuracy of C on all pairs > 0.5 (CI lower bound > 0.5), and C - S0 accuracy difference reported with paired component-bootstrap CI.
- Reading: success = content carries direction beyond growth: the earlier near-duplicate is ancestral in the population (consistent with
  agents copying peers, not only siblings of a shared source). Failure = near-duplicates are exchangeable in time given content
  (consistent with common-cause bursts or symmetric copying); reported as a pre-registered negative. Not a test of who copied whom
  (no ground-truth parent), only of which was first.
- Exploratory (not confirmatory): same analysis on set "all" and on s >= 0.5.

## A. Anchor-propagated dating with conformal error bars (co-time used as a dating method)
- Units: D_primary introductions; sets "all" and r2. Page halves crc32(page_id) % 2 as in PREREG_POSITIVE_LINE (half 0 calibrates,
  half 1 evaluates); anchors and targets come from the same half.
- Anchor density f in {0.016 (Swarm-Traces-like share of records with an internal anchor), 0.05, 0.20}; 100 random anchor draws per f.
  A target (non-anchor) is dated if its most similar anchor on a different page under a different label has s >= 0.5;
  estimate = that anchor's time (ties: closest length, then random).
- Calibration (half 0): q_f = split-conformal 90% quantile of |error| pooled over draws (rank ceil(0.9 (n + 1))).
- Evaluation (half 1): share of targets dated (coverage), empirical share with |error| <= q_f (interval validity), median |error|.
  Baseline: dating every target by the median anchor time (its 90% |error| quantile from half 0 and coverage in half 1).
- Predictions (half 1, set r2 and all): A1 validity: empirical coverage of the +-q_f interval >= 0.85 at each f;
  A2 informativeness: q_f <= 2 h while the baseline 90% half-width is >= 24 h. Coverage (share dated) is reported, not predicted.
- Reading: a dating rule with measured error bars for the minority of artifacts that have a near-duplicate anchor; it does not date
  artifacts without one.

## S. Time-information spectrum (EXPLORATORY, no confirmatory claim)
- For log-spaced lag octaves, AUC of similarity for distinguishing pairs at lag in [d, 2d) from [2d, 4d), within the six eligible families
  (cross-label pairs, representatives), and for the page-body positive control; converted to bits as a descriptive spectrum.
  Labelled exploratory; permutation-null bands only.

## Decision rule
A line enters the paper as positive only if its confirmatory predictions hold on the confirmation split; the pilot split alone is never
reported as confirmatory. Any change after this timestamp is listed as a deviation in REPORT.md.
