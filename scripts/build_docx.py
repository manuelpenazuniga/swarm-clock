"""Render paper/report.md to paper/report.docx (pandoc via pypandoc_binary). Figures embedded at 300 dpi.
If paper/apart_template.docx exists, it is used as the pandoc reference document (styles)."""
from pathlib import Path
import re, pypandoc
ROOT = Path(__file__).resolve().parents[1]
md = (ROOT / "paper/report.md").read_text()
md = md.replace("<br>\n", "  \n")                      # hard line breaks
md = re.sub(r"!\[(Figure \d)\]\(\.\./outputs/figs/(fig\d_[a-z_]+)\.png\)", lambda m: f"![]({ROOT}/outputs/figs/{m.group(2)}.png){{width=6.3in}}", md)
for small in ("fig1_lifespans", "fig4_power"):
    md = md.replace(f"{ROOT}/outputs/figs/{small}.png){{width=6.3in}}", f"{ROOT}/outputs/figs/{small}.png){{width=3.6in}}")
tmp = ROOT / "paper/_docx_src.md"; tmp.write_text(md)
args = ["--resource-path", str(ROOT)]
ref = ROOT / "paper/apart_template.docx"
if ref.exists():
    args += ["--reference-doc", str(ref)]
pypandoc.convert_file(str(tmp), "docx", format="markdown+pipe_tables+raw_html", outputfile=str(ROOT / "paper/report.docx"), extra_args=args)
tmp.unlink()
print("wrote paper/report.docx")
