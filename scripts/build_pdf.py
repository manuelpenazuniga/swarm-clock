"""Render paper/report.md to paper/report.pdf (HTML + headless Chrome). Interim until the official template is used."""
import re, subprocess, sys
from pathlib import Path
import markdown
ROOT = Path(__file__).resolve().parents[1]
md = (ROOT / "paper/report.md").read_text()
md = md.replace("../outputs/figs/", str(ROOT / "outputs/figs") + "/")
body = markdown.markdown(md, extensions=["tables", "sane_lists"])
css = """
@page { size: A4; margin: 18mm 17mm 18mm 17mm; }
body { font-family: 'Times New Roman', Times, serif; font-size: 10.3pt; line-height: 1.32; color: #111; }
h1 { font-size: 15pt; text-align: center; margin: 0 0 6pt; line-height: 1.2; }
h2 { font-size: 11.5pt; margin: 10pt 0 4pt; } h3 { font-size: 10.5pt; margin: 8pt 0 3pt; }
p { margin: 3pt 0 4pt; text-align: justify; } li { margin: 1pt 0; text-align: justify; }
table { border-collapse: collapse; font-size: 8.4pt; margin: 4pt auto 6pt; } th, td { border-top: 0.5pt solid #888; border-bottom: 0.5pt solid #888; padding: 1.5pt 4pt; }
th { background: #f0f0f0; } img { display: block; margin: 4pt auto 0; max-width: 100%; } em { font-size: 9pt; }
hr { border: 0; border-top: 0.5pt solid #aaa; margin: 6pt 0; } code { font-size: 8.5pt; }
img[alt="Figure 1"] { max-width: 100%; } img[alt="Figure 2"], img[alt="Figure C1"] { max-width: 85%; }
img[alt="Figure 3"] { max-width: 85%; }
"""
html = f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{body}</body></html>"
(ROOT / "paper/report.html").write_text(html)
chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={ROOT/'paper/report.pdf'}",
                f"file://{ROOT/'paper/report.html'}"], check=True, capture_output=True)
from pypdf import PdfReader
r = PdfReader(str(ROOT / "paper/report.pdf"))
n = len(r.pages)
for i, p in enumerate(r.pages):
    t = p.extract_text() or ""
    for key in ["## 7. Limitations", "7. Limitations", "Appendix A", "References"]:
        if key in t: print(f"page {i+1}: {key}")
print("pages:", n)
