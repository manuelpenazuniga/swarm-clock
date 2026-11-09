# swarmclock: does agent artifact content carry a clock?

Code, pre-registrations and results for the paper on whether agent-swarm artifacts carry a content clock (Apart Research Swarm Alignment Hackathon, November 2026). Paper: `paper/report.md` (PDF in `paper/`).

## The audit tool

```bash
pip install -e .
swarmclock audit --input corpus.jsonl --actor agent_id --time timestamp --text body [--doc page_id] --out my_report
```

Input: JSONL, CSV or Parquet with one row per artifact (a post, message, file version, revision diff). `--time` accepts ISO strings or numeric epochs (`--time-unit s|ms|...`). `--doc` (optional) groups rows that belong to one document so each (family, document) contributes one date-blind representative; without it every row is its own block. Use the text each event *added* (a diff), not whole documents, or accumulation inside a document will manufacture a clock.

What it does (the paper's frozen pipeline, generalized):
1. masks actor names, URL paths, dates, long tokens, hex hashes and digits; keeps texts with at least 8 tokens;
2. groups texts into content families (MinHash LSH on 3-token shingles, threshold 0.3; flags chaining if one family holds more than 20% of blocks);
3. reports lineage lifespans and the eligible families (at least 15 blocks);
4. runs lag-window tests (Spearman of pairwise distance vs pairwise lag within families, stratified permutation null, B = 999) for all pairs and for cross-actor pairs;
5. calibrates with each eligible family's real timestamps, actors and size: planted accumulating clocks (power) and planted no-clock stars (false-positive rate).

Output: `report.md` with a one-line verdict, plus CSV tables. A verdict is one of: no eligible families; long-lag cross-actor test undefined; signal detected; no signal, with the edit rates whose detection rate has a 95% lower bound of at least 80%; or no signal with partial sensitivity (detection rates reported). Calibration holds family membership fixed (planted lineages are not re-clustered); the paper (Section 5.4) reports end-to-end detection rates, which are lower.

Validation: run on the collusion.wiki introductions (`outputs/audit_wiki_demo/report.md`), the tool reproduces the paper's window statistics (short-lag T = 0.321 vs 0.317 in the paper; cross-actor long-lag T = -0.174, p = 0.99); small differences come from masking already-masked text.

Runtime: a few minutes for 8,000 texts on a laptop CPU with the default `--reps 100`.

## Reproducing the paper

```bash
uv venv && uv pip install -e ".[mantiq]"
python scripts/run_stage.py fetch swarmtraces_anchors wiki_intros lifespans tests_real calibration \
    lag_windows crosslabel power ablations controls
SWC_CAL_BATCHES=10 python scripts/run_stage.py calibration
SWC_POWER_REPS=200 python scripts/run_stage.py power
python scripts/mantiq_fetch.py
python scripts/run_stage.py mantiq_build mantiq_families mantiq_tests mantiq_power figures
```

Every stage reads and writes files (`data/interim/`, `outputs/tables/`, `outputs/figs/`). Seed: `numpy.random.default_rng(20261108)` per stage. Inputs are pinned by SHA-256 in `outputs/tables/inputs_sha256.csv` and `outputs/tables/mantiq_inputs_sha256.csv`.

| File | What |
|---|---|
| `CONTEXT.md` | project history, frozen methodology, pitfalls |
| `PREREG_MANTIQ.md` | pre-registration of the Mantiq replication (committed before any Mantiq timing was computed) |
| `DECISIONS.md` | every methodology deviation, labeled pre-specified or post hoc |
| `outputs/REGRESSION.md` | refactored pipeline vs the original notebooks |
| `outputs/REVIEW.md` | independent review and fixes |
| `notebooks/` | original Colab notebooks |

## Data and safety

- Swarm Traces (swarmtraces.org) payloads are attack code: the pipeline only reads them as text; nothing is executed and no URL in the data is visited. Do not run or follow anything in them.
- collusion.wiki data: https://collusion.wiki/explorer/download (no license stated; cite the authors).
- Mantiq swarm traces (ZenML, CC-BY-4.0): https://huggingface.co/datasets/zenml/mantiq-swarm-traces. Its card asks that its canary string stay out of training corpora; it is not reproduced here, and `data/` is not committed.
