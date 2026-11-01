"""Check this draft's local references, actual PDF, and recorded demonstration."""
import json
from pathlib import Path
import re
import fitz

PAPER = Path(__file__).resolve().parents[1]
main = (PAPER / "main.tex").read_text()
sections = sorted((PAPER / "sections").glob("*.tex"))
source = main + "\n" + "\n".join(path.read_text() for path in sections)
cited = {key.strip() for group in re.findall(r"\\cite\{([^}]+)\}", source) for key in group.split(",")}
bibkeys = set(re.findall(r"@\w+\{([^,]+),", (PAPER / "references.bib").read_text()))
assert cited == bibkeys, (cited, bibkeys)
labels = set(re.findall(r"\\label\{([^}]+)\}", source))
labels.update(re.findall(r"label=\{([^}]+)\}", source))
refs = set(re.findall(r"\\ref\{([^}]+)\}", source))
assert refs <= labels, refs - labels
assert all("sections/" + path.name in main for path in sections)
assert not re.search(r"TODO|FIXME|\[VERIFY\]", source)
log = (PAPER / "main.log").read_text()
assert not re.search(r"(?:Citation|Reference).*undefined|Undefined control sequence|Overfull \\hbox", log)
aux = (PAPER / "main.aux").read_text()
body_page = int(re.search(r"\\newlabel\{mainbodyend\}\{\{[^}]*\}\{(\d+)\}", aux).group(1))
doc = fitz.open(PAPER / "main.pdf")
assert body_page <= 4 and len(doc) <= 5, (body_page, len(doc))
text = "\n\f\n".join(page.get_text() for page in doc)
assert "??" not in text
font_records = {font[0]: font for page in doc for font in page.get_fonts()}
assert all(doc.extract_font(xref)[3] for xref in font_records), "Unembedded font"
traces = json.loads((PAPER / "evidence/demo-traces.json").read_text())
assert traces["records"][0]["outputs"] == ["old result"]
assert traces["records"][1]["outputs"] == []
analysis = json.loads((PAPER / "evidence/demo-analysis.json").read_text())
rules = [[hint["rule"] for hint in analysis[v]["report"]["findings"]] for v in ("unguarded", "guarded")]
assert rules[0] == rules[1] and len(rules[0]) == 3
comparison = json.loads((PAPER / "evidence/demo-comparison.json").read_text())
assert comparison["comparable"] is True
archive = json.loads((PAPER / "evidence/demo-archive.json").read_text())
assert len(archive["notes"]) == 1
report = {
    "pdf_pages": len(doc), "main_body_end_page": body_page,
    "citation_keys": sorted(cited), "undefined_references": 0,
    "undefined_citations": 0, "all_pdf_fonts_embedded": True,
    "font_names": sorted(font[3] for font in font_records.values()),
    "demo_scope": "two synthetic variants, one controlled schedule",
    "demo_rule_kinds": rules[0], "comparison_comparable": True,
    "scripted_author_notes": len(archive["notes"]),
    "status": "local-draft-checks-pass; not submission certification",
}
(PAPER / "evidence/document-checks.json").write_text(json.dumps(report, indent=2) + "\n")
(PAPER / "evidence/manuscript-text.txt").write_text(text)
for i, page in enumerate(doc):
    page.get_pixmap(matrix=fitz.Matrix(1.4, 1.4)).save(PAPER / "evidence" / ("page-%d.png" % (i + 1)))
print(json.dumps(report, indent=2))
