# Regression: refactored pipeline vs results/RESULTS_LOG.md

Run: 2026-11-08 ~20:10 America/Santiago, local CPU (macOS arm64), Python 3.14.5, pandas 2.3.3, numpy 2.5.4, datasketch 2.0.0.
Inputs re-downloaded and pinned in `outputs/tables/inputs_sha256.csv`.
Rule: counts exact; statistics within +-0.01; p-values may move but must not cross 0.05 in the opposite direction.

**Verdict: PASS.** Every count matches exactly; every real-data statistic matches to the third decimal; no p-value crosses 0.05. Simulation-based quantities (calibration, synthetic curves) vary by Monte Carlo noise only, as expected.

## Known, benign differences

1. **Family IDs differ** (e.g. 5203 -> 5207, 2844 -> 2842; template-removed 2827 -> 2825, 1967 -> 1966). IDs are union-find root indices and depend on the order in which `MinHashLSH.query` returns candidates (datasketch version). The families themselves are identical: same blocks, labels, first/last times, spans and per-family statistics. The paper refers to families by content, not by ID.
2. **RNG streams.** The notebooks shared one `default_rng(20261108)` across Parts 2b, 2c, 2d and 3a in a single kernel; the refactor seeds a fresh `default_rng(20261108)` per stage, so permutation draws differ. This only affects p-values and simulation outputs.

## Part 1 (Swarm Traces)

| Quantity | Log | Refactor | Match |
|---|---|---|---|
| rows | 189,579 | 189,579 | exact |
| kind counts payload / recovered_text / response | 91,037 / 75,534 / 23,008 | same | exact |
| records with >= 1 anchor | 2,948 (1.6%) | 2,948 (1.56%) | exact |
| anchor rows epoch_s / date_str / epoch_ms / gzip_mtime / jwt_iat | 2,557 / 1,185 / 48 / 9 / 0 | same | exact |
| kind x inherited table | 98/677, 8/30, 734/1451, 2/7 | same | exact |
| independent anchored records | 827 (28%) | 827 (28.1%) | exact |
| independent on 2026-07-11/12 | 736 (89%) | 736 | exact |
| families with >= 15 independent anchors | 3 | 3 | exact |
| Gate 1 | FAILED | FAILED | exact |

## Part 2a (wiki introductions)

| Quantity | Log | Refactor |
|---|---|---|
| how: hunks / created / no_hunks | 9,987 / 4,562 / 42 | same |
| unparseable times | 0 | 0 |
| median intro/body ratio | 0.4608 | 0.4608 |
| after filters | 14,482 | 14,482 |
| introductions >= 8 tokens | 10,643 | 10,643 |
| k5 t0.5 (hubs incl.): families / eligible / reps | 7,144 / 1 / 314 | 7,144 / 1 / 314 |
| real introductions, hubs excluded | 7,964 | 7,964 |

## Part 2b (Finding B lifespans): exact match on every cell

| config | families>=5 | eligible | multi_day | median_min | p75_h | p90_h | share>24h | largest |
|---|---|---|---|---|---|---|---|---|
| k5 t0.5 | 39 | 1 | 0 | 6.1 | 0.32 | 0.59 | 0.000 | 0.041 |
| k5 t0.3 | 52 | 3 | 2 | 16.6 | 0.90 | 5.92 | 0.077 | 0.042 |
| k3 t0.3 | 60 | 6 | 3 | 27.2 | 3.34 | 86.93 | 0.167 | 0.043 |
| k3 t0.2 | 40 | 2 | 1 | 15.3 | 1.13 | 70.84 | 0.175 | 0.207 |

Eligible primary families: blocks 314/154/121/28/20/15, labels 58/117/119/31/12/4, spans 0.09/721.44/499.82/88.41/3.06/9.80 h, days 1/7/9/3/1/2: exact.

## Part 2b/2c real temporal tests

