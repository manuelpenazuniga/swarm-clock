# swarmclock audit report

Input: `data/interim/wiki_audit_input.jsonl` (actor=`label`, time=`t`, text=`m`, doc=`page_id`)

**Verdict:** no cross-actor long-lag signal (T=-0.174, p=0.987); planted clocks at per-copy edit rates 0.05 to 0.1 are detected with a 95% lower bound >= 80% (fixed families; family recovery not simulated)

## Corpus

- texts after masking (>= 8 tokens): 7964; actors: 2329; span: 946.5 h
- families with >= 5 blocks: 61; lifespan quantiles (h): {0.5: 0.468, 0.75: 3.296, 0.9: 86.771}
- eligible families (>= 15 blocks): 6; largest family share: 0.043

## Lag-window tests (mean within-family Spearman of distance vs lag; stratified permutation null)

| pairs       | window            |      T |     p |   families_with_pairs |
|:------------|:------------------|-------:|------:|----------------------:|
| all         | short (<6h)       |  0.321 | 0.001 |                     5 |
| all         | long (>=6h)       | -0.173 | 0.986 |                     4 |
| all         | very long (>=24h) | -0.028 | 0.716 |                     3 |
| cross-actor | short (<6h)       | -0.001 | 0.696 |                     5 |
| cross-actor | long (>=6h)       | -0.174 | 0.987 |                     4 |
| cross-actor | very long (>=24h) | -0.028 | 0.715 |                     3 |

## Sampling-matched calibration (long window; planted lineages reuse each family's times, actors, size)

| planted   |   edit_rate |   reject_long_all |   reject_long_cross_actor |   reps |   ci_lo_cross_actor |
|:----------|------------:|------------------:|--------------------------:|-------:|--------------------:|
| clock     |       0.005 |             0.740 |                     0.750 |    100 |               0.657 |
| clock     |       0.010 |             0.720 |                     0.770 |    100 |               0.678 |
| clock     |       0.020 |             0.810 |                     0.860 |    100 |               0.779 |
| clock     |       0.050 |             0.900 |                     0.920 |    100 |               0.850 |
| clock     |       0.100 |             0.930 |                     0.940 |    100 |               0.875 |
| star      |       0.005 |             0.020 |                     0.060 |    100 |               0.028 |
| star      |       0.010 |             0.060 |                     0.090 |    100 |               0.048 |
| star      |       0.020 |             0.040 |                     0.060 |    100 |               0.028 |
| star      |       0.050 |             0.020 |                     0.040 |    100 |               0.016 |
| star      |       0.100 |             0.030 |                     0.060 |    100 |               0.028 |

Max false-positive rate of planted no-clock stars (cross-actor): 0.09 (nominal 0.05).

## How to read this

- A positive short-lag statistic that vanishes for cross-actor pairs means similarity comes from actors revising their own text.
- A clock requires a positive long-lag cross-actor statistic AND adequate calibrated power; a null without power is inconclusive.
- Similarity is not transmission: families are candidate reuse, not proof of copying. Actor labels may not be identities.
- Calibration holds family membership fixed: planted lineages are not re-clustered, so fast clocks that would fragment families are counted as detectable. Treat high edit rates with caution.
