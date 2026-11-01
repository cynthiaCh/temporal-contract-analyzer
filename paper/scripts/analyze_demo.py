"""Reproduce syntax reports for the paper's synthetic variants; no execution."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from temporal_contract_analyzer.core import analyze_sources
from temporal_contract_analyzer.boundary_cards import cards


def main():
    result = {}
    for variant in ("unguarded", "guarded"):
        source = ROOT / "paper" / "demo" / variant / "panel.cjs"
        report = analyze_sources({"panel.cjs": source.read_text(encoding="utf-8")})
        if report["status"] != "parsed":
            raise RuntimeError("Parser unavailable or incomplete: " + variant)
        result[variant] = {
            "source": str(source.relative_to(ROOT)),
            "report": report,
            "cards": cards(report),
        }
    destination = ROOT / "paper" / "evidence" / "demo-analysis.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({variant: [x["rule"] for x in record["report"]["findings"]]
                      for variant, record in result.items()}))


if __name__ == "__main__":
    main()
