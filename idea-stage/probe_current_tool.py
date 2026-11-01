"""Reproduce bounded ideation probes; never execute benchmark candidates.

Only the small JavaScript function authored below is executed. Existing
development cases are scanned as source, and are not held-out evaluation data.
Run from the repository root: python3 -B idea-stage/probe_current_tool.py
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from temporal_contract_analyzer.core import analyze_sources, compare, scan
from temporal_contract_analyzer.boundary_cards import cards


BEFORE = """async function refresh(active, read, render) {
  if (!active()) return;
  const result = await read();
  render(result);
}
"""
AFTER = """async function refresh(active, read, render) {
  const result = await read();
  if (!active()) return;
  render(result);
}
"""


def main():
    before = analyze_sources({'refresh.js': BEFORE})
    after = analyze_sources({'refresh.js': AFTER})
    delta = compare(before, after)
    result = {
        'kind': 'exploratory_tool_ideation_probes',
        'scope': 'One authored pair and two already-exposed development cases; no accuracy estimate',
        'tool_version': before['tool_version'],
        'tool_sha256': before['tool_sha256'],
        'guard_relocation': {
            'before_source': BEFORE, 'after_source': AFTER,
            'before_status': before['status'], 'after_status': after['status'],
            'before_rules': [f['rule'] for f in before['findings']],
            'after_rules': [f['rule'] for f in after['findings']],
            'comparable': delta['comparable'],
            'changed_files': delta['changed_files'],
            'added_hints': len(delta['added_hints']),
            'removed_hints': len(delta['removed_hints']),
            'synthetic_requirement': 'Render only if the supplied active predicate holds after read completes.',
        },
        'development_cases': [],
    }
    node = shutil.which('node')
    if node:
        # A controlled schedule, not a general execution-equivalence check.
        replay = '''
const variants = JSON.parse(process.argv[1]);
(async () => {
  const output = {};
  for (const [scenario, initiallyActive, invalidate] of [
    ['invalidated_during_read', true, true],
    ['inactive_at_entry', false, false],
    ['remains_active', true, false],
  ]) {
    output[scenario] = {};
    for (const [name, source] of Object.entries(variants)) {
      const refresh = new Function(source + '; return refresh;')();
      let active = initiallyActive;
      let readCalls = 0;
      let resolve;
      const pending = new Promise(r => { resolve = r; });
      const effects = [];
      const work = refresh(
        () => active, () => { readCalls++; return pending; }, x => effects.push(x)
      );
      if (invalidate) active = false;
      resolve('payload');
      await work;
      output[scenario][name] = {read_calls: readCalls, render_effects: effects};
    }
  }
  console.log(JSON.stringify(output));
})().catch(e => { console.error(e); process.exitCode = 1; });
'''
        execution = subprocess.run(
            [node, '-e', replay, json.dumps({'before': BEFORE, 'after': AFTER})],
            check=True, capture_output=True, text=True, timeout=10,
        )
        scenarios = json.loads(execution.stdout)
        result['guard_relocation']['controlled_scenarios'] = scenarios
        result['guard_relocation']['controlled_execution'] = {
            name: observation['render_effects']
            for name, observation in scenarios['invalidated_during_read'].items()
        }
    else:
        result['guard_relocation']['controlled_execution'] = {'status': 'node_unavailable'}

    bench = ROOT.parent / 'temporal-contract-bench'
    paths = {
        'transfer': 'case-clusters/transfer-retry-handoff/arms/transfer-progress-maintenance-v2-vanilla/base',
        'vue_readiness': 'case-clusters/local-config-readiness/arms/local-config-readiness-latent-vue2/base',
    }
    for name, relative in paths.items():
        path = bench / relative
        if not path.is_dir():
            result['development_cases'].append({'name': name, 'status': 'source_unavailable'})
            continue
        report = scan(path)
        view = cards(report)
        events = [e for f in report['files'] for e in f['events']]
        result['development_cases'].append({
            'name': name, 'source_path': str(path),
            'input_sha256': report['input_sha256'], 'status': report['status'],
            'summary': report['summary'], 'cards': len(view),
            'cards_with_effect': sum(bool(c['effects']['evidence_ids']) for c in view),
            'record_receive_calls': [
                {'id': e['id'], 'callee': e.get('callee'), 'tags': e['tags'], 'text': e['text']}
                for e in events if e.get('callee') in {'record', 'receive'}
            ],
        })
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
