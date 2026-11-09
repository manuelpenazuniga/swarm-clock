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
contrib = "M.P. conceived the question, designed and ran all analyses, and wrote the report (solo project)."
llm = ("We used Claude (Anthropic) through Claude Code to refactor the analysis notebooks into a pipeline, run and extend the analyses, draft and revise "
"the text and figures, and run independent sub-agent reviews; GPT-6 Astra (via Codex) and Gemini 4 Argon (via agy) were used as independent auditors. "
"Some extension designs (the co-time split-half test and the calendar test) were proposed and piloted by AI agents and pre-registered before computation, "
"as disclosed in the decision log. All numbers in this report are produced by the released code and read from its output tables; the main results were "
"re-run and reproduced, and every reference was checked against its source. The author is responsible for all content.")
out = f"""# {title}

Manuel Peña  
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
