# Pre-registration addendum H: relay vs broadcast on a held-out set (hub-page introductions)

Written 2026-11-09 ~00:56 America/Santiago (system clock at hashing is authoritative), BEFORE any order or lag statistic on this set.
Known at writing: PREREG_FRONTIER.md lines D and A and their results (D failed: confirmation accuracy of the pilot-selected
score 0.47 [0.41, 0.53]; pooled over both splits, polarity S1 0.48 [0.42, 0.55]); EXPLORATORY simulations (scripts/d_positive_control*.py)
showing that S1 orders planted relay clusters (copies of copies, real cluster sizes) at 0.79-0.82 (token edits) and 0.66-0.75
(donor-block edits of real phrases), and planted broadcast clusters (independent copies of one source) at 0.46-0.51.
Computed before writing on this set (time-blind): 2,679 hub introductions (4 hub pages, 514 labels; template texts removed);
different-label pairs with Jaccard in [0.3, 0.999): 7,758 in 52 components (largest 2,220 pairs).

Held-out set: introductions on the four hub pages (dse/WillkommenImWiki, StartSeite, TestSeite, RecentChanges) from
data/interim/wiki_intros.parquet (same masking as D_primary, >= 8 tokens), default-page template texts removed. These were excluded
from every analysis in the paper and in PREREG_FRONTIER.md.
- Pairs: different label (same page allowed: hubs are shared boards), s = Jaccard(k = 3) in [0.3, 0.999), |lag| >= 1 s.
- Score fixed in advance: S1 rare-variant polarity, as in PREREG_FRONTIER.md, except the exclusion set: df'(x) counts introductions in
  wiki_intros.parquet (10,643; D_primary plus hubs) containing x, excluding those written under label(A) or label(B) and A, B themselves
  (pages are not excluded, because the hub page is where other agents' relatives live). S0 (length) reported alongside.
- Metric: component-balanced accuracy (components of the pair graph), 95% CI by component bootstrap (2,000).
- H1 (broadcast, primary): upper 95% CI bound of S1 accuracy < 0.66 (the weakest simulated relay value).
- H2 (relay detectable): lower 95% CI bound of S1 accuracy > 0.5.
- Reading: H1 true and H2 false -> cross-agent near-duplicates on the hubs, too, lack the ancestral polarity that relay copying leaves
  (broadcast-like). H2 true -> content orders hub posts (relay present there), a real-data positive for direction.
  Neither -> inconclusive. Exploratory: S0, S2, lag strata (< 10 min, >= 10 min), unweighted accuracy.
