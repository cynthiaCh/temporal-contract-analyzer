#!/usr/bin/env python3
"""Read-only checks on frozen source, runtime assertions, and static inputs."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from temporal_contract_analyzer.core import analyze_sources


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = HERE/'run-02'
    summary = read(output/'summary.json')
    cases = read(HERE/'CASES.json')['cases']
    labels = read(output/'RUNTIME_LABELS.json')
    plan = read(output/'TEST_PLAN.json')
    assert plan['written_before_runtime'] and labels['analysis_not_yet_run']
    assert plan['source_freeze_sha256'] == digest(HERE/'INPUT_HASHES.json')
    assert plan['test_code_hashes'] == labels['test_code_hashes']
    for path, expected in labels['test_code_hashes'].items():
        assert digest(HERE/path) == expected, path
    for path, expected in read(HERE/'INPUT_HASHES.json').items():
        assert digest(HERE/path) == expected, path
    with zipfile.ZipFile(HERE/'frozen-tool/source.zip') as archive:
        for path, expected in read(HERE/'frozen-tool/FILES.json').items():
            assert hashlib.sha256(archive.read(path)).hexdigest() == expected
            assert digest(HERE.parents[1]/path) == expected
    current = analyze_sources({})
    rows = summary['rows']
    assert len(rows) == len(cases) == len(labels['rows']) == 14
    assert len({r['implementation'] for r in rows}) == 7
    for case, behavior, result, expectation in zip(cases, labels['rows'], rows, plan['cases']):
        assert case['id'] == behavior['case'] == result['case'] == expectation['id']
        assert result['tool_sha256'] == current['tool_sha256'] == read(HERE/'PROTOCOL.json')['tool_sha256']
        assert result['tests'] == behavior['tests']
        assert sorted(result['failed_tests']) == sorted(expectation['expected_failed_tests'])
        folder = output/case['id']
        report = read(folder/'report.json')
        for file in report['files']:
            assert file['sha256'] == digest(HERE/'snapshots'/case['id']/file['path'])
        if (folder/'flow-adapter.json').exists():
            original = (HERE/'snapshots'/case['id']/case['entry']).read_text()
            adapter = read(folder/'flow-adapter.json')
            chars = list(original)
            for region in adapter['erased_ranges']:
                assert region['kind'] in {'TypeAlias', 'TypeAnnotation', 'TypeParameterDeclaration'}
                for i in range(region['start'], region['end']):
                    if chars[i] not in '\r\n\u2028\u2029': chars[i] = ' '
            assert ''.join(chars) == (folder/'runtime-erased.mjs').read_text()
    audit = dict(independent_implementations=7, snapshots=14, real_upstream_fix_pairs=5,
                 runtime_tests=sum(r['tests']['tests'] for r in rows),
                 passing_assertions=sum(r['tests']['pass'] for r in rows),
                 expected_failing_assertions=sum(r['tests']['fail'] for r in rows),
                 tool_sha256=current['tool_sha256'], tool_unchanged=True,
                 original_sources_and_runtime_adapter_checked=True,
                 runtime_plan_and_code_hashes_match=True,
                 parsed_snapshots=sum(r['status'] == 'parsed' for r in rows),
                 flow_parse_failures=[r['case'] for r in rows if r['status'] != 'parsed'],
                 bug_versions_with_default_cards=[r['case'] for r in rows if r['label'] == 'upstream_bug' and r['focused_cards']],
                 candidates_on_behavior_controls=[r['case'] for r in rows if r['label'] == 'behavior_control' and r['focused_cards']],
                 limitations='Deterministic local integrity checks, not an independent external audit or semantic proof. Cases were selected by availability and upstream issue history, not random sampling.')
    assert audit['runtime_tests'] == 50 and audit['expected_failing_assertions'] == 8
    destination = output/'integrity.json'
    assert not destination.exists()
    destination.write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
