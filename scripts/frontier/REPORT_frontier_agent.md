# Frontier report: a calendar, not a clock (2026-11-09, 00:08 to 00:30 Santiago)

Paths are relative to `scratchpad/frontier/` (scripts in `scripts/`, outputs in `out/`). The project was not modified.

## 1. Deductions and the frontier question

The paper shows two things: divergence within lineages does not grow with lag beyond 6 h (no clock), and near-duplicates are written within the hour (co-time). Two untested routes for text to still carry time remain:

- **(i) Local order:** content tells which of two near-duplicates came first.
- **(ii) Population calendar:** the swarm keeps introducing shared material (domains, page names, phrases) that persists. An artifact then cannot predate the first appearance of the newest material it contains; archaeologists call this a *terminus post quem* (TPQ). No clock is needed. This also separates "exogenous drift" from inheritance, because the signal sits at the population level, not inside lineages.

**Outcome: (ii) is real, preregistered and confirmed, and it is the frontier result. (i) is a clean preregistered negative.**

## 2. Verified literature (bibliographic details checked by web search; alphaXiv access was denied, full texts not read)

- Drummond et al. (2003). Measurably evolving populations. *TREE* 18:481-488, doi:10.1016/S0169-5347(03)00216-7. At day scales the swarm is not a measurably evolving population, yet it is datable.
- Shalizi & Thomas (2011). arXiv:1004.4704. Direction of influence is not identified from observational data. Our polarity test is a parametric handle, and it found nothing.
- Grozea & Popescu (2010). Who's the thief? *CICLing*, LNCS 6008:700-710, doi:10.1007/978-3-642-12116-6_59. Prior art for text-based direction.
- Gomez-Rodriguez, Leskovec & Krause (2010). arXiv:1006.0234 (NetInf). Infers diffusion from timestamps; we test the converse.
- Lee & Tiwari (2024). Prompt Infection, arXiv:2410.07283. The agent-to-agent relay whose signature line D looked for.
- Angelopoulos & Bates (2021). arXiv:2107.07511. Split-conformal intervals (line A).
- TPQ: a standard archaeological concept; no specific citation verified.

## 3. Tests and exact numbers

Each preregistration was hashed before its computation (`PREREG_FRONTIER*.sha256`, stamped 00:13:52, 00:18:37 and 00:24:18). **Disclosure:** the "Written" times inside two of the files were wrong estimates (00:21 and ~00:56); the hash stamps are authoritative. The files are not committed to git; commit them if used.

**T. TPQ dating (`PREREG_FRONTIER_T.md`; `scripts/t_tpq.py`; `out/t_tpq_*.csv`)**
- Anchors: wiki pages in crc32 quarters {0, 2}. Targets: quarter 1 (pilot) and quarter 3 (confirmation).
- Eligible anchors per target: another label, another page, and Jaccard < 0.3. The Jaccard rule excludes near-duplicates without using times.
- TPQ: the 90th percentile of the first-appearance times of the target's 3-shingles that occur in 2 to 50 eligible anchors (the pilot chose this variant from four).
- **Confirmation (71.1% of 1,918 targets covered):** true time within [TPQ − 1 h, TPQ + 24 h] for **0.678**, vs **0.228** with anchor times permuted (97.5th percentile 0.253; p = 0.005, the floor at B = 200). **T1 passes.** Pilot: 0.624 vs 0.197.
- Day-scale successes (1 to 24 h after the TPQ): 0.40 vs 0.18.
- Robustness (exploratory, `out/t_adv_*`, `out/t_explore.log`): excess over the null 0.31 to 0.45 in every variant:
  - burst and template removed: 0.669 vs 0.225
  - date and weekday features dropped: 0.683
  - same-family anchors excluded: 0.679
  - anchors whose label shares a 6-character prefix excluded: 0.642
  - all three together: 0.651 vs 0.224
  - outside the two busiest days: 0.554 vs 0.249
- Anchor density (exploratory):

  | Share of artifacts timestamped | Dated | Success | Null |
  |---|---|---|---|
  | 2% | 23% | 0.57 | 0.27 |
  | 5% | 45% | 0.61 | 0.24 |

- Nearest eligible anchor (Jaccard < 0.3; exploratory, `out/t_knn.log`): dates 86% of targets, |error| < 24 h for 0.795 vs 0.311 null; median |error| 1.7 h vs 44 h.

