# Pre-registration addendum T: terminus post quem (TPQ) dating from first appearance of shared features

Written 2026-11-09 America/Santiago (system clock at hashing is authoritative), BEFORE any TPQ, first-appearance or target-time
statistic was computed. Known at writing: PREREG_FRONTIER.md (D, A, S) and _H results; paper results. Computed before writing
(time-blind): page quarters q = crc32(page_id) % 4 have 2,167 / 2,009 / 1,870 / 1,918 introductions; with anchors = quarters {0, 2},
83% (q = 1) and 82% (q = 3) of targets share a 3-shingle that occurs in 1 to 50 anchors.

Idea (archaeology's terminus post quem): if the swarm keeps introducing new shared material (domains, page names, phrases) that
persists, an artifact cannot predate the first appearance of the newest material it contains. This is calendar information from
population accretion, not from a divergence clock, and it is one-sided (a lower bound).

- Units: D_primary introductions (7,964; masked). Anchors (times known) = pages with q in {0, 2}. Pilot targets = q = 1;
  confirmation targets = q = 3 (computed only after the pilot, with the variant it selects; nothing else changes).
- For target x, eligible anchors: different label, different page, and Jaccard(x, a) < 0.3 (near-duplicates excluded, time-blind,
  so co-time cannot drive the result). Features: 3-shingles of x whose anchor document frequency (all anchors) is <= 50 and which
  occur in >= m eligible anchors. first(s | x) = earliest time among eligible anchors containing s.
- TPQ_x = stat over x's features of first(s | x). Targets with no feature are uncovered (coverage reported).
- Variants (pilot picks one): stat in {max, 90th percentile} x m in {1, 2}; criterion = success_real - mean(success_null) on pilot targets
  (ties -> max, m = 2).
- Success: t_x in [TPQ_x - 1 h, TPQ_x + 24 h] (dated to within a day, allowing 1 h of violation).
- Null: anchor times permuted among anchors (B = 200), features and eligibility unchanged; TPQ and success recomputed.
- T1 (primary, confirmation targets): success_real > 97.5th percentile of the null AND success_real - mean(null) >= 0.10.
- Secondary/descriptive: validity P(t_x >= TPQ_x - 1 h) real vs null; median t_x - TPQ_x; share of successes with t_x - TPQ_x >= 1 h
  (day-scale rather than recency); variant with near-duplicates allowed; set r2 (burst and template removed).
- Reading: T1 true -> text carries a one-sided, day-scale calendar signal through accretion of shared material, even without a clock
  and without near-duplicates. T1 false -> not even a day-scale lower bound beyond co-time.
