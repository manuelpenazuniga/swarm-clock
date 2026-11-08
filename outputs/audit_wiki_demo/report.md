# swarmclock audit report

Input: `data/interim/wiki_audit_input.jsonl` (actor=`label`, time=`t`, text=`m`, doc=`page_id`)

**Verdict:** no cross-actor long-lag signal (T=-0.174, p=0.987); accumulating clocks with per-copy edit rates in [0.01, 0.1] would be detected with >= 80% power

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

| planted   |   edit_rate |   reject_long_all |   reject_long_cross_actor |   reps |
|:----------|------------:|------------------:|--------------------------:|-------:|
| clock     |       0.005 |             0.600 |                     0.667 |     30 |
| clock     |       0.010 |             0.700 |                     0.800 |     30 |
| clock     |       0.020 |             0.900 |                     0.900 |     30 |
| clock     |       0.050 |             0.867 |                     0.900 |     30 |
| clock     |       0.100 |             0.967 |                     0.967 |     30 |
| star      |       0.005 |             0.000 |                     0.000 |     30 |
| star      |       0.010 |             0.067 |                     0.067 |     30 |
| star      |       0.020 |             0.000 |                     0.033 |     30 |
| star      |       0.050 |             0.033 |                     0.100 |     30 |
| star      |       0.100 |             0.000 |                     0.000 |     30 |

Max false-positive rate of planted no-clock stars (cross-actor): 0.10 (nominal 0.05).

## How to read this

- A positive short-lag statistic that vanishes for cross-actor pairs means similarity comes from actors revising their own text.
- A clock requires a positive long-lag cross-actor statistic AND adequate calibrated power; a null without power is inconclusive.
- Similarity is not transmission: families are candidate reuse, not proof of copying. Actor labels may not be identities.
