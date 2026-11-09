"""Restructure paper/report.md into the Apart template section order and render paper/report_apart.docx with the template's styles."""
import re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
s = (ROOT / "paper/report.md").read_text()
def sec(start, end=None):
    i = s.index(start); j = s.index(end, i + len(start)) if end else len(s)
    return s[i + len(start):j].strip("\n")
title = s.splitlines()[0].lstrip("# ").strip()
abstract = sec("## Abstract\n", "\n---")
take = sec("**Take-away.**", "![Figure 1]").strip()
fig1 = s[s.index("![Figure 1]"):s.index("## 1. Introduction")].strip()
intro = sec("## 1. Introduction", "## 2. Related work")
related = sec("## 2. Related work", "## 3. Data and feasibility")
data = sec("## 3. Data and feasibility", "## 4. Methods")
methods = sec("## 4. Methods", "## 5. Results")
results = sec("## 5. Results", "## 6. Discussion and implications")
disc = sec("## 6. Discussion and implications", "## 7. Limitations")
limits = sec("## 7. Limitations", "## Appendix A")
appA = sec("## Appendix A: Limitations and Dual-Use / Ethical Considerations", "## Appendix B")
appB = sec("## Appendix B: Reproducibility", "## Appendix C")
appC = sec("## Appendix C: Secondary results", "## References")
refs = sec("## References")
intro = intro.replace("**What is new.**", "**Our main contributions are:**")
results = re.sub(r"^### 5\.(\d)", r"### 4.\1", results, flags=re.M)
def fixrefs(t):
    t = re.sub(r"Section 5\.(\d)", r"Section 4.\1", t)
    t = t.replace("Section 7", "Section 5 (Limitations)").replace("(Section 5.7)", "(Section 4.7)")
    return t
future = """- Test the clock and calendar on further agent corpora with real, rather than simulated, timestamp availability, and on longer-running cooperative swarms.
- Replace token-edit simulations with clocks produced by language-model rewriting, and test clocks confined to single families with pre-specified per-family designs.
- Turn co-time and the calendar into an imputation tool with calibrated, dependence-aware error bars, and evaluate whether imputed day bins help sequential detectors.
- Prototype the gateway-side log (time, actor, content hash) and measure what it recovers that content cannot."""
conclusion = ("We asked whether the text an agent swarm writes can tell time. In the one corpus we could test, the text agents pass on shows no "
"detected pooled divergence clock, even though the same test finds a strong clock in documents that grow and end-to-end simulations would usually "
"have caught one; clocks confined to single families remain insufficiently constrained. Text nonetheless carries two weaker kinds of time: near-duplicates "
"mark co-time, and first appearances of shared material give a coarse, empirical day-scale calendar when many artifacts are timestamped. For oversight, "
"content can synchronize and coarsely date events after the fact, but chronology and lineage should be recorded at the gateway when actions occur.")
code = """- **Code repository**: https://github.com/manuelpenazuniga/swarm-clock (pipeline, `swarmclock audit` tool, pre-registrations, decision log, output tables and figures).
- **Data/Datasets**: Swarm Traces (https://swarmtraces.org/), collusion.wiki (https://collusion.wiki/explorer/download), Mantiq swarm traces (https://huggingface.co/datasets/zenml/mantiq-swarm-traces, CC-BY-4.0). Input SHA-256 hashes are listed in Appendix B. Swarm Traces payloads are attack code and are processed as inert text only.
- **Other artifacts**: interim PDF and DOCX renderings, independent audit reports (`outputs/REVIEW.md`)."""
contrib = "Manuel Peña-Zúñiga conceived the question, designed and ran all analyses, and wrote the report (solo project)."
llm = ("We used Claude (Anthropic) through Claude Code to refactor the analysis notebooks into a pipeline, run and extend the analyses, draft and revise "
"the text and figures, and run independent sub-agent reviews; GPT-6 Astra (via Codex) and Gemini 4 Argon (via agy) were used as independent auditors. "
"Some extension designs (the co-time split-half test and the calendar test) were proposed and piloted by AI agents and pre-registered before computation, "
"as disclosed in the decision log. All numbers in this report are produced by the released code and read from its output tables; the main results were "
"re-run and reproduced, and every reference was checked against its source. The author is responsible for all content.")
out = f"""# {title}

Manuel Peña-Zúñiga  
Independent researcher, Santiago, Chile

**With Apart Research**

**Abstract**

{abstract}

## 1. Introduction

**Take-away.** {take}

{fig1}

{intro}

## 2. Related Work

{related}

## 3. Methods

### 3.1 Data and feasibility

{data}

### 3.2 Analysis

{methods}

## 4. Results

{results}

## 5. Discussion and Limitations

{disc}

### Limitations

{limits}

### Future Work

{future}

## 6. Conclusion

{conclusion}

## Code and Data

{code}

## Author Contributions

{contrib}

## References

{refs}

## Appendix

### A. Limitations and Dual-Use / Ethical Considerations

{appA}

### B. Reproducibility

{appB}

### C. Secondary results

{appC}

## LLM Usage Statement

{llm}
"""
out = fixrefs(out)
(ROOT / "paper/report_apart.md").write_text(out)
print("wrote paper/report_apart.md", len(out.split()), "words")

