"""Trusted build snapshot; actor exports contain only original public base."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile


class FrozenBenchmark:
    def __init__(self,runtime):
        receipt=Path(runtime['grader_build_inputs'])
        raw=receipt.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=runtime['grader_build_inputs_sha256']:
            raise ValueError('Grader build receipt changed')
        self.receipt=json.loads(raw);self.files={}
        with tarfile.open(receipt.parent/'benchmark-source.tar') as packed:
            for entry in packed:
                path=PurePosixPath(entry.name)
                if not entry.isfile() or path.is_absolute() or '..' in path.parts or entry.name in self.files:
                    raise ValueError('Unsafe/duplicate frozen input')
                content=packed.extractfile(entry).read()
                if hashlib.sha256(content).hexdigest()!=self.receipt['files'].get('benchmark-source/'+entry.name):
                    raise ValueError('Frozen source changed: '+entry.name)
                self.files[entry.name]=content
        expected={p.removeprefix('benchmark-source/') for p in self.receipt['files'] if p.startswith('benchmark-source/')}
        if expected!=set(self.files):raise ValueError('Incomplete frozen source archive')

    def manifest(self,case_id):
        relative=self.receipt['case_manifests'][case_id]
        return relative,json.loads(self.files[relative])

    def task(self,case_id):
        path,m=self.manifest(case_id)
        relative=m['prompt'] if m.get('schema_version')=='python-pilot-0.1' else m['diagnostic_tasks']['maintenance']['core_prompt']
        return self.files[str(PurePosixPath(path).parent/relative)].decode('utf8')

    def candidate_files(self,case_id,control=None,project=False):
        relative,m=self.manifest(case_id);root=PurePosixPath(relative).parent
        overlays=['base']
        if control=='reference':overlays.append(m.get('reference') or m['references']['bounded'])
        elif control=='negative':overlays.append(m['mutants'][0])
        elif control not in (None,'original'):raise ValueError('Unknown trusted control')
        files={};projection=None
        for overlay in overlays:
            prefix=str(root/overlay)+'/'
            selected={k[len(prefix):]:v for k,v in self.files.items() if k.startswith(prefix)}
            if not selected:raise ValueError('Empty frozen candidate/control')
            files.update(selected)
        if project and case_id.startswith('rxjs-asyncsubject-clear-latent-maintenance-port-'):
            from .swe_tempoc_inputs import project_public_files
            original,_=self.candidate_files(case_id)
            _,projection=project_public_files(original)
            files,_=project_public_files(files)
        return files,projection

    def export(self,case_id,destination,control=None,project=False):
        destination=Path(destination)
        if destination.exists():raise ValueError('Use a fresh candidate directory')
        destination.mkdir(parents=True)
        files,projection=self.candidate_files(case_id,control,project)
        for name,content in files.items():
            path=destination.joinpath(*PurePosixPath(name).parts)
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
        return projection

    def case_config(self,case_id):
        relative,m=self.manifest(case_id)
        _,projection=self.candidate_files(case_id,project=True)
        result=dict(manifest=relative,case_id=case_id)
        if projection:result['projection']=projection
        return result

    def public_config(self,case_id):
        _,m=self.manifest(case_id)
        family=('transfer_legacy' if case_id=='transfer-progress-maintenance-v2-jquery' else 'review' if case_id.startswith('review-') else 'query' if case_id.startswith('query-')
                else 'transfer' if case_id.startswith('transfer-') else 'async' if case_id.startswith('async-')
                else 'subscription' if case_id.startswith('subscription-') else 'autosave' if case_id.startswith('draft-autosave-') else None)
        if family is None:raise ValueError('No legacy behavioral public adapter for '+case_id)
        return dict(case_id=case_id,family=family,runtime=m['framework']['runtime'],
                    runtime_version=m['framework']['version'])


def public_evaluator(repo,solver_image,case_json):
    folder=Path(repo)/'tools/tempoevo-docker/public_v2'
    inputs={str(case_json):'/checks/case.json'}
    inputs.update({str(p):'/checks/public_v2/'+p.relative_to(folder).as_posix()
                   for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts})
    return dict(image=solver_image,command=['/runtime/node16/bin/node','/checks/public_v2/check.cjs'],
                inputs=inputs,seconds=180,trusted_gold_runtime=False)


def syntax_evaluator(repo,grader_image):
    """Current master construction check, with unchanged checker and semantics."""
    script=Path(repo)/'tools/tempoevo-docker/public_syntax.py'
    return dict(image=grader_image,command=['/usr/local/bin/python3','-B','/checks/public_syntax.py'],
                inputs={str(script):'/checks/public_syntax.py'},seconds=180)


def gold_evaluator(repo,grader_image,case_json,manifest,config):
    name='projected_gold.py' if config.get('projection') else 'python_gold.py' if manifest.get('schema_version')=='python-pilot-0.1' else 'gold.py'
    return dict(image=grader_image,command=['/usr/local/bin/python3','-B','/checks/gold.py'],
                inputs={str(case_json):'/checks/case.json',str(Path(repo)/'tools/tempoevo-docker'/name):'/checks/gold.py'},
                seconds=300 if config.get('projection') else 210)
