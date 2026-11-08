# Pre-registration: Mantiq replication (zenml/mantiq-swarm-traces, CC-BY-4.0)

Written 2026-11-08 ~20:06 America/Santiago, committed to git BEFORE any temporal quantity (time, lag, distance-vs-lag, family span) was computed or inspected on Mantiq. What had been inspected: the dataset card, table schemas, row counts, message lengths (median 158 characters), the share of agent-written file versions with exported text (80.3%), mounts, file extensions and top-level path names. Nothing about timing.

The dataset card asks that its canary GUID not enter training corpora; we never copy it into the repo or paper.

## 1. Question
In a cooperative swarm that builds a shared code base (1 planner, 16 workers, 1 judge; 19 runs of 11 to 45 minutes; true `agent_id`), does artifact text accumulate divergence with time, in particular across agents? This is the same question as on collusion.wiki, asked where identity is ground truth and where agents genuinely build on each other's work.

## 2. Units of analysis (analyzed separately, never pooled)
- **U-M, messages.** Each inter-agent message body (`messages.body_sha256` -> `blobs.text`), sent, whether delivered or not. Introduction = the full message. Actor = `from_agent_id`. Time = `events.ts_wall_ns` of `sent_event`. Block = the message itself.
- **U-F, file introductions.** File versions with `made_by == "agent"` and `kind in {create, write}` whose text is exported (`file_versions.sha256` -> `blobs.text`). Excluded paths: anything under `.git/` or `upstream.git`, `__pycache__`, `*.pyc`, sed temporary files (`sed??????`), and files with non-text extensions. Introduction = lines added relative to the previous version of the same file (`prev_version_id`; `difflib.SequenceMatcher` on lines, `insert` and `replace` opcodes, new side), or the full content when the version is a create or the previous text is not exported. Actor = `agent_id`. Time = `events.ts_wall_ns` of the version's `event_id`. Normalized path = path with the mount prefix removed. Block = (family, agent_id, normalized path), so the same file maintained by two agents forms two blocks.

## 3. Masking (applied before families)
Wiki masker (URL paths, dates, tokens of 24+ characters -> `<TOK>`, digits -> 0), plus: agent IDs (`a` + two digits) and workspace mounts (`ws/aNN`) -> `<AGENT>`; relative timestamps written by the scrubber (`T+<n>s`) and any remaining time-like strings -> `<DATE>` (critical: these encode time); hexadecimal strings of 7+ characters -> `<HASH>`; slash-containing path tokens -> `<PATH>`. Keep introductions with at least 8 tokens.

## 4. Families (identical to the wiki primary)
MinHash (128 permutations) LSH on k = 3 token shingles, threshold 0.3, connected components; built **separately within each run** (IDs and content cannot join across runs, and shared task text would create spurious cross-run families). Chaining check: if the largest family holds more than 20% of a unit's blocks in a run, the run's families are flagged as chained; the pre-specified fallback for the window tests is then (k = 5, threshold 0.5), reported alongside the primary.

## 5. Eligibility
At least 15 blocks per family (same count as the wiki; it is a count, so it does not depend on time scale). One date-blind representative per block (the longest masked introduction). Lifespans are reported for families with at least 5 blocks, in seconds and as a fraction of the run's duration (`runs.seconds`).

## 6. Time scale and windows (rescaled to run duration, declared a priori)
Lag is expressed as a fraction of the run's duration D. Windows: short lag < D/3; long lag >= D/3; very long lag >= 2D/3. Lag-curve bins (fraction of D): [0, 0.05), [0.05, 0.1), [0.1, 0.2), [0.2, 1/3), [1/3, 0.5), [0.5, 2/3), [2/3, 1].

## 7. Tests (same statistic and null as the wiki)
Within each family: Spearman correlation between pairwise 1 - Jaccard (k = 3 shingles) and pairwise lag, restricted to the window; averaged across eligible families pooled over runs. Null: permute times among representatives within family x length-tercile strata. One-sided. B = 999. Two pair sets: all pairs; cross-agent pairs (pairs with the same true `agent_id` excluded).
**Decisive tests:** cross-agent, long window (>= D/3), one per unit. Two decisive tests, each at alpha = 0.025 (Bonferroni). Everything else is descriptive or secondary.

## 8. Calibration with Mantiq's real sampling
For every eligible family: (a) **sampling-matched clock**: reuse the family's real times, actors and size; root = earliest real introduction; each member copies one of the 5 previous members (in time order) and applies token-level edits at rate p in {0.0025, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20}; (b) **sampling-matched star**: each member is an independent edit of the root at rate 3p with the real times (null with real sampling). 100 replicates per rate, B = 99, test = the decisive long-window test (all pairs and cross-agent). Vocabulary for edits: tokens of the unit's own masked introductions.

## 9. Predictions
- **H_coop** (accumulating construction): cross-agent long-window T > 0 with p < 0.025 in at least one unit, and lag curves that keep rising beyond D/3.
- **H_null** (no accumulating clock, as on the wiki): long-window T <= 0 or p >= 0.025 in both units, with calibration showing power >= 80% for some range of edit rates.

## 10. Decision points (not to be relaxed after seeing data)
- If a unit has text for fewer than 50% of its candidate records, or fewer than 5 eligible families pooled over runs, that unit is reported as a limitation and not tested.
- If neither unit is testable, Mantiq is reported as a limitation only.
- Runs with planted faults are included in the primary analysis (faults are incidental to the question). Pre-specified sensitivity: the 7 practice runs with nothing planted (practice_01, 02, 04, 05, 07, 08, 09).
- Pre-specified sensitivity for U-F: exclude judge/status files (`JUDGE.md`, `round.txt`).

## 11. Interpretation (from CONTEXT section 9, fixed in advance)
- Cross-agent clock in Mantiq but not on the wiki -> "accumulating construction leaves a clock; recency boards do not"; retitle.
- No clock in either -> the thesis generalizes to two very different swarms (adversarial covert board vs cooperative engineering team).
- Power below 80% at every edit rate -> Mantiq is inconclusive for that unit; reported as such.
