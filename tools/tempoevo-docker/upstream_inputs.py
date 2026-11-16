"""Bounded public RxJS source projection from the pinned original archive.

No trusted tests, reference patch or scorer is read into the projection.
Unprojected original files are restored by the trusted grader, not the Agent.
"""
import json
import subprocess
from pathlib import Path
from temporal_contract_analyzer.core import EvidenceError, sha

SCRIPT = r'''
import hashlib,json,tarfile
from pathlib import PurePosixPath
p='/opt/swe-tempoc/.swe-tempoc/upstream/rxjs-asyncsubject-clear-latent-maintenance/base.tar.gz'
with open(p,'rb') as f: archive_sha=hashlib.sha256(f.read()).hexdigest()
files={}
with tarfile.open(p) as t:
 for member in t:
  parts=PurePosixPath(member.name).parts
  name='/'.join(parts[1:])
  if not member.isfile() or '..' in parts:continue
  if name.startswith('src/') or name in ['README.md','package.json','tsconfig.json','spec/subjects/AsyncSubject-spec.ts','spec/Subject-spec.ts']:
   files[name]=t.extractfile(member).read().decode('utf-8')
print(json.dumps(dict(archive_sha256=archive_sha,files=files)))
'''


def load(case_id, root, row, manifest_path, manifest, image, destination):
    if case_id != 'rxjs-asyncsubject-clear-latent-maintenance':
        raise EvidenceError('No public projection adapter for this upstream task')
    command=['docker','run','--rm','--pull=never','--network','none','--read-only',
             '--entrypoint','python3',image,'-c',SCRIPT]
    run=subprocess.run(command,capture_output=True,text=True,timeout=60)
    if run.returncode:raise EvidenceError('Public source extraction failed: '+run.stderr[-1000:])
    value=json.loads(run.stdout)
    if value['archive_sha256']!=manifest['archive_sha256']:
        raise EvidenceError('Pinned upstream source archive differs from public task identity')
    files=value['files']
    if 'src/internal/AsyncSubject.ts' not in files:raise EvidenceError('Projection misses target product source')
    from temporal_contract_analyzer.candidate_files import write_files
    write_files(destination,{k:v.encode() for k,v in files.items()})
    prompt_path=manifest_path.parent/manifest['prompt']
    raw=prompt_path.read_bytes()
    projection=dict(kind='original_archive_public_projection_v1',archive_sha256=value['archive_sha256'],
        paths=sorted(files),files_sha256={k:sha(v.encode()) for k,v in files.items()},
        scope='All original src/** plus named public tests and root documents; unprojected original files remain frozen during scoring.',
        local_dependency_limit='Public original sources are provided; full upstream npm dependencies are only available in the trusted grader.')
    return dict(candidate=str(destination),task=raw.decode(),label=case_id,
        case_record=dict(id=case_id,manifest=row['manifest'],source='swe-tempoc',
            condition='latent-maintenance',authorization='ungranted',prompt_sha256=sha(raw),
            source_manifest_sha256=sha(manifest_path.read_bytes()),projection=projection))
