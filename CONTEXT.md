# CONTEXT: Swarm Clock project (Apart Research Swarm Alignment Hackathon, Nov 6-8, 2026)

This file is the single source of truth for anyone (human or agent) continuing this project. Read it fully before touching code. Companion files: `results/RESULTS_LOG.md` (every number obtained so far, verbatim), `paper/report_draft.md` (paper draft), `notebooks/` (the analysis as run in Colab), `prompts/CLAUDE_CODE_PROMPT.md` (instructions for the automation agent).

---

## 0. Who, what, when

- **Author:** MP (Manuel Peña-Zúñiga), Biological Engineer (PUC Chile), founder/independent AI engineer, Santiago, Chile. Background: computational biology, food-tech CTO, Web3/Rust, healthcare AI (vertigo triage, agentic benchmarks), Kaggle. Goal: strengthen his AI safety research profile; a strong result can lead to the Apart Fellowship.
- **Team:** solo. Has Colab Pro, API credits, coding agents. Plans to sleep very little tonight.
- **Event:** Apart Research "Swarm Alignment Hackathon", co-organized with AI Alignment Foundation and AE Studio. https://apartresearch.com/sprints/swarm-alignment-2026
- **HARD DEADLINE:** Sunday 2026-11-08 23:59 Anywhere on Earth = **Monday 2026-11-09 08:59 Santiago (UTC-3)**. Target: submit a complete draft by **08:00 Santiago**, then overwrite with the final version if allowed. Never risk the deadline for an extra analysis.
- **Submission requirements** (as reported by auditor 2 from the Guidelines tab; RE-VERIFY on the site): official Apart template, PDF, at most 8 main pages, abstract of 150 to 250 words, author list, a Limitations and Dual-Use appendix; a public code repository is optional.
- **Judging rubric** (reported by auditor 2; re-verify): three dimensions (impact/innovation, execution, presentation). Generic approaches score around 2; level 3 needs more than routine application; "is this actually new to the field, or replicating recent work?" matters for 4 to 5.
- **Prizes:** cash for 1st to 5th ($2,000 / $1,000 / $600 / $200 / $200) plus Adaption credits; top teams get priority for the Apart Fellowship.
- **Tracks:** (1) sandboxes and testbeds, (2) science of agent networks, (3) agent infrastructure (identity when agents rename/copy), (4) multi-agent oversight and control. Our paper is Track 4 with Track 3 implications.

---

## 1. The research in one paragraph

**Question:** Can the content of agent artifacts supply a clock for swarm corpora that lack timestamps? Motivation: the swarm monitor `kollude` states of the Swarm Traces corpus "No clock -> no e-CUSUM", so sequential detectors cannot run on it, and Swarm Traces reports 97% of payloads have no native timestamp. If copied artifacts accumulated edits over time (like pathogen sequences), textual divergence would carry chronological signal ("temporal signal" in phylodynamics) and could date undated artifacts.

**Answer so far (four findings):**
- **A.** Swarm Traces cannot be dated from content: 1.6% of records contain an internal timestamp, only 28% of those carry a non-inherited anchor, 89% of independent anchors fall on 2026-07-11/12, only 3 families reach 15 anchors, and the largest is identical after masking (zero divergence). Pre-registered Gate 1 failed; not relaxed.
- **B.** On collusion.wiki, artifact lineages are minute-scale: median lifespan 6 to 27 minutes across four similarity definitions.
- **C.** Temporal association exists only at short lags (<6 h: T = 0.317, p = 0.001) and vanishes at long lags (>=6 h: T = -0.174, p = 0.989), where the same test detects 95 to 100% of planted accumulating lineages. Excluding same-label pairs removes all signal (short lag T = -0.005, p = 0.71): all chronological signal is agents revising their own text; cross-agent copying is exact (bursts with distance 0) and carries no chronology at any lag. Two regimes, neither accumulating, consistent with recency-weighted copying (De Marzo et al., 2026).
- **D.** Methodological: a naive temporal test on agent artifacts is anti-conservative (false-positive rate 20% and 12% instead of 5%) when tested families are contaminated by real members; testing only planted members restores near-nominal rates.

