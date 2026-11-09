# Independent review and fixes

Reviewer: a fresh subagent that did not write the paper (2026-11-08 ~20:25 to 20:45 Santiago). It had access to the paper, tables, code, docs and git history, not to `data/`. It checked every number against `outputs/tables`, fetched six arXiv abstracts, and viewed every figure. Below: each finding and what was done.

## Critical

| # | Finding | Action |
|---|---|---|
| C1 | Mantiq "not testable" misapplied PREREG section 10: as written both units pass eligibility (19, 36 families); the right route is section 11 (decisive test undefined, power < 80%) -> inconclusive | Fixed: abstract, 5.5, 6, Limitations now say "inconclusive"; post hoc refinements reported separately |
| C2 | "Frozen before temporal results were inspected" untrue for wiki window, cross-label and template analyses | Fixed: Methods opens with a status paragraph (fixed before testing vs exploratory vs pre-registered); Table 2 labeled exploratory |
| C3 | Cross-label "conservative" argument half wrong (label reuse is anti-conservative for the self-revision reading) | Fixed: both directions stated; "self-revision" renamed "same-label revision" |
| C4 | Overclaims ("all chronological signal comes from self-revision", Fig. 3 caption, "no order at all", "rules out", "cannot be made sequential", title) | Fixed: new title "No Content Clock in Agent-Swarm Corpora: Artifact Similarity Is Short-Range Recency, Not Accumulating Lineages"; all listed sentences rewritten. A post hoc leave-one-family-out analysis (D8) then showed the cross-label short-lag null is fragile (T = 0.112, p = 0.017 without the 15-page archival family); the paper now reports weak cross-label recency within hours |
| C5 | Mantiq copy-channel numbers not produced by committed code; inconsistent denominators (0.533 of 5,632 vs 0.947 of 4,915) | Fixed: new stage `mantiq_copy_channels` with one definition (DECISIONS D10): 4,438 of 4,700 edits on agent-written bases are by the same agent (94%); abstract wording now conditional |

## Important

| Finding | Action |
|---|---|
| Equal-weight averaging; one 11-pair family drives long-lag T and the cross-label drop | Added LOFO and pair-weighted means (`robustness_wiki_windows.csv`); reported in Table 2 and 5.3 |
| Negative long-lag T unexplained | Explained: driven by the 11-pair archival family; T = 0.026 (p = 0.47) without it |
| Power scope overstated; Mantiq power at alpha 0.05 instead of pre-registered 0.025 | Scope sentence added (all four families are clocks; token edits); Mantiq power recomputed with stored p-values and reported at alpha = 0.025 |
| Nulls without power (cross-label short, >= 24 h) | Added `power_short_crosslabel` stage (post hoc, D8); reported in Table 2 |
| ">= 80% power" borderline at 0.01 (Wilson lower bound 0.80) | Reworded: "point estimates exceed 80% ... lower bound 0.80 at the slow end" |
| Finding D applies to the real whole-family tests | Stated in 5.4 and Discussion |
| "days" = distinct dates, not lifespan | Fixed in text and figure labels (e.g. "30 d, 7 dates") |
| Self-revision examples selected; counter-example omitted; N missing | N added for all same/different-label means; round-status counter-example reported; Fig. 6a shows N |
| Fig. 5 is a schematic | Caption and panel titles say "Schematic (not data)"; clipped text fixed |
| PREREG edited after commit | Disclosed (DECISIONS D9, Appendix B) |

## Minor

All applied: nominal 0.05 in abstract; "about 4 times" (not "triples"); anchor rows vs records clarified; "shared with another record"; star 0.10 unrecovered mentioned; Table 3 denominator stated; Fig. 1 legend overlap fixed; pre-specified Mantiq sensitivities reported; Paglieri wording ("shared knowledge library"); Frank "proposes"; Greenblatt author line; Fig. 3 power annotation rounding (0.855 -> 0.86); Mantiq corpus counts now in `mantiq_corpus_summary.json`. "700", "about six weeks" (Murtuza abstract: "over six weeks") and "hash-chained batches" (Mantiq card) were verified against the sources. Repository link: placeholder pending the author's decision to publish.

## Second pass (fresh verifier, 2026-11-08 ~20:57 to 21:00)
Checked every number in the revised paper against `outputs/tables`: all match except four, now fixed: 24-hour cross-label power range 0.86 to 1.00 (was "to 0.99"); LOFO long-lag minimum p 0.468 ("p ≥ 0.46"); longest families "near 0.9 beyond 10 minutes (0.87 to 0.93)" (default-page text is 0.74 under 10 minutes); "two shortest-lived families" instead of "strongest signal". Wording fixes applied: Discussion heading limited to the wiki ("the one corpus we could test"); same-label revision vs cross-label recency attributed to specific families; power scope in abstract and Discussion; abstract labels the window test exploratory and Mantiq descriptives post hoc (249 words); "unlikely to reflect low power"; title narrowed to "Two Agent-Incident Corpora"; pair-weighted means now reported; Fig. 4 caption states α = 0.025 for Mantiq; Fig. 5a copies drawn at distance 0; Fig. 6a title neutral; Fig. 1 label overlap fixed. Status labels (pre-registered / exploratory / post hoc) confirmed correct by the verifier.

## Third pass: Gemini 4 Argon High (via `agy`, 2026-11-08 ~22:00 to 22:20)
Run with all material inline (paper, DECISIONS, PREREG, REVIEW, CONTEXT sections, key tables, stats.py, synth.py); a first attempt in agent mode produced no output because headless mode could not grant shell permission. It audited the version before extensions A/B/C. Scores: impact 3.5, execution 4.0, presentation 4.5. Accepted and fixed:
- Sampling-matched power is conditional on family recovery (texts are not re-clustered); end-to-end calibration recovers 0% of lineages at 0.20 and 70% at 0.10. Headline bound narrowed to 0.01 to 0.05 end to end (abstract, take-away, Figure 0c, 5.4, Discussion); faster clocks fragment lineages, stated explicitly. Tool verdict now says "conditional on the lineage still forming one family".
- Disclosed: generation clock (per copy event), LSH lifespans measure lexical recognizability, masking removes evolving numbers/paths, joint permutation of times across labels and the >= 10-pair rule.
- Mantiq U-F unit limitation (added lines only; one block per agent and file) stated; chaining (4 runs; 2 with fallback) reported; 75% vs 80% text coverage explained; 0.21 lifespan labeled boilerplate-removed; 94% now also given as 79% of all edits with a previous version.
- Title narrowed: "No Usable Content Clock in Two Agent-Incident Corpora: Scarce Anchors in Swarm Traces, Short-Range Recency on collusion.wiki"; abstract "internal anchors cannot date the corpus"; Finding D caution on the far tail of the short-lag p-value.
- Take-away moved below the abstract divider (abstract alone is 249 words).
- Numbers: 0.88 to 0.93 (not 0.87); archival plateau 0.95 to 0.98; p = 0.468; labels 3,102 (recounted from data; CONTEXT said 3,103); `wiki_corpus_summary.json` and `wiki_family_summary.csv` exported.
- Presentation: new per-family table (Table 2) replaces inline numbers; schematic figure moved out of the main text to save space.
- Related work: MemeTracker (Leskovec, Backstrom and Kleinberg, 2009) and BitShred (Jang, Brumley and Venkataraman, 2011) added after verifying both.
Not adopted: re-running sampling-matched power through LSH (replaced by the end-to-end bound from the existing calibration); a full-file U-F sensitivity (whole-file accumulation is the within-document clock the design excludes by construction, pitfall 2).
