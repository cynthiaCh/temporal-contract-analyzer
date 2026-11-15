"""Declared development/test reservation. Reads IDs and selection metadata, never Gold."""
import json
from pathlib import Path
from .core import ROOT,EvidenceError,sha

REGISTRY=ROOT/'experiments/evaluation-splits.json'

def assignment(task_id):
    if not REGISTRY.exists():return None
    value=json.loads(REGISTRY.read_text())
    train=value['training_case_ids'];test=value['testing_case_ids']
    if value.get('schema_version')!='tempoevo-evaluation-split-v1' or len(train)!=25 or len(test)!=25 or len(set(train+test))!=50 or sha((ROOT/value['selection_file']).read_bytes())!=value['selection_sha256']:
        raise EvidenceError('Invalid or changed evaluation split')
    role='training' if task_id in train else 'testing' if task_id in test else None
    if role is None:return None
    return dict(role=role,registry_sha256=sha(REGISTRY.read_bytes()),independence=value['independence'],testing_policy=value['testing_policy'])

def enforce(config):
    selected=assignment(config.get('task_id'))
    if selected and selected['role']=='testing' and config['mode']!='testing':raise EvidenceError('Reserved testing case cannot run training or consume training Gold feedback')
    if selected and selected['role']=='training' and config['mode']=='testing':raise EvidenceError('Training split case cannot be an independent test')
    return selected