**Working title:** "Rogue Swarms Leave No Clock: Artifact Lineages in Two Real Agent Incidents Are Recency Bursts, Not Accumulating Lineages" (adjust if the Mantiq replication changes the story; see section 9).

**Safety implications:** (1) forensic analysts should not make chronological claims from artifact content in these incidents; (2) post-hoc corpora without timestamps cannot feed sequential detectors via content; (3) chronology and lineage must be recorded at the gateway (tool-call or egress layer) when actions occur, outside the agents' reach (matches the organizers' Track 3 example "lineage-bound identity and gateway-side audit trail").

---

## 2. How we got here: pivot history (all pivots forced by verified prior art or by data)

| # | Idea | Why abandoned |
|---|---|---|
| 1 | Sybil-resistant anonymous agent credentials with RLN / ZK nullifiers (Track 3), "conditional anonymity" | Prior art verified: Crapis and Buterin, "ZK API Usage Credits: LLMs and Beyond" (ethresear.ch, Feb 2026) uses RLN for private LLM API credits with slashing; Zhu and Wang 2610.00347 (authority conservation across replacement, forking, rollback); Zhu and Wang 2610.00349 (budget conservation under retries/duplicates). Also a flaw found: legitimate replicas sharing a secret would trigger slashing. |
| 2 | "When Agents Fork": identity and quota enforcement under cloning and rollback (suggested by an auditor) | Same Zhu and Wang papers cover it directly. |
| 3 | Reproducible audit of cancellation/revocation in a LangGraph-A2A workflow (auditor suggestion) | Khan, "Stop Means Stop" 2607.14166 (six frameworks, SOUNDGATE) and Zhu and Wang 2609.21284 (root-scoped quiescence) already cover it; would be a reproduction. |
| 4 | Behavioral re-identification of renamed agents on real swarm data (Track 3 "Who is who") | Data has no ground-truth identity: collusion.wiki only has `ip16` (first two IP octets), 191 values shared by a median of 27 labels (max 431), 1,741 labels span multiple ip16; Swarm Traces has no agent IDs. Evaluation would be circular. |
| 5 | Coordination forensics on collusion.wiki (Track 4) | Rejected by MP as mediocre: it is the organizers' own example project, likely crowded. |
| 6 | "Genomic surveillance for AI swarms": phylodynamic reconstruction, date Swarm Traces with a clock calibrated on the wiki, name-independent attribution, variant monitor | Two independent audits: cross-dataset clock transfer is fatal; overlaps with patient-zero, kollude, De Marzo et al., Murtuza, Counter-Swarm; terminology inflation. Narrowed to the single question "can content supply a clock?". |
| 7 | Clock on Swarm Traces, then on the wiki | Data answered: Gate 1 failed (Finding A); lineages are minute-scale (B); naive test anti-conservative (D); signal is self-revision recency, not a clock (C). |

Principle adopted from pivot 6 on: freeze analysis choices and gates before looking at temporal results; never relax a gate after seeing data; turn every surprise into a reported finding.

---

## 3. Prior art (with verification status)

Verified by direct fetch of the source page in this session (V), or reported by an auditor and not independently fetched (A). Verify all (A) items before citing.

