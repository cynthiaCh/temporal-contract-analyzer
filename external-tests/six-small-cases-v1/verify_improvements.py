#!/usr/bin/env python3
"""Check same-input reproduction and established historical controls."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from temporal_contract_analyzer.core import analyze_sources
from temporal_contract_analyzer.layers import verify_bundle
from temporal_contract_analyzer.review import focused_review


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--node', default='/Applications/Visual Studio Code.app/Contents/MacOS/Code')
    args = parser.parse_args()
    run = args.run.resolve()
    destination = run / 'verification.json'
    assert not destination.exists()
    baseline = {(r['case'], r['variant']): r for r in read(HERE/'run-02/summary.json')['rows']}
    current = read(run/'summary.json')['rows']
    assert len(current) == len(baseline) == 8
    assert len({r['tool_sha256'] for r in current}) == 1
    assert current[0]['tool_sha256'] == analyze_sources({})['tool_sha256']
    rows = []
    for row in current:
        old = baseline[(row['case'], row['variant'])]
        for field in ['input_sha256', 'tests', 'runtime_exit_code', 'observations']:
            assert row[field] == old[field], (row['case'], row['variant'], field)
        expected = int(row['case'] == 'just-memoize-last' or row['variant'] != 'original')
        assert row['focused_cards'] == expected
        report = read(run/row['case']/row['variant']/'report.json')
        assert len(focused_review(report)['cards']) == expected
        rows.append(dict(case=row['case'], variant=row['variant'], identical_input_and_runtime=True,
                         baseline_cards=old['focused_cards'], current_cards=row['focused_cards']))
    historic = ROOT/'external-tests/reentry-publication-v1/run-07'
    controls = []
    for old in read(historic/'summary.json')['rows']:
        source = (historic/old['name']/'index.js').read_text()
        report = analyze_sources({'index.js': source}, node=args.node)
        statuses = [f['state_publication']['status'] for f in report['findings'] if 'state_publication' in f]
        assert statuses == old['expected'], (old['name'], statuses, old['expected'])
        cards = len(focused_review(report)['cards'])
        assert cards == int('write_after_call' in statuses)
        controls.append(dict(name=old['name'], statuses=statuses, focused_cards=cards,
                             input_sha256=report['input_sha256'], tool_sha256=report['tool_sha256']))
    frozen = historic/'before/bundle'
    manifest = verify_bundle(frozen)
    verification = dict(tool_version=current[0]['tool_version'], tool_sha256=current[0]['tool_sha256'],
                        same_input_comparison=rows, historical_controls=controls,
                        historical_bundle=dict(path=str(frozen.relative_to(ROOT)), verified=True,
                                               input_sha256=manifest['input_sha256']))
    destination.write_text(json.dumps(verification, ensure_ascii=False, indent=2)+'\n')
    hashes = read(run/'reproduction_hashes.json')
    hashes['verify_improvements.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (run/'reproduction_hashes.json').write_text(json.dumps(hashes, indent=2)+'\n')
    print(json.dumps(verification, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