# ---- condense main text to fit 8 pages in the template's styling: move detail to Appendix D (no content removed)
s2 = (ROOT / "paper/report_apart.md").read_text()
moved = []
def move_par(start_marker, label, keep=None):
    global s2
    i = s2.index(start_marker); j = s2.find("\n\n", i); j = len(s2) if j < 0 else j
    par = s2[i:j]; moved.append((label, par))
    s2 = s2[:i] + (keep or "") + s2[j:]
move_par("**One-family clocks, other edit models, other family definitions**", "D.1 One-family clocks, edit models and family definitions",
         "Detailed sensitivity analyses (one-family clocks, phrase-block edits, nine family definitions) are in Appendix D.1: no pooled clock is present, but a long-lag association confined to one or two families cannot be excluded.")
move_par("**What the model saw (exploratory, pre-registered).**", "D.2 Model-context exposure in Mantiq",
         "Model-context exposure analyses (Appendix D.2) show that large overlaps are more frequent for sources the model had seen, but similarity does not track exposure in general.")
fi = s2.index("![Figure 2]"); fj = s2.index("\n\n", s2.index("*Figure 2.", fi)); moved.append(("D.3 Figure 2", s2[fi:fj])); s2 = s2[:fi] + s2[fj:]
mi = s2.index("### 4.7 Pre-registered replication on a cooperative swarm (Mantiq)"); mj = s2.index("### 4.8", mi)
moved.append(("D.4 Mantiq pre-registered replication", s2[mi:mj].split("\n", 1)[1].strip()))
s2 = s2[:mi] + "### 4.7 Pre-registered replication on a cooperative swarm (Mantiq)\n\nBoth pre-registered units passed eligibility, but the decisive cross-agent long-window tests were undefined and power was below 80%, so by the pre-registered rule Mantiq is inconclusive about a clock; details in Appendix D.4.\n\n" + s2[mj:]
ti = s2.index("### 4.8 The deliverable: `swarmclock audit`"); tj = s2.index("## 5. Discussion and Limitations", ti)
moved.append(("D.5 The audit tool", s2[ti:tj].split("\n", 1)[1].strip()))
s2 = s2[:ti] + "### 4.8 The deliverable: `swarmclock audit`\n\n`swarmclock audit --input corpus.jsonl --actor agent --time ts --text body` runs the calibrated clock test on any corpus and reproduces our wiki statistics without wiki-specific code (Appendix D.5).\n\n" + s2[tj:]
s2 = s2.replace("(Figure 2a)", "(Appendix Figure 2a)")
app = "\n\n### D. Detail moved from the main text\n\n" + "\n\n".join(f"**{lab}.**\n\n{par}" for lab, par in moved) + "\n"
k = s2.index("## LLM Usage Statement")
s2 = s2[:k] + app.lstrip("\n") + "\n" + s2[k:]
(ROOT / "paper/report_apart.md").write_text(s2)
print("condensed; main words:", len(s2[s2.index('## 1. Introduction'):s2.index('## References')].split()))

