"""Read-only public-metadata validation. No models, graders, manifests or network."""
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FIELDS = ['rank', 'split', 'case_id', 'core_case', 'source_unit',
          'mechanism_hint', 'runtime', 'manifest', 'source_rank', 'batch']


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_csv(data):
    return list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))


def balanced_order(rows):
    """Proportional deficit, source then core; alphabetical ties and case IDs."""
    total = len(rows)
    source_counts = collections.Counter(r['source_unit'] for r in rows)
    source_used = collections.Counter()
    buckets = {}
    core_counts = {}
    core_used = {}
    for source in source_counts:
        groups = collections.defaultdict(list)
        for row in rows:
            if row['source_unit'] == source:
                groups[row['core_case']].append(row)
        for group in groups.values():
            group.sort(key=lambda r: r['case_id'])
        buckets[source] = dict(groups)
        core_counts[source] = {c: len(group) for c, group in groups.items()}
        core_used[source] = collections.Counter()
    result = []
    for position in range(1, total + 1):
        eligible = [s for s in source_counts if source_used[s] < source_counts[s]]
        source = min(eligible, key=lambda s: (
            -(position * source_counts[s] - total * source_used[s]), s))
        local_position = source_used[source] + 1
        eligible_cores = [c for c, group in buckets[source].items() if group]
        core = min(eligible_cores, key=lambda c: (
            -(local_position * core_counts[source][c]
              - source_counts[source] * core_used[source][c]), c))
        result.append(buckets[source][core].pop(0))
        source_used[source] += 1
        core_used[source][core] += 1
    return result


def main():
    provenance = json.loads((HERE / 'provenance.json').read_text(encoding='utf-8'))
    need(provenance['status'] == 'proposed_not_frozen', 'Unexpected proposal status')
    source_blobs = {}
    for name, record in provenance['sources'].items():
        data = subprocess.check_output(
            ['git', '-C', str(ROOT), 'show', provenance['source_commit'] + ':' + record['path']])
        need(sha(data) == record['sha256'], 'Source blob drift: ' + name)
        source_blobs[name] = data
    for filename, expected in provenance['artifact_sha256'].items():
        need(Path(filename).name == filename, 'Artifact must be in this input directory')
        need(sha((HERE / filename).read_bytes()) == expected, 'Input drift: ' + filename)

    train_source = read_csv(source_blobs['training_csv'])
    test_source = read_csv(source_blobs['testing_csv'])
    summary_rows = read_csv(source_blobs['summary_cases_csv'])
    summary = json.loads(source_blobs['summary_json'])
    train = read_csv((HERE / 'training-order.csv').read_bytes())
    test = read_csv((HERE / 'testing-cases.csv').read_bytes())
    selected = read_csv((HERE / 'selected-cases.csv').read_bytes())
    for name, rows, count in [('training', train, 70), ('testing', test, 30), ('selected', selected, 100)]:
        need(len(rows) == count, name + ' count mismatch')
        need(list(rows[0]) == FIELDS, name + ' fields changed or historical fields present')
        need([int(r['rank']) for r in rows] == list(range(1, count + 1)), name + ' ranks mismatch')
        need(len({r['case_id'] for r in rows}) == count, name + ' duplicate IDs')
    train_ids = [r['case_id'] for r in train]
    test_ids = [r['case_id'] for r in test]
    need(not set(train_ids) & set(test_ids), 'Training/testing overlap')
    need(set(train_ids) == {r['case_id'] for r in train_source}, 'Training membership differs from source')
    need(test_ids == [r['case_id'] for r in test_source], 'Testing membership/order differs from source')
    need(set(train_ids) == {r['case_id'] for r in summary_rows if r['group'] == 'training70'}, 'Training differs from summary')
    need(set(test_ids) == {r['case_id'] for r in summary_rows if r['group'] == 'testing30'}, 'Testing differs from summary')
    need((summary['training_cases'], summary['testing_cases'], summary['total_unique_cases']) == (70, 30, 100), 'Summary counts differ')
    need(train_ids == [r['case_id'] for r in balanced_order(train_source)], 'Deterministic order differs')

    source_map = collections.defaultdict(set)
    for row in train_source:
        source_map[row['core_case']].add(row['source_unit'])
    need(all(len(v) == 1 for v in source_map.values()), 'Ambiguous core/source mapping')
    for split_name, rows, originals in [('training', train, train_source), ('testing', test, test_source)]:
        original_by_id = {r['case_id']: r for r in originals}
        for row in rows:
            original = original_by_id[row['case_id']]
            need(row['split'] == split_name, 'Split label differs')
            need(row['source_rank'] == original['rank'], 'Source rank differs')
            need(all(row[k] == original[k] for k in ['core_case', 'runtime', 'manifest']), 'Public metadata differs')
            need(row['source_unit'] in source_map[row['core_case']], 'Coarse source label differs')
            need(row['mechanism_hint'] == row['source_unit'], 'Unexpected semantic relabeling')
            expected_batch = str((int(row['rank']) - 1) // 10 + 1) if split_name == 'training' else ''
            need(row['batch'] == expected_batch, 'Batch differs')
    combined = train + test
    need(all(all(a[k] == b[k] for k in FIELDS if k != 'rank') for a, b in zip(selected, combined)), 'Combined metadata differs')

    split = json.loads((HERE / 'evaluation-split.json').read_text(encoding='utf-8'))
    need(split['schema_version'] == 'tempoevo-incremental-split-v1', 'Unsupported official schema')
    need(split['status'] == 'proposed_not_frozen', 'Split unexpectedly frozen')
    need(split['training_case_ids'] == train_ids and split['testing_case_ids'] == test_ids, 'Registry membership/order differs')
    expected_path = (HERE / 'selected-cases.csv').relative_to(ROOT).as_posix()
    need(split['selection_file'] == expected_path, 'Selection path differs')
    need(sha((ROOT / split['selection_file']).read_bytes()) == split['selection_sha256'], 'Selection hash differs')
    nodes = list(range(0, 71, 10))
    need(split['checkpoints_processed_training_cases'] == nodes, 'Eight checkpoints differ')
    need(split['checkpoint_labels'] == ['M' + str(n) for n in nodes], 'Checkpoint labels differ')
    need(split['independence']['unseen'] is False and split['independence']['independent_holdout'] is False, 'Unsupported independence claim')
    batches = []
    for start in range(0, 70, 10):
        rows = train[start:start + 10]
        need(len(rows) == 10, 'Incomplete batch')
        batches.append({'batch': start // 10 + 1,
                        'source_groups': len({r['source_unit'] for r in rows}),
                        'core_groups': len({r['core_case'] for r in rows})})
    print(json.dumps({'status': 'metadata_validation_passed_not_runtime_qualified',
                      'proposal_status': provenance['status'], 'training': 70, 'testing': 30,
                      'unique_total': 100, 'id_overlap': 0, 'checkpoints': nodes,
                      'batches': batches, 'models_called': 0, 'graders_called': 0}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        print('VALIDATION FAILED: ' + str(exc), file=sys.stderr)
        sys.exit(1)