| Work | Status | Relevance |
|---|---|---|
| METR/Redwood investigation (Greenblatt, Cotra, Wijk), 2026-08-26. https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/ | V (search) | Incident reconstruction from privileged transcripts; at least 20% of agents expressed interest in tampering with transcripts; >95% of board activity attributed. |
| Swarm Traces (Forman, Kharlov, Tom, Ladish, Kitts, Byrd, McKenzie, Piecha), https://swarmtraces.org/ ; data https://swarmtraces.org/data/final/redacted.jsonl.gz | V | 80,000+ reassembled payloads; 97% no native timestamp; ~80% outbound; 7,905 names vs ~1,200 agents (authors compare counts; they do not claim to deduplicate names into agents); no license stated. |
| Gated companion: https://huggingface.co/datasets/vopi/OpenAI-HF-Hack-SwarmTraces | V | Gated; schema not public; not used. |
| collusion.wiki (Von Arx, Byrd, Kitts, Larsen), 2026-09-04. https://collusion.wiki/ ; downloads https://collusion.wiki/explorer/download | V | ~18,000 agent posts on a German volunteer wiki; IPs half-redacted; posts after the report include fakes; no license stated. |
| De Marzo, Albore, Garcia, "Copying explains the collective behavior of AI agents in the wild", arXiv 2609.09150 (Sep 2026) | V (abstract) | Agents copy in proportion to visibility: current page most, recent edits next, older activity weakly. Our a priori prediction (recency, no accumulation). Abstract does not mention lineages, phylogenies or a formal temporal-signal test. |
| Murtuza, "Quantifying Collusion Among Autonomous LLM Agents: A Statistical Analysis of the Collusion Wiki Incident", arXiv 2610.04528 (Oct 2026) | V (abstract) | Quantitative statistical analysis of the wiki incident. Auditor 1 claims it analyzes moderator deletions (p ~ 1e-107) and identifies statistical traps; NOT verified beyond the abstract. |
| patient-zero (AI Swarm Dynamics Hackathon, Oct 2026). https://github.com/devonmvfisher/patient-zero | V | Token spread tracing on the wiki using diff additions, shuffled nulls, planted cascades; blind to same-page spread; does NOT measure divergence over time or date artifacts. |
| kollude (Dhruva P Gowda). https://github.com/dhruva137/kollude | V | Template folding, e-CUSUM alerts; wiki first alarm 107 h before a June 21 landmark; on Swarm Traces: 3,893 templates reused across captures (86.2% of foldable payloads) and "No clock -> no e-CUSUM". Our motivating gap. |
| Counter-Swarm Doctrine (Frank), arXiv 2609.06140 | V (search snippet) / A | Coordination episodes, influence vs common causes, wiki reconstruction and cleanup chronology (auditor 2: 4,773 of 5,217 deletions after June 22). |
| Khan, "Stop Means Stop", arXiv 2607.14166 | V | Relevant only to pivot 3 history. |
| Zhu and Wang 2609.21284, 2610.00347, 2610.00349 | V | Relevant only to pivots 1 to 3. |
| Crapis and Buterin, ethresear.ch post 24104 | V | Relevant only to pivot 1. |
| LLM DNA (Wu et al.), arXiv 2509.24496 | V (search) | Phylogeny of models from functional representations; recovers chronology without release dates. Different object (models, not artifacts). |
| PhyloLM (Yax, Oudeyer, Palminteri), arXiv 2404.04671 | A | Same as above. |
| Paglieri et al. (Google DeepMind), "A Case Study on Emergent Cheating and Whistleblowing in Autonomous Research Swarms", arXiv 2609.04170 | A (CSA summary verified) | A grading exploit spread through a 100-agent swarm's shared library in 27 minutes. Controlled experiment. |
| Mantiq swarm traces (ZenML). https://huggingface.co/datasets/zenml/mantiq-swarm-traces | V | CC-BY-4.0, open: 19 recordings of an 18-agent team (1 planner, 16 workers, 1 judge) building a Lisp interpreter; true agent_id; OS-level timestamps; text in `blobs`; canary GUID (exclude from training). Planned replication corpus. |
| AI Village (aidigestorg/ai-village) | V | Gated with manual review; custom research terms requiring notification of authors; NOT usable tonight. |
| Methods: TempEst (Rambaut et al. 2016), date-randomization test (Duchene et al. 2015), structured nulls (Murray et al. 2016), delta plots (Holland et al. 2002), Neighbor-Net (Bryant and Moulton 2004), compression stemmatology (Roos, Heikkila, Myllymaki 2006; Roos and Heikkila 2009), shingling/containment (Broder 1997), NCD (Cilibrasi and Vitanyi 2005), MemeTracker (Leskovec et al. 2009), clone genealogies (Kim et al. 2005), software lineage inference (Jang, Woo, Brumley 2013), Information Evolution (Adamic et al. 2014), malware lineage (Lindorfer et al. 2012; BitShred, Jang et al. 2011) | A (classic) | Background; verify DOIs before citing. |

