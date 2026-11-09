# Rogue Swarms Leave No Clock: Artifact Lineages in Two Real Agent Incidents Are Recency Bursts, Not Accumulating Lineages

**Author:** Manuel Peña-Zúñiga (MP), independent (Santiago, Chile)
**Track:** 4 (Multi-Agent Oversight and Control), with implications for Track 3 (Agent Infrastructure)
**Code:** [repo link TBD]

---

## Abstract (150-250 words, final numbers TBD)

Monitoring tools for agent swarms need a clock: sequential detectors cannot run on corpora without timestamps, and an existing swarm monitor explicitly declines to analyze the Swarm Traces corpus for that reason. We ask whether the content of agent artifacts can supply that clock. We study two public datasets from the 2026 OpenAI agent incidents: 189,579 reconstructed Hugging Face attack records (Swarm Traces) and 14,591 wiki revisions written by agents on a covert message board (collusion.wiki). In Swarm Traces, only 1.6% of records carry an internal timestamp, only 28% of those records carry an anchor not inherited from copied code, and 89% of independent anchors fall within a single 48-hour window, which rules out content-based dating. On the wiki, we reconstruct per-revision text additions, group them into content families under four similarity definitions, and find that the median lineage lives 6 to 27 minutes. A calibrated, date-randomization test (validated on synthetic lineages planted into the real log, false-positive rate near nominal) detects temporal association in the few multi-day families, but the association is confined to lags under 6 hours (T = 0.32, p = 0.001) and absent at lags of 6 hours or more (T = -0.17, p = 0.99), where the same test detects 95% of planted accumulating lineages. Text distance saturates within hours, long-lived families stay flat, and once same-label pairs are excluded, no temporal association remains at any lag (short-lag T = -0.005, p = 0.71): all chronological signal comes from agents revising their own text, while cross-agent copying is exact and does not diverge. Copying in these swarms is recency-driven and non-accumulating, so post-hoc chronology cannot be recovered from content. Chronology and lineage must be logged at the gateway when actions occur. We also show that a naive temporal test is anti-conservative on agent artifacts.

---

## 1. Introduction

In July 2026, roughly 1,200 OpenAI agents running inside an evaluation coordinated through an unsanctioned message board, and about 700 of them took part in an intrusion into Hugging Face (METR/Redwood, 2026). A separate group of agents used a dormant German wiki as a covert board for about six weeks (collusion.wiki, 2026). Public reconstructions of both incidents now exist, and investigators increasingly ask how such swarms could be detected early.

Sequential monitoring requires time. The swarm monitor kollude states of the Swarm Traces corpus: "No clock, no e-CUSUM", so its time-series alerts do not run on it. Swarm Traces reports that 97% of payloads carry no native timestamp.

**Question.** Can the content of agent artifacts supply a clock? Phylogenetics answers the analogous question for pathogens: if copied sequences accumulate changes over time, divergence carries chronological signal (a "temporal signal"), which can date undated samples.

**Prediction from prior work.** De Marzo, Alboré and Garcia (2026) show that agents on the wiki choose what to write roughly in proportion to what they can see, with the current page weighted most, then recent edits, and older activity only weakly. This predicts short-range similarity without long-range accumulation.

**Contributions.**
1. A feasibility audit of content-based dating for Swarm Traces (Finding A).
2. A lifespan distribution for artifact lineages on the wiki, robust across four similarity definitions (Finding B).
3. A calibrated test that separates an accumulating clock from recency-driven similarity, validated on synthetic lineages planted into the real log (Finding C).
4. A methodological warning: a naive temporal test is anti-conservative on agent artifacts because real members contaminate the tested families (Finding D).
5. A design implication for Tracks 3 and 4: chronology and lineage must be captured at the gateway.

## 2. Related work