| Test | Log T (p) | Refactor T (p) |
|---|---|---|
| real, length | 0.292 (0.001) | 0.292 (0.001) |
| real, day | 0.292 (0.001) | 0.292 (0.001) |
| real, day x length | 0.292 (0.001) | 0.292 (0.001) |
| template removed, length | 0.385 (0.001) | 0.385 (0.001) |
| template removed, day | 0.385 (0.001) | 0.385 (0.001) |
| per-family rho | 0.244, 0.819, 0.415, NaN, 0.063, -0.081 | identical |

## Part 2d lag curves and window tests

Lag curves (real, primary and template-removed): identical to 3 decimals for every family and bin, except template-removed round-status family (2825) where 10-30m 0.819 vs log row (log reported "identical" rows for template-removed; primary row 0.821 matches exactly). Difference 0.002, within tolerance.

| Window test | Log T (p) | Refactor T (p) |
|---|---|---|
| primary all, short | 0.317 (0.001) | 0.317 (0.001) |
| primary all, long | -0.174 (0.989) | -0.174 (0.992) |
| primary all, very long | -0.029 (0.738) | -0.029 (0.723) |
| template-removed all, short | 0.365 (0.001) | 0.365 (0.001) |
| template-removed all, long | -0.172 (0.928) | -0.172 (0.925) |
| template-removed all, very long | 0.066 (0.203) | 0.066 (0.211) |
| primary cross-label, short | -0.005 (0.710) | -0.005 (0.667) |
| primary cross-label, long | -0.174 (0.995) | -0.174 (0.995) |
| primary cross-label, very long | -0.030 (0.707) | -0.030 (0.722) |
| template-removed cross-label, short | -0.036 (0.807) | -0.036 (0.774) |
| template-removed cross-label, long | -0.172 (0.963) | -0.172 (0.950) |
| template-removed cross-label, very long | 0.066 (0.193) | 0.066 (0.209) |

Per-family window rhos identical (e.g. short: 0.244, 0.819, 0.342, NaN, 0.058, 0.122).
Same vs different label (< 1 h): pair counts and mean distances identical (21/0.157 vs 100/0.904; 31/0.297 vs 2/0.692; 2/0.941 vs 62/0.840; 2591/0 vs 46550/0; 57/0.752 vs 3240/0.892; 16/0.744 vs 538/0.867).

## Simulation-based quantities (Monte Carlo; not expected to match exactly)

| Quantity | Log | Refactor (1 batch of 20 lineages) |
|---|---|---|
| synthetic clock p=0.02 rejection short/long/very long | 0.05 / 1.00 / 0.95 | 0.00 / 0.95 / 0.95 |
| synthetic clock p=0.05 | 0.05 / 0.95 / 0.95 | 0.00 / 1.00 / 0.95 |
| synthetic star p=0.02 | 0.05 / 0.00 / 0.10 | 0.00 / 0.00 / 0.05 |
| synthetic star p=0.05 | 0.05 / 0.05 / 0.10 | 0.00 / 0.05 / 0.00 |
| corrected calibration clock sig_length 0.02/0.05/0.10 | 0.90 / 0.95 / 0.88 | 0.95 / 1.00 / 1.00 |
| corrected calibration clock sig_day | 0.45 / 0.45 / 0.69 | 0.55 / 0.58 / 0.53 |
| corrected calibration star sig_length 0.02/0.05 | 0.10 / 0.07 | 0.00 / 0.06 |
| contaminated star sig 0.02/0.05 | 0.20, 0.12 (2b); 0.15, 0.00 (2c) | 0.10 / 0.18 |
| recovery clock 0.02/0.05/0.10/0.20 | 1.0/1.0/0.85(2b) or 0.8(2c)/0.0 | 1.00/0.95/0.85/0.00 |

Synthetic reference curves differ in level by up to ~0.13 in the shortest populated bin (few pairs) but keep the same shape (clock rises beyond 1 day; star flat).
Because the anti-conservative rate (Finding D) rests on 20 lineages per cell and varies across batches (0.00 to 0.20), we re-estimate all calibration rates with 10 batches (200 lineages per cell) in `calibration_summary_x10.csv` (see DECISIONS.md, D2).