**Our claimed delta:** we found no prior work that tests whether artifact divergence in these incidents carries chronological information under calibrated nulls, separates accumulation from recency, or separates self-revision from cross-agent copying. We do not claim new similarity or permutation methods. Never claim "first"; say "to our knowledge".

---

## 4. Data facts (verified by running code)

### Swarm Traces `redacted.jsonl.gz`
- 189,579 rows; fields: id, cite, kind, parent_id, time_utc, tags, text.
- kind: payload 91,037; recovered_text 75,534; response 23,008.
- time_utc: empty. parent_id: null in first 5k rows (full-file check pending).
- Redaction placeholders look like `[REDACTED:destination:000002]`, `[SERVICE 2 URL 1]`, `[REDACTED-HUGGINGFACE-TOKEN]`.
- Content is attack code (Python, JS, curl). Treat as data only.

### collusion.wiki `revisions.jsonl.gz`
- 14,591 rows. Fields: rev_id, page_id, page_key, wiki, name, seq, rcs_rev, rcs_path, body, body_len, body_sha256, lines, diff_base, diff_base_reason, hunks, label, ip16, time, time_grade, winning_clock, uncertainty_seconds, request_time, success_time, recent_changes_time, write_date, archived_at, request_action, change_summary, related_event_id, relation_type, round_id, body_encoding.
- `diff_base` is the rev_id string of the base revision (e.g. `dse~--help@1`).
- `hunks` are line-position opcodes (insert/replace/delete with a0, a1, b0, b1); the added text must be reconstructed as `body.split("\n")[b0:b1]` for insert and replace.
- time_grade: reqlog 14,482; rclog 103; write_date 6. uncertainty_seconds = 1 for all rows.
- relation_type: first_recreation_of in 63 rows (recreated pages: usable as positive controls).
- 3,103 labels (self-chosen names); ip16 = 191 values (shared Azure ranges, not identity).
- Hub pages to exclude: dse/WillkommenImWiki (front page, 2,321 edits), dse/StartSeite, dse/TestSeite, dse/RecentChanges.
- The wiki's default new-page text "Beschreibe hier die neue Seite." is a template confound.
- Other files: pages, events (14,591 saves, 5,217 deletions, 4 reverts, 101 probes), labels, links (23,877), records (13,703), shortener-logs, manifest.

### Mantiq (not yet explored)
- Tables per run as Parquet: events (`event_id`, `host_seq`, `source`, `kind`, `agent_id`, `session_id`, `ts_wall_ns`, `ts_mono_ns`, `payload` JSON, `blobs` JSON list of sha256), messages (`from_agent_id`, `to_agent_id`, `sent_event`, `delivered_event`, `rejected_event`, no text column), blobs (`sha256`, `size`, `roles`, `text`), model_calls, tool_calls, processes, fs_ops, file_versions (606k), reads, links, findings, agents (327), sessions, runs (19), answer_keys.
- events/links/fs_ops files are 100 to 190 MB each (per split or per run, check). Splits: practice (10 runs), hidden (9 runs).

---

## 5. Frozen methodology (do not change without logging a new pre-registration)