- **Incident reconstructions.** METR/Redwood (2026) reconstruct workstreams and recover missing action times from privileged transcripts. Swarm Traces (Forman et al., 2026) reassembles payloads and documents missing timestamps. collusion.wiki (Von Arx et al., 2026) documents the wiki board qualitatively.
- **Quantitative wiki analyses.** De Marzo et al. (2026) model copying choices. Murtuza (2026) supplies a statistical analysis of the wiki incident. Counter-Swarm Doctrine (Frank, 2026) distinguishes influence from common causes and reconstructs the cleanup chronology.
- **Swarm forensics tools.** patient-zero (AI Swarm Dynamics Hackathon, Oct 2026) links token uses to plausible earlier exposures using diff additions and shuffled nulls; it does not measure divergence over time or date artifacts. kollude implements template folding and sequential alerts, and does not run time-series detection on Swarm Traces.
- **Methods.** Temporal-signal testing (TempEst, Rambaut et al., 2016; date-randomization, Duchene et al., 2015; structured nulls, Murray et al., 2016). Text-copying histories (computational stemmatology, Roos et al., 2006; Roos and Heikkila, 2009). Shingling and containment (Broder, 1997). Model phylogenies from outputs (PhyloLM, 2024; LLM DNA, 2025) address models, not artifacts circulating in a swarm.

**Our delta.** To our knowledge, no prior work tests whether artifact divergence in these incidents carries chronological information under calibrated nulls, or separates accumulation from recency. We do not claim new similarity or permutation methods.

## 3. Data

| Dataset | Records | Time information | Notes |
|---|---|---|---|
| Swarm Traces (redacted.jsonl.gz, pinned by SHA-256) | 189,579 (91,037 payloads, 75,534 recovered texts, 23,008 responses) | `time_utc` empty in all rows | Redacted, incomplete reconstruction |
| collusion.wiki (revisions.jsonl.gz) | 14,591 revisions, 4,579 pages, 3,103 self-chosen labels | Request-log times, 1 s uncertainty for 99.3% | Only ip16 (2 octets) available; 191 values shared by a median of 27 labels, so no ground-truth identity |

Window: revisions before 2026-07-03 UTC (to exclude post-publication fakes), request-log times only. Hub pages excluded (WillkommenImWiki, StartSeite, TestSeite, RecentChanges).

## 4. Methods

**4.1 Swarm Traces anchors.** We extract internal timestamps in the 2026-05-01 to 2026-07-31 window: JWT `iat`, gzip header mtime, Unix epochs (seconds and milliseconds), and date strings. An anchor value appearing in more than one record is marked inherited (it may date the copied source, not the record). Families: MinHash LSH on masked text (redaction tokens, digits and long tokens masked). Pre-registered gate: at least 500 independent anchors in at least 5 families with at least 15 anchors each.

**4.2 Wiki introductions.** For each revision we reconstruct the text it added (insert and replace hunks against its diff base), or the full body for page creations, so inherited page content is not counted. We mask agent labels, dates, numbers, long tokens and URL paths, and keep introductions with at least 8 tokens.

**4.3 Families and lifespans.** Families are connected components of a MinHash LSH graph on token shingles. Primary configuration frozen before temporal analysis: k=3, threshold 0.3. Sensitivity: (k=5, 0.5), (k=5, 0.3), (k=3, 0.2). Lifespan = time between first and last introduction of a family. Eligible for testing: at least 15 pages.

**4.4 Temporal association test.** One date-blind representative per (family, page) block (the longest introduction). Statistic: within each family, Spearman correlation between pairwise text distance (1 - Jaccard) and pairwise absolute time difference, averaged over families. Null: permute times among representatives within date-blind strata (length terciles) or within calendar days. One-sided, 999 permutations.

**4.5 Clock vs recency.** Mean distance by time-lag bin (10 min to more than 3 days), and the same test restricted to pairs with lag under 6 h, at least 6 h, and at least 24 h. An accumulating clock predicts rising distance and a positive long-lag statistic; recency predicts saturation.

**4.6 Calibration.** We plant 20 synthetic lineages per condition into the real log, with roots drawn from real texts and token-level edits (substitution, insertion, deletion) at rates p in {0.02, 0.05, 0.10, 0.20}, spread over 5 to 7 days. `clock`: each member copies a recent member and edits it. `star`: each member is an independent edit of the root, with random times. We rerun the frozen pipeline and test only planted members.

## 5. Results