**A. Co-time dating with split-conformal 90% intervals (`out/a_anchor_dating.csv`)**
- Both predictions held: interval coverage in the held-out half 0.91 to 0.95; half-widths 0.008 to 1.2 h vs a 75 to 86 h baseline.
- Rarely applicable: at 1.6% anchors it dates 3.7% of artifacts (burst and template removed: **0.18%**, ±0.45 h).

**D. Direction (`PREREG_FRONTIER.md`; `scripts/d_direction.py`)**
- Pairs: cross-label, cross-page near-duplicates; split by similarity component.
- Confirmation, using the pilot-selected score: length-balanced pairs **0.469 [0.41, 0.53]**; all pairs 0.503. **Fails.**
- Pooled over both splits: rare-variant polarity 0.482 [0.42, 0.55] (563 pairs, 131 components); length 0.58 [0.50, 0.65].
- Power check (exploratory): planted relay clusters (copies of copies) give polarity 0.66 to 0.82; broadcast clusters (independent copies of one source) give 0.46 to 0.51.

**H. Held-out hub introductions (2,679, never analysed; `PREREG_FRONTIER_H.md`)**
- Polarity 0.505 [0.40, 0.61]. **H1 passes** (no relay-level polarity). The 0.66 bound came from simulations run after D.
- Length: 0.666 [0.56, 0.77].
- Exploratory: the largest component is one link list extended by 43 labels over 50 min. Length orders 96% of its pairs and polarity inverts, because new entries are copied forward.
- So order appears only through accretion.

**S. Time-information spectrum (exploratory, `out/s_spectrum.csv`)**
- Within families, local-octave AUC stays inside the null band up to about 1.4 days, against 0.55 to 0.68 for planted clocks. Noisy.

## 4. Ready to add: the TPQ calendar

**Preregistration (verbatim core of `PREREG_FRONTIER_T.md`, SHA-256 aa6f9b57…2bce1):**

> "eligible anchors: different label, different page, and Jaccard(x, a) < 0.3 […] TPQ_x = stat over x's features of first(s | x). […] Success: t_x in [TPQ_x - 1 h, TPQ_x + 24 h]. Null: anchor times permuted among anchors (B = 200) […]. T1 (primary, confirmation targets): success_real > 97.5th percentile of the null AND success_real - mean(null) >= 0.10."

**Claim:** the text agents add has no divergence clock, but it carries a population calendar. The first appearances of the material an artifact shares with timestamped, non-near-duplicate artifacts by other labels bound its date to within a day for most covered artifacts.

**Results paragraph:**

> In a preregistered split (anchors: half the wiki pages; pilot and confirmation targets: the remaining quarters), we bounded each introduction's date by the first appearance of the 3-shingles it shares with timestamped introductions under other labels on other pages. Near-duplicates (Jaccard ≥ 0.3) were excluded without using times. On confirmation targets (71% covered), the true time fell within [−1 h, +24 h] of the bound for 67.8% of introductions, versus 22.8% with permuted anchor times (97.5th percentile 25.3%). Day-scale successes (1 to 24 h) were 40% vs 18%. The excess persisted with burst and template text removed, date-like features dropped, same-family and same-label-prefix anchors excluded, and outside the two busiest days (exploratory; 0.31 to 0.45). With 2% of artifacts timestamped, 23% of the rest were bounded (57% vs 27% null). This separates population-level novelty from within-lineage divergence. It does not distinguish persistent accretion from changes in daily topic, and it rests on one corpus with randomly placed anchors.

**Abstract sentence:**

> Text nonetheless carries a calendar: in a preregistered held-out test, the first appearance of material an introduction shares with timestamped, non-near-duplicate artifacts placed 68% of covered introductions within a day of their true time (23% under permuted times).

**Consequence for the paper:** "does not date them" and the title's "not a clock" framing should become "no clock, but a calendar given sparse anchors". Clocks also need dated tips, so this is the fair comparison.

## 5. Go / no-go

| Line | Decision | Note |
|---|---|---|
| **T** | **GO** | New Section 5.x, abstract sentence, revised take-away. State the day-scale share, since same-day timing overlaps with recency. |
| **A** | **GO**, one sentence | Precise but rare: 0.18% of non-burst artifacts vs TPQ's 23% at about 2% anchors. |
| **D/H** | **GO** as a preregistered negative | No order beyond length; no relay signature; order appears only via accretion. |
| **S** | NO-GO | Not crisp. |
| Drift vs inheritance per family | Unresolved | T answers it at corpus level. |