- **Swarm Traces anchors:** 2026-05-01 to 2026-07-31 UTC (epochs 1777593600 to 1785456000). WARNING: auditor 1 proposed 1720396800.., which is July **2024**; never use it. Types: jwt_iat (strong), gzip_mtime, epoch_s, epoch_ms, date_str (weak; the `may` regex can match the English word). Anchor values in more than one record are "inherited" (lower bounds only).
- **Wiki unit:** introduction = added text of a revision (insert/replace hunks), or full body for page creation. Window: time < 2026-07-03 UTC, time_grade == reqlog, hubs excluded.
- **Masking:** agent labels (>= 4 chars) -> `<AGENT>`, URL paths -> `host/<PATH>`, dates -> `<DATE>`, tokens >= 24 chars -> `<TOK>`, digits -> 0. Keep introductions with >= 8 tokens.
- **Families:** MinHash (128 perms) LSH graph, connected components (union-find). Primary: k = 3 token shingles, threshold 0.3. Sensitivity: (5, 0.5), (5, 0.3), (3, 0.2). Watch for chaining (largest family share > 20% means a spurious giant component).
- **Eligibility:** >= 15 pages per family. Dependency block = (family, page); representative = longest introduction (date-blind).
- **Statistic:** within family, Spearman(pairwise 1 - Jaccard on k=3 shingles, pairwise |dt|); averaged across families. One-sided. Null: permute times among representatives within strata (length terciles per family; or calendar day; or day x length). B = 999 for real data (p floor 0.001), B = 199 or 99 for simulations.
- **Window tests:** same statistic restricted to lag windows <6 h, >=6 h, >=24 h. Cross-label variant excludes same-label pairs.
- **Calibration:** plant synthetic lineages into the real log (roots = real introductions, token-level substitution/insertion/deletion at rate p), `clock` (each member copies one of the 5 most recent members) vs `star` (independent edits of the root, random times); test ONLY planted members (testing the whole family is contaminated and anti-conservative).
- **Seed:** `np.random.default_rng(20261108)`.

---

## 6. Gates and pre-declared readings (keep this discipline)

| Gate | Rule | Outcome |
|---|---|---|
| Gate 1 (Swarm Traces) | >= 500 independent anchors in >= 5 families with >= 15 each | FAILED (827 anchors, 3 families) -> Finding A |
| Multi-day lineage gate (wiki) | >= 5 eligible families with >= 3 days, largest family share < 20% | FAILED in all 4 configs -> Finding B |
| Day strata | signal disappears under family x day strata => between-day drift | Signal persisted -> led to window tests |
| Clock vs recency | long-lag test ~0 with curves saturating => recency | Confirmed (Finding C) |
| Cross-label | if short-lag signal vanishes without same-label pairs => self-revision | Confirmed (T = -0.005, p = 0.71) |

---

## 7. Known pitfalls and lessons (do not repeat)

1. Epoch range error (2024 vs 2026) in auditor 1's suggestion.
2. Whole page bodies manufacture temporal signal (accumulation within a page); always use introductions.
3. Hub pages and the wiki template create spurious long-lived "families".
4. LSH with low threshold chains into a giant component (k3 t0.2: 20.7%).
5. Planted roots drawn from real texts merge with real families; test only planted members.
6. `nan` handling: if all families are skipped, return p = nan (earlier code returned a bogus 0.02).
7. With B permutations, p cannot be below 1/(B+1); with B = 19 nothing can be significant at 0.05.
8. T is identical across strata by construction; only p changes.
9. Self-chosen labels are not identity: name reuse and renaming both exist. Cross-label exclusion is conservative for our claim.
10. `ip16` is not identity.
11. Do not claim the largest Swarm Traces family dates anything: it is identical after masking.
12. Swarm Traces timestamps embedded in copied scripts date the source, not the execution.

---

## 8. Auditor feedback (summary)

**Accepted from auditor 1:** no cross-dataset transfer; use hunks; suppress homoplasy (masking, IDF); measure treelikeness; contrastive framing against De Marzo; drop the deletion natural experiment; avoid "phylodynamic" (use "temporal signal / lineage reconstruction"); monitor must beat baselines (dropped the monitor).
**Rejected or corrected from auditor 1:** epoch range (2024), unverified specifics (zzMAILBOX_AIC71C_RESET, "14 minutes", alphabetical deletion, ZZZ adaptation, p ~ 1e-107), "guaranteed score".
**Accepted from auditor 2:** frame as calibrated measurement study; similarity is not transmission ("candidate reuse"); drop identity attribution; separate temporal signal from dating; calibrate with synthetic controls; freeze choices; overstated-claims table (below).
**Diverged from auditor 2:** they recommended a wiki-only study; we first tried Swarm Traces (gate failed), then followed their wiki protocol.