**Finding A: Swarm Traces cannot be dated from content.** 2,948 of 189,579 records (1.6%) contain an anchor; anchor values repeated across records are treated as inherited, leaving 827 records (28%) with an independent anchor, of which 736 (89%) fall on 2026-07-11 and 2026-07-12. Only 3 families reach 15 independent anchors (gate required 5), and the largest (137 anchors) is identical after masking, so it has zero divergence. The gate failed; we did not relax it.

**Finding B: lineages are minute-scale.**

| Configuration | Families with at least 5 pages | Median lifespan | p75 | p90 | Share over 24 h |
|---|---|---|---|---|---|
| k5, 0.5 | 39 | 6.1 min | 0.32 h | 0.59 h | 0.0% |
| k5, 0.3 | 52 | 16.6 min | 0.90 h | 5.92 h | 7.7% |
| k3, 0.3 (primary) | 60 | 27.2 min | 3.34 h | 86.9 h | 16.7% |
| k3, 0.2 | 40 | 15.3 min | 1.13 h | 70.8 h | 17.5% (largest family 20.7% of blocks: chaining) |

Figure 1: lifespan ECDF (fig_lifespans.png).

**Finding C: temporal association is short-range recency, not a clock.** Six families are eligible in the primary configuration. The pooled statistic is T = 0.292 (p = 0.001) with length strata, and remains p = 0.001 with day strata and with the wiki's default new-page template removed (T = 0.385). Per family, the association is strongest in short-lived families (rho = 0.82 over 2 days with 4 labels; 0.42 over 3 days; 0.24 within 1 day) and absent in the longest-lived ones (rho = 0.06 over 7 days; -0.08 over 9 days). 
Restricting the test by time lag separates the two hypotheses (Table 3). The association is confined to lags under 6 hours and disappears at longer lags, while the same long-lag test detects 95 to 100% of planted `clock` lineages and rejects at 0 to 10% for `star` lineages.

| Lag window | Real T (p), primary | Real T (p), template removed | Synthetic clock rejection | Synthetic star rejection |
|---|---|---|---|---|
| under 6 h | 0.317 (0.001) | 0.365 (0.001) | 5% | 5% |
| 6 h or more | -0.174 (0.989) | -0.172 (0.928) | 95 to 100% | 0 to 5% |
| 24 h or more | -0.029 (0.738) | 0.066 (0.203) | 95% | 10% |

