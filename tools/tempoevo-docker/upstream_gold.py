"""Restore immutable unprojected originals, then call the unchanged SWE scorer.

Trusted side only. The solver sees neither this script nor benchmark internals.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile


def overlay(candidate, repository, paths):
    for name in paths:
        rel=Path(name)
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe projection path')
        target=repository/rel
        if not (candidate/rel).exists() and target.is_file():target.unlink()
    for p in candidate.rglob('*'):
        if p.is_symlink():raise ValueError('Candidate symlink')
        if p.is_file():
            target=repository/p.relative_to(candidate)
            if any(parent.is_symlink() for parent in target.parents):raise ValueError('Unsafe base parent')
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)


def main():
    sys.path.insert(0,'/opt/swe-tempoc')
    import swe_tempoc as swe
    from tempoc import upstreamagent as ua
    from tempoc import upstreamcalibrate as cal
    config=json.loads(Path('/checks/case.json').read_text())
    identity=config['case_id'];projection=config['projection']
    case,task=ua.load_task(identity)
    archive=Path('/opt/swe-tempoc/.swe-tempoc/upstream')/identity/'base.tar.gz'
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=projection['archive_sha256']:
        raise ValueError('Frozen archive mismatch')
    with tempfile.TemporaryDirectory(prefix='tca-upstream-') as temp:
        root=Path(temp);repository=root/'candidate'
        cal.extract(archive,repository)
        # Bind the projected originals too, rather than accepting a foreign source context.
        for name,digest in projection['files_sha256'].items():
            if hashlib.sha256((repository/name).read_bytes()).hexdigest()!=digest:
                raise ValueError('Projection original differs from pinned archive')
        overlay(Path(sys.argv[-1]),repository,projection['paths'])
        node='/opt/swe-tempoc/.swe-tempoc/toolchains/node-'+task['node_version']+'/bin/node'
        result=swe.score(identity,repository,root/'score',node_override=node,timeout=240)
        full=root/'score/score.json'
        print(json.dumps(dict(valid=result.get('valid_scored') is True,
            passed=result.get('verdict')=='PASS',verdict=result.get('verdict'),
            full_score=json.loads(full.read_text()) if full.exists() else result,
            error=result.get('error'))))


if __name__=='__main__':main()