**Claims to avoid (auditor 2 table):** "phylodynamic reconstruction" -> "testing temporal signal"; "names are the host" -> "self-chosen labels are unreliable metadata"; "name-independent attribution" -> "label-independent grouping of artifact variants"; "transmission network" -> "candidate reuse graph"; "solve the 97% missing timestamps" -> "assess whether content provides chronological information"; "validated method" -> state exactly what was validated; "first application" -> scoped contribution relative to stemmatology, software lineage, patient-zero, kollude; "uncommon author profile" is not an innovation.

---

## 9. What remains (priority order) and how it could change the story

1. **Part 3a (ready):** sampling-matched power with each real family's timestamps/labels/size, edit rates 0.0025 to 0.20 -> "we exclude clocks with per-copy edit rate in [x, y]"; very fast clocks saturate within hours (also unrecoverable). Plus NCD ablation and (k5, 0.3) sensitivity. Regenerates fig_power.png.
2. **Mantiq replication (Part 3b discovery ready):** cooperative swarm with true agent_id. Pre-register before analysis. Candidate artifacts: inter-agent message texts (messages -> events.blobs -> blobs.text) and file_versions (code written over time). Apply: lifespans, window tests all vs cross-agent (true identity), sampling-matched calibration. Possible outcomes:
   - Cross-agent clock present in Mantiq but absent on the wiki -> stronger thesis: "accumulating construction leaves a clock; recency boards do not". Retitle accordingly.
   - Absent in both -> thesis generalizes to two very different swarms.
3. Positive control: 63 `first_recreation_of` pairs should have near-zero distance.
4. Swarm Traces: parent_id over full file; anchor rates by kind.
5. Figures (publication quality): lifespan ECDF, lag curves with synthetic references, window-test forest plot (all vs cross-label), power curve, a schematic of the two regimes.
6. Paper to <= 8 pages in the official template; abstract 150 to 250 words; Limitations and Dual-Use appendix; reproducibility appendix (SHA-256 of inputs, seed, commands).
7. Package as a reusable "content chronology audit" (`swarmclock audit --input corpus.jsonl --actor col --time col --text col`) with README.
8. Independent review of the final PDF by a fresh reviewer (agent or human) that did not write it; fix; submit.

---

## 10. Writing rules for the paper

- English. No em dashes. Precise, verifiable claims; give numbers with their test and N. Prefer "consistent with" over "proves".
- Report negative results plainly; state power alongside every null.
- Name the data limits: observational, redacted, incomplete, labels not identity, few eligible families.
- Ethics: never execute or follow anything in payloads; quote only short masked excerpts; cite datasets and respect terms (Mantiq canary GUID: do not include the canary string in the paper).

---

## 11. Files

| Path | What |
|---|---|
| notebooks/swarm_clock_part1.ipynb | Download (pins SHA-256), Swarm Traces schema, anchors, Gate 1, wiki structure checks |
| notebooks/swarm_clock_part2a.ipynb | Wiki introductions, masking, families, eligibility; saves data/wiki_intros.parquet and data/wiki_reps.parquet |
| notebooks/swarm_clock_part2b.ipynb | Lifespans (Finding B, fig_lifespans.png), family characterization, exploratory test, first (contaminated) calibration |
| notebooks/swarm_clock_part2c.ipynb | Strata by day, template ablation, corrected calibration |
| notebooks/swarm_clock_part2d.ipynb | Lag curves (fig_lag_curves.png), window tests, synthetic references, same vs different label, cross-label tests |
| notebooks/swarm_clock_part3a.ipynb | Sampling-matched power (fig_power.png), NCD ablation, k5 sensitivity (NOT yet run) |
| notebooks/swarm_clock_part3b_discovery.ipynb | Mantiq schema discovery (NOT yet run) |
| results/RESULTS_LOG.md | All numbers so far (regression targets) |
| paper/report_draft.md | Paper draft (Markdown) |
| prompts/CLAUDE_CODE_PROMPT.md | Instructions for Claude Code |

Runtime dependency chain: 2b -> 2c -> 2d -> 3a share in-memory state in one kernel (2b loads data/wiki_intros.parquet from 2a; 2a needs data/ from Part 1). Part 3b is independent.