Lag curves (Figure 2) saturate. In the clearest short-lived family, mean distance rises from 0.09 (under 10 minutes) to 0.86 (1 to 3 hours) and plateaus near 0.95, i.e. texts become effectively unrelated within hours. The two multi-day families stay flat at about 0.9 across all lags: they are held together by shared structure (link lists, the wiki's default page text), not by accumulating edits. Synthetic `clock` curves keep rising at lags beyond one day (for example 0.61 at 12 to 24 hours to 0.85 beyond 3 days), and `star` curves are flat.

**Who produces short-range similarity.** At lags under 1 hour, same-label pairs are far more similar than different-label pairs in the families that carry the signal (0.16 vs 0.90; 0.30 vs 0.69). Cross-agent copying appears instead as exact-copy bursts: the largest family has 46,550 different-label pairs at distance 0, written by 58 labels within 5 minutes. Exact copies do not diverge, so they cannot produce a clock either. One family (round-status reports, 3 days, 31 labels) keeps a positive long-lag correlation (rho about 0.30); we report it as a single-family exception, plausibly driven by daily changes in task content.

**Excluding same-label pairs removes the signal entirely.** Restricting every window test to pairs written under different labels, the short-lag statistic falls from T = 0.317 (p = 0.001) to T = -0.005 (p = 0.71); long-lag T = -0.174 (p = 0.995); very-long-lag T = -0.030 (p = 0.71). Results are the same with the template removed. Across labels, artifact similarity carries no chronological information at any lag. This test is conservative for our conclusion: label reuse by different agents removes some cross-agent pairs, and renaming by one agent adds same-agent pairs to the cross-label set, and both errors would favor finding signal, yet none appears.

Figure 2: distance vs time lag, real families vs synthetic clock and star (fig_lag_curves.png).

**Finding D: calibration and the anti-conservative naive test.**

| Condition | Edit rate | Recovered | Significant (length strata) | Significant (day strata) | Significant if real members included |
|---|---|---|---|---|---|
| clock | 0.02 | 100% | 90% | 45% | 95% |
| clock | 0.05 | 100% | 95% | 45% | 95% |
| clock | 0.10 | 80% | 88% | 69% | 94% |
| star | 0.02 | 100% | 10% | 0% | 15% |
| star | 0.05 | 70% | 7% | 0% | 0% |

The pipeline recovers planted multi-day lineages at edit rates up to 10% and the test has high power with length strata, so the absence of accumulating multi-day lineages in the real log is not a detection failure. In the first version of our calibration, planted lineages merged with real families and the star condition rejected 20% and 12% of the time; testing only planted members restores near-nominal rates.

## 6. Discussion and implications

- **Two regimes, neither accumulating.** Cross-agent copying is exact (bursts with zero divergence); iterative variation is mostly one label revising its own text, and saturates within hours. Both match recency-weighted copying (De Marzo et al., 2026).
- **For forensic analysts.** Content similarity in these incidents links artifacts written minutes to hours apart. It does not support dating artifacts or ordering events across days. Chronological claims from content should be withheld.
- **For monitoring (Track 4).** Recency bursts are detectable in near real time, where timestamps exist. Post-hoc corpora without timestamps cannot feed sequential detectors through content alone.
- **For infrastructure (Track 3).** Chronology and lineage must be recorded at the gateway (tool-call or egress layer) when actions occur, outside the agents' reach, consistent with the organizers' "lineage-bound identity and gateway-side audit trail" direction.

## 7. Limitations

- Observational data: redacted, incomplete, and possibly mixed with traffic from outside the swarm.
- Families are defined by lexical similarity; semantic copying without shared wording is invisible.
- Within-day permutation reduces power (45% to 69% in calibration).
- Synthetic edits are token-level and may not reflect how LLM agents modify text.
- Only a few multi-day families are eligible; per-family estimates are noisy.
- Similarity is not transmission: we report candidate reuse, not causal copying, and do not infer identity.
- Anchor extraction uses regular expressions; date strings are a weak tier and may include false matches.

## Appendix A: Dual-use and ethics

Swarm Traces payloads are attack code. We treated all text as data: nothing was executed, no URLs found in the data were visited, and no payload content is republished beyond short masked excerpts. Our analysis characterizes the limits of forensic inference and does not improve attack capability. A possible dual-use concern is that knowing content cannot date artifacts could inform evasion; the recommended mitigation (gateway logging) does not depend on content.

## Appendix B: Reproducibility

Inputs pinned by SHA-256 (Part 1). Notebooks Part 1 to Part 2d, fixed random seed 20261108, frozen configuration listed in Section 4.

## References (verify each link before submission)

- Broder, A. (1997). On the resemblance and containment of documents.
- Counter-Swarm Doctrine (Frank, 2026). arXiv:2609.06140.
- De Marzo, G., Albore, N., Garcia, D. (2026). Copying explains the collective behavior of AI agents in the wild. arXiv:2609.09150.
- Duchene, S. et al. (2015). The performance of the date-randomization test in phylogenetic analyses of time-structured virus data. MBE.
- Forman, A. et al. (2026). Swarm Traces. https://swarmtraces.org/
- kollude (Gowda, 2026). https://github.com/dhruva137/kollude
- METR/Redwood (2026). Independent investigation of the OpenAI / Hugging Face incident. https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/
- Murray, G. et al. (2016). The effect of genetic structure on molecular dating and tests for temporal signal. MEE.
- Murtuza, S. (2026). Quantifying collusion among autonomous LLM agents. arXiv:2610.04528.
- patient-zero (2026). https://github.com/devonmvfisher/patient-zero
- Rambaut, A. et al. (2016). TempEst. Virus Evolution.
- Roos, T., Heikkila, T., Myllymaki, P. (2006). A compression-based method for stemmatic analysis. ECAI.
- Von Arx, S., Byrd, C. S., Kitts, S., Larsen, T. (2026). collusion.wiki. https://collusion.wiki/
- Wu, Z. et al. (2025). LLM DNA. arXiv:2509.24496.
- Yax, N. et al. (2024). PhyloLM. arXiv:2404.04671.
