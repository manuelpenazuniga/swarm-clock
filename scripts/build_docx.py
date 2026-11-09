"""Render paper/report.md to paper/report.docx (pandoc via pypandoc_binary). Figures embedded at 300 dpi.
If paper/apart_template.docx exists, it is used as the pandoc reference document (styles)."""
from pathlib import Path
import re, pypandoc
ROOT = Path(__file__).resolve().parents[1]
md = (ROOT / "paper/report.md").read_text()
md = md.replace("<br>\n", "  \n")                      # hard line breaks
md = re.sub(r"!\[(Figure C?\d)\]\(\.\./outputs/figs/(fig[A-Za-z0-9_]+)\.png\)", lambda m: f"![]({ROOT}/outputs/figs/{m.group(2)}.png){{width=6.3in}}", md)
for small in ("figC2_lifespans",):
    md = md.replace(f"{ROOT}/outputs/figs/{small}.png){{width=6.3in}}", f"{ROOT}/outputs/figs/{small}.png){{width=3.6in}}")
md = md.replace(f"{ROOT}/outputs/figs/figC1_lag_curves.png){{width=6.3in}}", f"{ROOT}/outputs/figs/figC1_lag_curves.png){{width=5.0in}}")
tmp = ROOT / "paper/_docx_src.md"; tmp.write_text(md)
args = ["--resource-path", str(ROOT)]
ref = ROOT / "paper/apart_template.docx"
if ref.exists():
    args += ["--reference-doc", str(ref)]
pypandoc.convert_file(str(tmp), "docx", format="markdown+pipe_tables+raw_html", outputfile=str(ROOT / "paper/report.docx"), extra_args=args)
tmp.unlink()
print("wrote paper/report.docx")

# post-process: booktabs-like borders, small table font
import docx
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
d = docx.Document(str(ROOT / "paper/report.docx"))
for t in d.tables:
    tblPr = t._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "bottom", "insideH"):
        e = OxmlElement(f"w:{edge}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:color"), "808080"); b.append(e)
    tblPr.append(b)
    for row in t.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(8)
d.save(str(ROOT / "paper/report.docx"))
print("styled tables:", len(d.tables))
