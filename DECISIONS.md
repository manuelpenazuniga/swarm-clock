# DECISIONS (methodology changes and their justification)

Frozen methodology: CONTEXT.md section 5. Anything below that touches analysis is labeled PRE-SPECIFIED (decided before seeing the relevant outcome) or POST HOC.

## D1. Per-stage RNG (refactor, 2026-11-08 20:00)
Notebooks shared one `default_rng(20261108)` across cells in a single kernel. The refactor seeds a fresh `default_rng(20261108)` per stage so stages are independent and re-runnable. Affects only permutation draws and simulation outputs. Not a methodology change.

## D2. More Monte Carlo replicates for calibration and power (2026-11-08 ~20:03). Precision only.
Calibration cells and power points were estimated from 20 lineages / 20 replicates, which gives a binomial SE of about 0.05 to 0.11; batches disagreed (contaminated star false-positive rate 0.00 to 0.20). We add replicates with the identical design: calibration with 10 batches (200 lineages per cell), sampling-matched power with 200 replicates per edit rate (B = 99 per test unchanged). Original 20-replicate outputs are kept (`calibration_summary.csv`, `power_sampling_matched.csv`). The paper reports the higher-precision estimates with Wilson 95% intervals. Decided after seeing the noisy 20-replicate numbers, but it changes no design choice, test, or threshold.

## D3. Positive control with `first_recreation_of` pairs: premise failed (2026-11-08 ~20:04). Reported as a finding.
Planned (CONTEXT section 9.3): the 63 recreated pages should be near-copies of the pre-deletion text (distance ~0). Measured: 60 of 63 matched to their deletion event (same page, all 60); masked-body k=3 Jaccard distance to the last pre-deletion revision has median 1.0, mean 0.87; only 4 of 60 (6.7%) are identical. Agents reuse deleted page titles with new content; they do not restore deleted text. This is not a valid positive control of the metric, so we do not use it as one. The metric is validated instead by (a) planted synthetic lineages (calibration) and (b) the real exact-copy burst family (46,550 cross-label pairs at distance 0). No threshold or analysis was changed.

## D4. Swarm Traces `parent_id` (2026-11-08 ~20:04)
Full-file check: `parent_id` is non-null in 61,125 rows (42,708 recovered_text and 18,417 response rows), always pointing to a payload (one exception points to a recovered_text). It encodes derivation (payload -> its response or recovered text), not copying between payloads, and carries no time. Gate 1 and Finding A are unchanged.

## D5. Mantiq U-M: identical fan-out messages (POST HOC sensitivity, 2026-11-08 ~20:09)
Seen after building families (lifespans only, before any window test): every one of the 19 eligible U-M families is a single sender (labels = 1) sending the same text to 15 or more recipients in separate `send_message` calls within seconds (median span 0.1 s). The pre-registered block definition (one block per message) counts each copy as a separate artifact. Pre-registered analysis is run and reported as written. Post hoc sensitivity `U-M-dedup`: keep one introduction per identical (run, sender, masked text), the earliest. Result: 0 eligible families (decision point: not tested).

## D6. Mantiq U-F: tool-generated boilerplate (POST HOC sensitivity, 2026-11-08 ~20:09)
Seen after building families (before any window test): 34 of the 36 eligible U-F families are pytest cache files (`pytest-cache-files-*/README.md` and `CACHEDIR.TAG`), identical in every worker's workspace and recorded as `made_by = agent` because the agent's own process (pytest) wrote them. This is the analogue of the wiki's default-page template, which we ablated there. Pre-registered analysis reported as written; post hoc sensitivity `U-F-noboiler` drops paths matching `pytest-cache-files-|.pytest_cache|CACHEDIR.TAG` (576 introductions). Result: 2 eligible families (decision point: not tested). The eligibility threshold (15 blocks) was NOT lowered.

## D7. Mantiq copy-channel descriptives (POST HOC, descriptive only, 2026-11-08 ~20:10)
To explain why no lineages form: share of workspace file versions delivered by git (exact bytes), how many of those carry content first written by another agent, and whether agent edits build on their own or others' versions. Descriptive, no test; table `mantiq_copy_channels.csv`.

## D8. Robustness of wiki window tests and extra power analyses (POST HOC, after independent review, 2026-11-08 ~20:50)
The reviewer noted that the pooled statistic weights families equally (a family with 11 long-lag pairs counts as much as one with 5,765). We add (a) leave-one-family-out (LOFO) window tests and (b) pair-weighted mean rho (`robustness_wiki_windows.csv`); (c) sampling-matched power of the cross-label short-lag and very-long-lag tests (`power_short_and_verylong_crosslabel.csv`). Findings that change the paper's wording: the long-lag null is robust (no LOFO variant significant; the negative pooled T is driven by the 11-pair archival family, T = 0.026 without it); the all-pairs short-lag signal is robust (p = 0.001 in every LOFO); but the cross-label short-lag null is NOT robust: leaving out the 15-page archival family gives T = 0.112 (p = 0.017), and in the three larger families cross-label rho equals all-pairs rho. The paper now reports weak cross-label short-range association (recency) and no long-range accumulation, instead of "all signal is self-revision".

## D9. Edit to PREREG_MANTIQ.md after its commit (disclosure)
After commit f6dd463, the "Written" line of PREREG_MANTIQ.md was corrected from "~20:40" to "~20:06" (the original was a wrong estimate of the wall-clock time; the commit timestamp 2026-11-08 20:06:46 -0300 is authoritative). No other change was made to the pre-registration (`git diff f6dd463 -- PREREG_MANTIQ.md`).

## D10. Mantiq copy-channel table regenerated by code (after review)
The first version of `mantiq_copy_channels.csv` was produced by ad hoc commands with two inconsistent denominators (0.533 of 5,632 and 0.947 of 4,915). It is now produced by the `mantiq_copy_channels` stage with one definition: agent-written create/write versions with a previous version (5,632); base written by an agent (4,700), of which the same agent wrote 4,438 (94.4%); base delivered by git 28; base unknown 904.

## D11. Git history rewritten to remove attribution trailers (2026-11-08 ~22:00)
At the author's request, the "Co-Authored-By" trailer was removed from every commit message (`git filter-branch --msg-filter`). File contents and author/committer dates are unchanged; only commit hashes changed. The pre-registration commit (formerly 90996c3) is now f6dd463, still dated 2026-11-08 20:06:46 -0300, before any Mantiq timing was computed (first Mantiq analysis commit f679e0b, 20:10:43).
