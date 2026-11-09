# RESULTS_LOG: every result obtained so far (verbatim from the Colab runs)

All numbers below were produced by the notebooks in `notebooks/` on 2026-11-08 (Chile time, UTC-3), and pasted back by MP. They are the regression targets: the refactored pipeline must reproduce them (exactly for counts; within ±0.01 for statistics; p-values may differ slightly due to permutation randomness, but must not cross 0.05 in the opposite direction).

Random seed used in Part 2b onward: `rng = np.random.default_rng(20261108)`.

---

## Part 1: Swarm Traces schema and anchors (Gate 1)

### Schema
```
rows: 189579
[('id', 189579), ('cite', 189579), ('kind', 189579), ('parent_id', 189579), ('time_utc', 189579), ('tags', 189579), ('text', 189579)]
id         sample='R0000001'
cite       sample='R0000001:865502a6'
kind       sample='payload'
parent_id  non-null(first5k)=0
time_utc   non-null(first5k)=0
tags       non-null(first5k)=0
text       sample='fetch("https://[REDACTED:destination:000002][SERVICE 2 URL 1]",{method:\'POST\',...'

kind [('payload', 91037), ('recovered_text', 75534), ('response', 23008)]
tags [('', 189542), ('article-evidence;appendix-request', 3), ('article-evidence;g236-command;g23619cmd.bin;command-000007', 2), ... ]
median length: text 313.5, cite 17, id 8, kind 7
TEXT field = text
```
Note: `parent_id` and `time_utc` were null in the first 5k rows; time_utc appears empty throughout (consistent with Swarm Traces' own statement that 97% of payloads lack native timestamps). parent_id over the full file was NOT checked yet (TODO, cheap).

### Anchors (window 2026-05-01 to 2026-07-31, epochs 1777593600..1785456000)
```
records with >=1 anchor: 2948 of 189579 (1.6%)
kind counts (anchor rows): epoch_s 2557, date_str 1185, epoch_ms 48, gzip_mtime 9   (no jwt_iat found)

records by kind x inherited (anchor value shared by >1 record = inherited):
              False  True
date_str        98    677
epoch_ms         8     30
epoch_s        734   1451
gzip_mtime       2      7

independent anchors by day:
2026-05-09 1 | 05-17 1 | 05-18 4 | 05-26 2 | 05-27 12 | 05-28 1 | 05-29 1 | 06-01 2 | 06-14 1 | 06-17 2 | 06-18 4
2026-07-09 16 | 07-10 8 | 07-11 492 | 07-12 244 | 07-13 19 | 07-18 9 | 07-19 10
```
Correct derived figures: 827 records with an independent anchor = 28% of the 2,948 anchored records; 736 of 827 (89%) on 2026-07-11/12.
(An earlier chat message said "65% inherited"; that was a miscalculation and is NOT to be used.)

### Families (masked MinHash LSH, k=5 token shingles, threshold 0.5) and Gate 1
```
independent anchored records: 827
families with >=15 independent anchors: 3
top families: 46367:137, 178530:22, 113563:17, 45240:12, 10867:11, 52361:10, 10987:8, ...
GATE 1 FAILED -> fall back to the wiki-only measurement study
```
Manual audit of 20 anchors (see attachment in chat): anchors are real-looking times embedded in exploit code (URLs with epoch parameters, comments like "Jul9"). Family 46367 (largest, 137 anchors) is IDENTICAL after masking (`location='https://[REDACTED...]'`): the anchor is the only varying part, so divergence = 0 and no clock is possible there. One family (121615) has May anchors on `/response-headers?...` text, plausibly noise or a different traffic source.

---

## Part 2a (cell outputs, partially) and Part 1 section 4: collusion.wiki structure
```
14591 revisions
relation_type {'None': 14528, 'first_recreation_of': 63}
diff_base_reason {'None': 10012, 'page_created': 4562, 'earlier_revisions_not_published': 17}
time_grade {'reqlog': 14482, 'rclog': 103, 'write_date': 6}
request_action {'form_edit': 14482, 'None': 109}
wiki {'dse': 13403, 'probier': 1013, 'fractal': 169, 'dorfwiki': 6}
uncertainty_seconds: all = 1.0 (count 14591, std 0)
hunks example: [{"op": "insert", "a0": 0, "a1": 0, "b0": 0, "b1": 1}]   (line positions, not text)
related_event_id non-null: 63
body_encoding: ascii 14340, utf8 250, latin1 1
hunk ops: insert 10238, replace 5267, delete 784
diff_base examples: ('dorfwiki~AgentDataUSAProbeFebX2@2', 'dorfwiki~AgentDataUSAProbeFebX2@1', None), ... (diff_base = rev_id string of the base revision)
```

### Introductions
```
how: hunks 9987 | created 4562 | no_hunks 42
unparseable times: 0
median intro/body length ratio (hunks): 0.4608
after filters (time < 2026-07-03, reqlog, not bad_index): 14482
introductions with >= 8 tokens: 10643
most edited pages: dse/WillkommenImWiki 2321, dse/StartSeite 436, dse/TestSeite 237, dse/HealthdataCVDSequenceCollab 121, dse/DataUSAStateSequenceCollab2027 97, dse/Sector61State5FastSignal 73, dse/RecentChanges 70, ...
```
Manual audit of 8 introductions: they contain only new text (status reports like "R3 CONFIRMED: Poland arrived task 22:43:07 ...", link lists, coordination messages). OK.

### Families (k=5, threshold 0.5, hubs NOT excluded in 2a)
```
families total: 7144 | eligible (>=15 blocks): 1 | reps in eligible: 314
family 5203: blocks 314, pages 314, labels 58, 2026-06-18 20:09:40 to 20:14:55 (span 0.0875 h, 1 day)
example: "=Loop predicted child raw investor= * [https://jqp.vercel.app/<PATH> InvYear0] ..."
```

### Sensitivity diagnostic (hubs excluded: WillkommenImWiki, StartSeite, TestSeite, RecentChanges)
```
k5 t0.5 {'eligible': 1, 'multi_day(>=3d)': 0, 'span>=24h': 0, 'largest_family_share': 0.041, 'span_h_quantiles(>=5 blocks)': [0.02, 0.1, 0.32, 0.59]}
k5 t0.3 {'eligible': 3, 'multi_day(>=3d)': 2, 'span>=24h': 2, 'largest_family_share': 0.042, 'span_h_quantiles(>=5 blocks)': [0.07, 0.28, 0.9, 5.92]}
k3 t0.3 {'eligible': 6, 'multi_day(>=3d)': 3, 'span>=24h': 3, 'largest_family_share': 0.043, 'span_h_quantiles(>=5 blocks)': [0.1, 0.45, 3.34, 86.93]}
k3 t0.2 {'eligible': 2, 'multi_day(>=3d)': 1, 'span>=24h': 1, 'largest_family_share': 0.207, 'span_h_quantiles(>=5 blocks)': [0.1, 0.26, 1.13, 70.84]}
```
Pre-declared rule (">= 5 eligible families with >= 3 days and largest share < 20%") NOT met in any config. Primary config frozen as k=3, threshold 0.3.

---

## Part 2b: Finding B (lifespans), exploratory test, first calibration
```
real introductions (hubs excluded): 7964

config             families>=5  eligible  multi_day  median_span_min  p75_h  p90_h  share_>24h  largest_share
k5 t0.5                 39          1         0           6.1         0.32   0.59    0.000        0.041
k5 t0.3                 52          3         2          16.6         0.90   5.92    0.077        0.042
k3 t0.3 (primary)       60          6         3          27.2         3.34  86.93    0.167        0.043
k3 t0.2                 40          2         1          15.3         1.13  70.84    0.175        0.207
```
Eligible families (primary):
```
family  blocks labels  t0                    t1                    span_h   days  what it is
5203     314    58     2026-06-18 20:09:40   2026-06-18 20:14:55     0.09    1    exact-copy burst ("=Loop predicted child raw investor=" jqp link lists)
5455     154   117     2026-05-31 22:39:47   2026-07-01 00:06:03   721.44    7    DataUSA link lists ("Public official data links for research...")
6843     121   119     2026-06-01 12:46:23   2026-06-22 08:35:21   499.82    9    wiki default new-page text "Beschreibe hier die neue Seite." + varying content
2844      28    31     2026-06-17 02:24:35   2026-06-20 18:49:16    88.41    3    round-status reports ("R0 CONFIRMED: ... arrived task ...; answered ...")
1979      20    12     2026-06-18 18:04:04   2026-06-18 21:07:54     3.06    1    SEC/Investor county endpoint link pages
2378      15     4     2026-05-28 14:12:43   2026-05-29 00:00:54     9.80    2    archival link lists (pure.md / jqp)
```
Exploratory temporal test (length strata): T = 0.292, p = 0.001; per-family rho [0.244, 0.819, 0.415, 0.063, -0.081] (5203 has no variance).

First calibration (CONTAMINATED design: tested the whole recovered family, which included real members):
```
kind  p     recovery  completeness  sig_rate
clock 0.02  1.00      1.00          0.85
clock 0.05  1.00      1.00          0.95
clock 0.10  0.85      0.95          0.88
clock 0.20  0.00      0.23          NaN
star  0.02  1.00      1.00          0.20   <- anti-conservative
star  0.05  0.85      0.87          0.12   <- anti-conservative
star  0.10  0.00      0.20          NaN
star  0.20  0.00      0.03          NaN
```

---

## Part 2c: confound controls and corrected calibration
Per-family rho (length strata):
```
family reps days strata  rho
1979    20   1    3     0.244
2378    15   2    3     0.819
2844    28   3    3     0.415
5203   314   1    3     NaN
5455   154   7    3     0.063
6843   121   9    3    -0.081
```
Real tests:
```
real                    length      6  T=0.292  p=0.001
real                    day         6  T=0.292  p=0.001
real                    day_length  6  T=0.292  p=0.001
real, template removed  length      5  T=0.385  p=0.001
real, template removed  day         5  T=0.385  p=0.001
```
(T is identical across strata by construction: the observed statistic does not depend on strata; only the null does. p = 0.001 is the floor with B = 999. Code was reviewed: no bug.)
Template-removed eligible families: 5203 (314), 5432 (154, 721 h, 7 d), 2827 (28, 88 h, 3 d), 1967 (20, 3 h), 2363 (15, 9.8 h). Same rhos as above for the matching families.

Corrected calibration (planted members only):
```
kind  p     recovery  contaminated  sig_length  sig_day  sig_contaminated
clock 0.02  1.0       1.0           0.90        0.45     0.95
clock 0.05  1.0       1.0           0.95        0.45     0.95
clock 0.10  0.8       1.0           0.88        0.69     0.94
star  0.02  1.0       1.0           0.10        0.00     0.15
star  0.05  0.7       1.0           0.07        0.00     0.00
star  0.10  0.0       1.0           NaN         NaN      NaN
```
Reading: corrected test is near-nominal (length) or conservative (day); clock power high (length) / moderate (day).

---

## Part 2d: clock vs recency
Lag curves (mean 1 - Jaccard by lag bin):
```
set      family  <10m   10-30m 30m-1h 1-3h  3-6h  6-12h 12-24h 1-3d  >3d
primary  1979    0.354  0.914  0.934  0.898 0.922  NaN   NaN    NaN   NaN
primary  2378    0.086  0.138  0.603  0.856 0.947 0.979  NaN    NaN   NaN
primary  2844    0.862  0.821  0.853  0.919 0.946  NaN   NaN   0.947 0.983
primary  5203    0.000  NaN    NaN    NaN   NaN    NaN   NaN    NaN   NaN
primary  5455    0.871  0.908  0.909  0.912 0.915 0.920 0.912   NaN  0.919
primary  6843    0.744  0.883  0.899  0.891 0.925 0.925 0.903  0.925 0.878
(template_removed rows identical for the matching families)
```
Window tests, all pairs:
```
primary           short (<6h)        5 fam  T= 0.317  p=0.001  per_family [0.244, 0.819, 0.342, nan, 0.058, 0.122]
primary           long (>=6h)        4 fam  T=-0.174  p=0.989  [nan, -0.775, 0.307, nan, -0.046, -0.182]
primary           very long (>=24h)  3 fam  T=-0.029  p=0.738  [nan, nan, 0.299, nan, -0.165, -0.221]
template_removed  short              4 fam  T= 0.365  p=0.001
template_removed  long               3 fam  T=-0.172  p=0.928
template_removed  very long          2 fam  T= 0.066  p=0.203
```
Synthetic reference curves (planted, 7 days):
```
clock p=0.02  30m-1h 0.428 | 1-3h 0.332 | 3-6h 0.327 | 6-12h 0.337 | 12-24h 0.370 | 1-3d 0.465 | >3d 0.605
clock p=0.05  10-30m 0.714 | 30m-1h 0.576 | 1-3h 0.601 | 3-6h 0.588 | 6-12h 0.605 | 12-24h 0.614 | 1-3d 0.730 | >3d 0.850
star  p=0.02  ~0.54-0.58 flat
star  p=0.05  ~0.83-0.86 flat
```
Synthetic window-test rejection rates (per lineage, B=199):
```
clock p=0.02: short 0.05, long 1.00, very long 0.95
clock p=0.05: short 0.05, long 0.95, very long 0.95
star  p=0.02: short 0.05, long 0.00, very long 0.10
star  p=0.05: short 0.05, long 0.05, very long 0.10
```
Same label vs different label, pairs with lag < 1 h:
```
family  pairs same  d same  pairs diff  d diff
1979      21        0.157     100       0.904
2378      31        0.297       2       0.692
2844       2        0.941      62       0.840
5203    2591        0.000   46550       0.000
5455      57        0.752    3240       0.892
6843      16        0.744     538       0.867
```
Cross-label window tests (same-label pairs excluded), the decisive result:
```
primary           short (<6h)        T=-0.005  p=0.710  per_family [-0.073, -0.473, 0.353, nan, 0.054, 0.113]
primary           long (>=6h)        T=-0.174  p=0.995  [nan, -0.775, 0.307, nan, -0.046, -0.182]
primary           very long (>=24h)  T=-0.030  p=0.707  [nan, nan, 0.299, nan, -0.166, -0.221]
template_removed  short              T=-0.036  p=0.807
template_removed  long               T=-0.172  p=0.963
template_removed  very long          T= 0.066  p=0.193
```

---

## Pending (not yet run)
- Part 3a: sampling-matched power (edit rates 0.0025 to 0.20), NCD ablation, k5 t0.3 sensitivity.
- Part 3b: Mantiq schema discovery, then replication design.
- Swarm Traces: check `parent_id` over the full file; describe kind-specific anchor rates.
- Positive control with the 63 `first_recreation_of` pairs (distance should be near 0).

---

## Session 2026-11-08 evening (refactored pipeline, `scripts/run_stage.py`). Source of truth: `outputs/tables/`
- Regression vs everything above: PASS (`outputs/REGRESSION.md`).
- Part 3a power (sampling-matched, 200 reps, B=99), long-lag test, all / cross-label: 0.0025: 0.60/0.61; 0.005: 0.70/0.74; 0.01: 0.86/0.89; 0.02: 0.87/0.88; 0.05: 0.94/0.96; 0.10: 0.92/0.94; 0.20: 0.94/0.95.
- Cross-label short / >=24 h power (post hoc, 100 reps): 0.93 to 1.00 / 0.86 to 0.99 over 0.0025 to 0.20.
- NCD ablation: short 0.321 (0.001), long -0.197 (0.994), very long 0.089 (0.314); cross-label short 0.003 (0.753). k5 t0.3: 3 eligible families, no window significant.
- Robustness (post hoc, D8): long-lag LOFO all p >= 0.47 (T = 0.026 without the 11-pair archival family); short all-pairs LOFO all p = 0.001; cross-label short LOFO without archival family T = 0.112, p = 0.017 (cross-label null fragile).
- Calibration x10 (200 lineages/cell): star planted-only 0.04/0.04; star contaminated 0.15/0.15; clock length 0.95-0.99, day 0.49-0.59.
- Recreation control: premise failed (median distance 1.0; 4/60 identical).
- Swarm Traces parent_id: 61,125 non-null (derivation links to payloads).
- Mantiq (PREREG commit f6dd463): U-M 19 / U-F 36 eligible as written; decisive cross-agent long-window tests undefined; power at alpha 0.025: U-F clock 0.11 to 0.31, star 0 to 0.04, U-M 0 -> inconclusive. Post hoc: dedup messages 0 eligible; no pytest boilerplate 2 eligible. Copy channels: 88% of workspace versions are git copies; 61% of agent-authored git copies from another agent; 94% (4,438/4,700) of edits on agent-written bases by the same agent.
- Extensions (PREREG_EXTENSIONS.md): C same-label short T = 0.257 (p = 0.003), template removed 0.221 (0.014); B cross-label tau 0.039 h (half-life 1.6 min; CI tau 0.03 to 0.93 h), same-label tau 1.22 h (half-life 51 min; CI 0.006 to 2.72 h); A observed exposure AUC 0.478 [0.453, 0.492], 125,390 pairs (28,438 exposed), mean containment 0.005 exposed vs 0.017 unexposed; A2 short T 0.010 (p 0.18), long T -0.038 (p 0.75).
- End-to-end power (D13, 200 reps, LSH rebuilt on the whole corpus, planted members only): clock detection 0.005: 0.685; 0.01: 0.725; 0.02: 0.840; 0.05: 0.755; 0.10: 0.590; 0.20: 0.000 (lineage recovery 99.6, 98.8, 96.3, 69.5, 30.9, 0.8%); star false positives 0.010 / 0.045 / 0.000 at 0.01 / 0.05 / 0.10. Supersedes the "0.01 to 0.05 excluded at >= 80%" statement.