# ---- second condensation pass
s3 = (ROOT / "paper/report_apart.md").read_text()
moved2 = []
def cut_between(a, b, label, keep=""):
    global s3
    i = s3.index(a); j = s3.index(b, i) if b else s3.index("\n\n", i)
    moved2.append((label, s3[i:j].strip())); s3 = s3[:i] + keep + s3[j:]
cut_between("A second pre-registered line failed in both halves:", "\n\n", "D.6 Page-order and direction tests",
            "Two further pre-registered lines failed: content does not order a page's revisions better than length, and does not tell which near-duplicate came first (Appendix D.6).")
cut_between("The signal is strongest on the busiest days", "This is temporal association", "D.7 Calendar, exploratory variants")
cut_between("The whole-family statistic agrees (T = 0.292", "\n\n", "D.8 Whole-family statistic and alternative distances")
fi = s3.index("### Future Work"); fj = s3.index("## 6. Conclusion", fi)
s3 = s3[:fi] + "### Future Work\n\nTest the clock and calendar on more corpora with real timestamp availability and LLM-style rewriting; turn co-time and the calendar into a calibrated imputation tool; and prototype the gateway-side log (time, actor, content hash).\n\n" + s3[fj:]
app2 = "\n\n".join(f"**{lab}.**\n\n{par}" for lab, par in moved2) + "\n\n"
k = s3.index("## LLM Usage Statement"); s3 = s3[:k] + app2 + s3[k:]
(ROOT / "paper/report_apart.md").write_text(s3)
print("condensed2; main words:", len(s3[s3.index('## 1. Introduction'):s3.index('## References')].split()))

# ---- third condensation pass
s4 = (ROOT / "paper/report_apart.md").read_text()
moved3 = []
i = s4.index("### 3.1 Data and feasibility"); j = s4.index("### 3.2 Analysis", i)
moved3.append(("D.9 Corpora (Table 1)", s4[i:j].split("\n", 1)[1].strip()))
s4 = s4[:i] + "### 3.1 Data and feasibility\n\nWe use collusion.wiki (14,591 agent revisions; 3,102 self-chosen labels; request-log times), the main testable corpus; Swarm Traces (189,579 records without native timestamps), which fails a pre-registered anchor-feasibility gate (Appendix C.1); and Mantiq (19 runs of an 18-agent coding swarm with true agent IDs and recorder timestamps; CC-BY-4.0). Table 1 (Appendix D.9) summarizes what each corpus can test.\n\n" + s4[j:]
i = s4.index("### 4.6 A pitfall: whole-family tests are anti-conservative"); j = s4.index("### 4.7", i)
moved3.append(("D.10 Whole-family tests (Finding D)", s4[i:j].split("\n", 1)[1].strip()))
s4 = s4[:i] + "### 4.6 A pitfall: whole-family tests are anti-conservative\n\nTesting whole recovered families, which absorb real members, flags a planted no-clock lineage in 15% of cases, against 4% when only planted members are tested (200 lineages per condition; Appendix D.10): real members' temporal structure is misattributed to the lineage, so whole-family p-values on real data must be read with this in mind.\n\n" + s4[j:]
i = s4.index("**For monitoring (Track 4).**"); j = s4.index("\n\n", i)
moved3.append(("D.11 Monitoring implications", s4[i:j].strip())); s4 = s4[:i] + s4[j+2:]
app3 = "\n\n".join(f"**{lab}.**\n\n{par}" for lab, par in moved3) + "\n\n"
k = s4.index("## LLM Usage Statement"); s4 = s4[:k] + app3 + s4[k:]
(ROOT / "paper/report_apart.md").write_text(s4)
print("condensed3; main words:", len(s4[s4.index('## 1. Introduction'):s4.index('## References')].split()))

# ---- fourth pass: drop the intro "Answer in one paragraph" (redundant with abstract and take-away)
s5 = (ROOT / "paper/report_apart.md").read_text()
i = s5.index("**Answer in one paragraph.**"); j = s5.index("\n\n", i)
s5 = s5[:i] + s5[j+2:]
(ROOT / "paper/report_apart.md").write_text(s5)
print("condensed4; main words:", len(s5[s5.index('## 1. Introduction'):s5.index('## References')].split()))
