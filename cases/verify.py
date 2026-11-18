"""Validate the final case snapshot and its sole 70/30 split, without model calls."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def verify():
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    split = json.loads((ROOT / 'split.json').read_text())
    selection = ROOT / 'selected_100_cases.csv'
    rows = list(csv.DictReader(selection.open()))
    assert len(rows) == 100 and len({r['case_id'] for r in rows}) == 100
    assert hashlib.sha256(selection.read_bytes()).hexdigest() == split['selection_sha256'] == manifest['selection_sha256']
    total_files = total_bytes = 0
    for role, directory, count, key in [('training', 'train70', 70, 'training_case_ids'), ('testing', 'test30', 30, 'testing_case_ids')]:
        ids = {r['case_id'] for r in rows if r['split'] == role}
        assert len(ids) == count and ids == set(split[key])
        assert {p.name for p in (ROOT / directory).iterdir() if p.is_dir()} == ids
        with (ROOT / (directory + '.csv')).open() as stream:
            ranked = list(csv.DictReader(stream))
        assert [int(r['rank']) for r in ranked] == list(range(1, count + 1))
        assert [r['case_id'] for r in ranked] == [r['case_id'] for r in rows if r['split'] == role]
    assert set(split['training_case_ids']).isdisjoint(split['testing_case_ids'])
    assert len(manifest['cases']) == 100 and {c['case_id'] for c in manifest['cases']} == {r['case_id'] for r in rows}
    for case in manifest['cases']:
        folder = ROOT / case['path']
        assert folder.resolve().parent in [ROOT / 'train70', ROOT / 'test30']
        assert json.loads((folder / 'case.json').read_text())['id'] == case['case_id']
        actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
        assert actual == {entry['path'] for entry in case['files']}
        for entry in case['files']:
            path = folder / entry['path']
            assert not path.is_symlink() and folder in path.resolve().parents
            assert path.stat().st_size == entry['bytes']
            assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256'], str(path)
            total_files += 1
            total_bytes += path.stat().st_size
    assert total_files == manifest['file_count'] and total_bytes == manifest['bytes']
    print(json.dumps(dict(valid=True,training=70,testing=30,files=total_files,bytes=total_bytes)))


if __name__ == '__main__':
    verify()
