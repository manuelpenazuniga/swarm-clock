"""Fill the official Apart template .docx in place (keeps its styles, header tables, fonts) with paper/report_apart.md."""
import copy, re, sys
from pathlib import Path
import docx
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = Path(__file__).resolve().parents[1]
TPL = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/Users/mpz/Downloads/Copia de Apart Research hackathon submission template_.docx")
OUT = ROOT / "paper" / "Apart_submission_SwarmClock.docx"
md = (ROOT / "paper/report_apart.md").read_text()

d = docx.Document(str(TPL))
P = d.paragraphs

# ---------------------------------------------------------------- helpers
INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`)")

def add_runs(p, text, italic=False, size=None):
    for tok in INLINE.split(text):
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**"):
            r = p.add_run(tok[2:-2]); r.bold = True
        elif tok.startswith("`") and tok.endswith("`"):
            r = p.add_run(tok[1:-1]); r.font.name = "Courier New"
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            r = p.add_run(tok[1:-1]); r.italic = True
        else:
            r = p.add_run(tok)
        if italic:
            r.italic = True
        if size:
            r.font.size = Pt(size)

def clear_runs(p_el):
    for child in list(p_el):
        if child.tag in (qn("w:r"), qn("w:hyperlink")):
            p_el.remove(child)

def set_text(p, text):
    clear_runs(p._p); add_runs(p, text)

class Cursor:
    def __init__(self, anchor):
        self.el = anchor
    def put(self, el):
        self.el.addnext(el); self.el = el

def new_par(style="normal"):
    p = d.add_paragraph(style=style)
    if style == "normal":
        p.paragraph_format.space_after = Pt(2)
    el = p._p; el.getparent().remove(el)
    return docx.text.paragraph.Paragraph(el, d._body)

# prototypes for template list formatting
proto_num = copy.deepcopy(P[12]._p)       # numbered list item
proto_bul = copy.deepcopy(P[38]._p)       # bulleted list item
for pr in (proto_num, proto_bul):
    clear_runs(pr)

def list_par(proto, text):
    el = copy.deepcopy(proto)
    p = docx.text.paragraph.Paragraph(el, d._body)
    add_runs(p, text)
    return p

def table_el(rows):
    hdr = [c.strip() for c in rows[0].strip("|").split("|")]
    body = [[c.strip() for c in r.strip("|").split("|")] for r in rows[2:]]
    t = d.add_table(rows=1 + len(body), cols=len(hdr))
    for j, h in enumerate(hdr):
        cp = t.rows[0].cells[j].paragraphs[0]; add_runs(cp, h, size=8)
        for r in cp.runs: r.bold = True
    for i, row in enumerate(body):
        for j, v in enumerate(row[:len(hdr)]):
            add_runs(t.rows[i + 1].cells[j].paragraphs[0], v, size=8)
    tblPr = t._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for e in ("top", "bottom", "insideH"):
        x = OxmlElement(f"w:{e}"); x.set(qn("w:val"), "single"); x.set(qn("w:sz"), "4"); x.set(qn("w:color"), "808080"); b.append(x)
    tblPr.append(b)
    el = t._tbl; el.getparent().remove(el)
    return el

FIGW = {"fig1_three_times": 4.8, "fig2_copy_modes": 6.2, "figC1_lag_curves": 5.0, "figC2_lifespans": 3.6}

def emit(cur, text):
    """Render a markdown fragment after the cursor."""
    blocks = re.split(r"\n\s*\n", text.strip())
    for blk in blocks:
        lines = blk.strip("\n").split("\n")
        first = lines[0].strip()
        if not first:
            continue
        if first.startswith("### "):
            p = new_par("Heading 3"); add_runs(p, first[4:]); cur.put(p._p)
            rest = "\n".join(lines[1:]).strip()
            if rest: emit(cur, rest)
        elif first.startswith("!["):
            m = re.match(r"!\[[^\]]*\]\(\.\./outputs/figs/([A-Za-z0-9_]+)\.png\)", first)
            p = new_par(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(str(ROOT / "outputs/figs" / f"{m.group(1)}.png"), width=Inches(FIGW.get(m.group(1), 6.0)))
            cur.put(p._p)
            if len(lines) > 1:
                cap = new_par(); add_runs(cap, lines[1].strip().strip("*"), italic=True, size=9); cur.put(cap._p)
        elif first.startswith("*Figure") or first.startswith("*Figure C"):
            cap = new_par(); add_runs(cap, " ".join(l.strip() for l in lines).strip("*"), italic=True, size=9); cur.put(cap._p)
        elif first.startswith("|"):
            cur.put(table_el([l for l in lines if l.strip().startswith("|")]))
            sp = new_par(); cur.put(sp._p)
        elif re.match(r"^- ", first):
            for l in lines:
                if l.startswith("- "): cur.put(list_par(proto_bul, l[2:].strip())._p)
                elif cur.el is not None: pass
        elif re.match(r"^\d+\. ", first):
            for l in lines:
                m = re.match(r"^\d+\. (.*)", l)
                if m: cur.put(list_par(proto_num, m.group(1).strip())._p)
        else:
            p = new_par(); add_runs(p, " ".join(l.strip() for l in lines)); cur.put(p._p)

# ---------------------------------------------------------------- parse source sections
def section(name, nxt):
    i = md.index(name); j = md.index(nxt, i + len(name)) if nxt else len(md)
    return md[i + len(name):j].strip()
title = md.splitlines()[0].lstrip("# ").strip()
abstract = section("**Abstract**", "## 1. Introduction")
S = {
    "1. Introduction": section("## 1. Introduction", "## 2. Related Work"),
    "2. Related Work": section("## 2. Related Work", "## 3. Methods"),
    "3. Methods": section("## 3. Methods", "## 4. Results"),
    "4. Results": section("## 4. Results", "## 5. Discussion and Limitations"),
}
disc_all = section("## 5. Discussion and Limitations", "## 6. Conclusion")
S["5. Discussion and Limitations"] = disc_all.split("### Limitations")[0].strip()
S["Limitations"] = disc_all.split("### Limitations")[1].split("### Future Work")[0].strip()
S["Future Work"] = disc_all.split("### Future Work")[1].strip()
S["6. Conclusion"] = section("## 6. Conclusion", "## Code and Data")
S["Code and Data"] = section("## Code and Data", "## Author Contributions")
S["Author Contributions"] = section("## Author Contributions", "## References")
refs = section("## References", "## Appendix")
S["References"] = "\n".join(re.sub(r"^- ", "", l) for l in refs.splitlines() if l.strip())
S["Appendix"] = section("## Appendix", "## LLM Usage Statement")
S["LLM Usage Statement"] = section("## LLM Usage Statement", None)

# drop the take-away paragraph (redundant with the abstract in this version); shorten Figure 1 caption
_i = S["1. Introduction"]
_ti = _i.find("**Take-away.**")
if _ti >= 0:
    _tj = _i.find("\n\n", _ti); S["1. Introduction"] = _i[:_ti] + _i[_tj + 2:]
_i = S["1. Introduction"]
_ci = _i.find("*Figure 1."); _cj = _i.find("\n\n", _ci)
S["1. Introduction"] = _i[:_ci] + "*Figure 1. Three kinds of time in agent text (collusion.wiki). (a) No detected clock: distance between added texts does not grow with lag, unlike a planted clock, while whole page bodies drift (positive control). (b) Detection of planted clocks with the real sampling, families fixed or rebuilt end to end (band: 95% Wilson interval; crosses: no-clock controls). (c) Co-time: share of near-duplicate partners written within 1 h, pilot and held-out halves. (d) Calendar: share of covered held-out texts within [-1 h, +24 h] of the first-appearance estimate, real vs permuted anchor times.*" + _i[_cj:]

# move Table 2 (window tests) to the appendix to respect the 8-page limit in the template's typography
_r = S["4. Results"]
_a = _r.find("**Table 2.**")
if _a >= 0:
    _b = _r.find("\n\n", _r.find("|", _a))
    _b = len(_r) if _b < 0 else _b
    _tab = _r[_a:_b]
    S["4. Results"] = _r[:_a] + "Table 2 (Appendix) lists all window statistics; the key values are summarized here." + _r[_b:]
    S["Appendix"] = S["Appendix"] + "\n\n### E. Window tests (Table 2)\n\n" + _tab

# condensed limitations in the main text; the full list goes to the appendix
S["Appendix"] = S["Appendix"] + "\n\n### F. Full list of limitations\n\n" + S["Limitations"]
S["Limitations"] = ("One testable corpus with only four long-lived families; lexical, masked families (paraphrase is invisible); synthetic token-level clocks, "
    "with clocks confined to one family not excluded; association rather than dating for the clock test; an empirical, one-sided calendar interval with 71% coverage "
    "on one corpus; an inconclusive Mantiq replication; Swarm Traces tested only for anchor feasibility; labels are not identities. Full list in Appendix F.")

# contributions as the template's numbered list
_i = S["1. Introduction"]
if "**Our main contributions are:**" in _i:
    a, b = _i.split("**Our main contributions are:**", 1)
    lines = b.strip().split("\n\n")[0]
    rest = b.strip()[len(lines):]
    num = "\n".join(f"{k+1}. {l[2:]}" for k, l in enumerate([x for x in lines.split("\n") if x.startswith("- ")]))
    S["1. Introduction"] = a + "**Our main contributions are:**\n\n" + num + rest

# ---------------------------------------------------------------- header
hdr = d.tables[0]
set_text(hdr.rows[0].cells[0].paragraphs[1], title)
auth_tbl = hdr.rows[1].cells[0].tables[0].rows[0].cells[0].tables[0]
cells = [c for r in auth_tbl.rows for c in r.cells]
seen = set(); uniq = []
for c in cells:
    if id(c._tc) not in seen:
        seen.add(id(c._tc)); uniq.append(c)
for k, c in enumerate(uniq):
    p = c.paragraphs[0]; clear_runs(p._p)
    for extra in c.paragraphs[1:]:
        extra._p.getparent().remove(extra._p)
    if k == 1:
        r = p.add_run("Manuel Peña-Zúñiga"); r.add_break(); p.add_run("Independent researcher, Santiago, Chile")
# drop the second author row and merge the first row into one centered cell
if len(auth_tbl.rows) > 1:
    auth_tbl._tbl.remove(auth_tbl.rows[1]._tr)
row = auth_tbl.rows[0]
merged = row.cells[0].merge(row.cells[len(row.cells) - 1])
for p_ in merged.paragraphs:
    if not p_.text.strip():
        p_._p.getparent().remove(p_._p)
mp = merged.paragraphs[0]; clear_runs(mp._p)
mp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = mp.add_run("Manuel Peña-Zúñiga"); r.add_break(); mp.add_run("Independent researcher, Santiago, Chile")
merged.width = Inches(5.0)
tcW = merged._tc.get_or_add_tcPr().find(qn("w:tcW"))
if tcW is not None: tcW.set(qn("w:w"), str(int(5.0 * 1440))); tcW.set(qn("w:type"), "dxa")
for gc in auth_tbl._tbl.tblGrid.findall(qn("w:gridCol")):
    gc.set(qn("w:w"), str(int(5.0 * 1440 / max(1, len(auth_tbl._tbl.tblGrid.findall(qn("w:gridCol")))))))
abs_cell = hdr.rows[1].cells[0].tables[1].rows[0].cells[0]
ap = abs_cell.paragraphs[0]; clear_runs(ap._p); add_runs(ap, abstract)
for r in ap.runs:
    r.italic = False
for extra in abs_cell.paragraphs[1:]:
    extra._p.getparent().remove(extra._p)

# remove the "How to use this template" box
d.tables[1]._tbl.getparent().remove(d.tables[1]._tbl)

# ---------------------------------------------------------------- body: clear guidance, insert content
heads = [p for p in d.paragraphs if p.style.name in ("Heading 2", "Heading 3")]
body_el = d._body._body
allp = list(d.paragraphs)
head_idx = [i for i, p in enumerate(allp) if p.style.name in ("Heading 2", "Heading 3")]
# delete every non-heading paragraph after the first heading (guidance), keep sectPr
first = head_idx[0]
for p in allp[first:]:
    if p.style.name not in ("Heading 2", "Heading 3"):
        p._p.getparent().remove(p._p)
for p in d.paragraphs:
    if p.style.name in ("Heading 2", "Heading 3"):
        t = p.text.strip()
        if t.startswith("Author Contributions"): set_text(p, "Author Contributions"); t = "Author Contributions"
        if t.startswith("Appendix"): set_text(p, "Appendix"); t = "Appendix"
        key = t
        if key in S:
            cur = Cursor(p._p)
            if key == "References":
                for l in S[key].splitlines():
                    cur.put(list_par(proto_num, l.strip())._p)
            else:
                emit(cur, S[key])
d.save(str(OUT))
print("wrote", OUT)

# ---------------------------------------------------------------- replicate the template's direct (run-level) formatting
from docx.shared import RGBColor
OSTT = "Old Standard TT"
def set_font(run, name=OSTT):
    rPr = run._r.get_or_add_rPr()
    rf = rPr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rPr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), name)
def all_paragraphs(container):
    for p in container.paragraphs:
        yield p
    for t in container.tables:
        for row in t.rows:
            for c in row.cells:
                yield from all_paragraphs(c)
for p in all_paragraphs(d):
    for r in p.runs:
        if r.font.name == "Courier New":
            continue
        set_font(r)
    if p.style.name == "Heading 3":
        pf = p.paragraph_format; pf.space_before = Pt(10); pf.space_after = Pt(2)
        for r in p.runs:
            r.bold = True; r.font.size = Pt(13); r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    if p.style.name == "Heading 2":
        pf = p.paragraph_format; pf.space_before = Pt(10); pf.space_after = Pt(0)
        for r in p.runs:
            r.bold = True; r.font.size = Pt(14); r.font.color.rgb = RGBColor(0x43, 0x43, 0x43)
d.save(str(OUT))
print("formatted", OUT)
