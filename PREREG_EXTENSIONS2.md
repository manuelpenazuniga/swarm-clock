# Pre-registration: extensions A-prime and C2 (2026-11-08, before computation)

Committed BEFORE any of these quantities was computed. Motivation: three independent strategy reviews (GPT-6 Astra, Gemini 4 Argon, Opus) identified (i) file-system reads as the main caveat of extension A and (ii) the purely lexical distance as the main ML objection. Already known: everything in paper/report.md, including extension A (AUC 0.478 with file-system reads). For A-prime, only the existence and format of `model.request` events and `request_body` blobs was checked (one run: 522 requests, all exported, median 36 KB), not any overlap with sources.

## A-prime. Model-level exposure in Mantiq

- **Sources** (as in A): contents first written by an agent w (earliest `made_by == "agent"` version with that sha256 in the run), exported text, pytest boilerplate and `.git` paths excluded; authorship time t_auth.
- **Probes.** For each source, up to 3 longest distinct non-blank lines of its raw text with at least 30 characters (stripped). Sources with no such line are excluded (reported).
- **Model context.** For each `model.request` event of agent r (time t_req), the request body is parsed as JSON and all string values are concatenated; if parsing fails, the raw text is used.
- **Model exposure.** Source s is in r's model context before target x if some request of r with t_auth(s) < t_req < t_x contains at least one probe of s verbatim. Only sources with w != r.
- **Targets** (as in A): r's U-F introductions with boilerplate excluded (`U-F-noboiler`).
- **A1-prime (primary).** Within-target AUC: for each target with at least one model-exposed and one unexposed source, the AUC of containment c(x, s) (exposed vs unexposed); report the mean over targets with a 95% bootstrap interval over runs (999), and the number of targets. Secondary: pooled pair-level AUC (as in A). Prediction if agents copy from their context: within-target AUC > 0.5.
- **A2-prime (descriptive).** Among model-exposed pairs, Spearman of distance (1 - c) vs lag since first model exposure (fraction of run), short and long windows as in PREREG_MANTIQ; reported descriptively (no p-values, because pairs share targets and sources).
- **Coverage.** Report the share of sources that ever appear in any request of any other agent.

## C2. Non-lexical-token check on the wiki (character n-grams)

Same six primary families, representatives, strata, windows and B = 999 as Table 3 (all pairs and cross-label), with distance = 1 - cosine similarity of character 4-gram TF-IDF vectors (scikit-learn `TfidfVectorizer(analyzer="char_wb", ngram_range=(4, 4))`, fitted on the representatives of each family) on the masked text. Prediction: same pattern as Jaccard (positive short-lag all-pairs T, no positive long-lag T).

## P. Real-data positive control (added 2026-11-08 ~23:20, before computation)

Question: does the same window test fire on real agent text when accumulation exists by construction? Unit: full page bodies (not introductions) of wiki pages with at least 15 revisions in the analysis window (request-log times, before 2026-07-03), hubs INCLUDED (they are the most-edited pages), masked with the same masker. Each page is one "family"; each revision is one block (no representative selection). Distance: 1 - Jaccard on k = 3 shingles; strata: length terciles within page; windows as Table 3; B = 999; all pairs and cross-label. Prediction: positive long-lag T with p < 0.05 (bodies accumulate content over time, pitfall 2 of CONTEXT.md). If it does not fire, the test is insensitive even to built-in accumulation and the paper must say so.
