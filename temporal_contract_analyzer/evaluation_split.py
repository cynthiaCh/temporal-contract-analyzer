"""Declared development/test reservation. Reads IDs and selection metadata, never Gold."""
import json
from pathlib import Path
from .core import ROOT,EvidenceError,sha

REGISTRY=ROOT/'experiments/evaluation-splits.json'

def assignment(task_id, registry=None):
    registry=Path(registry).resolve() if registry else REGISTRY
    if not registry.exists():
        if registry!=REGISTRY:raise EvidenceError('Missing explicit evaluation split')
        return None
    value=json.loads(registry.read_text())
    train=value['training_case_ids'];test=value['testing_case_ids']
    version=value.get('schema_version')
    expected=(25,25) if version=='tempoevo-evaluation-split-v1' else (70,30) if version=='tempoevo-incremental-split-v1' else None
    if expected is None or (len(train),len(test))!=expected or len(set(train+test))!=sum(expected) or sha((ROOT/value['selection_file']).read_bytes())!=value['selection_sha256']:
        raise EvidenceError('Invalid or changed evaluation split')
    role='training' if task_id in train else 'testing' if task_id in test else None
    if role is None:return None
    return dict(role=role,registry_sha256=sha(registry.read_bytes()),independence=value['independence'],testing_policy=value['testing_policy'])

def enforce(config):
    purpose=config.get('evaluation_purpose')
    if purpose not in (None,'training_replay'):raise EvidenceError('Unknown evaluation purpose')
    selected=assignment(config.get('task_id'),config.get('evaluation_split_file'))
    if config.get('evaluation_split_file') and selected is None:raise EvidenceError('Case absent from explicit evaluation split')
    if config.get('evaluation_split') is not None and config['evaluation_split']!=selected:raise EvidenceError('Frozen evaluation split changed')
    if selected and selected['role']=='testing' and config['mode']!='testing':raise EvidenceError('Reserved testing case cannot run training or consume training Gold feedback')
    if purpose=='training_replay':
        if not selected or selected['role']!='training' or config['mode']!='testing' or config.get('learning_policy')!='frozen':
            raise EvidenceError('Training replay requires a declared training case and frozen testing')
        if config.get('max_attempts',1)!=1 or any(config.get(k) for k in ('training_evaluator','training_recipe','training_feedback','online_memory')):
            raise EvidenceError('Training replay cannot consume training feedback or update experience')
    if selected and selected['role']=='training' and config['mode']=='testing' and purpose!='training_replay':raise EvidenceError('Training split case cannot be an independent test')
    return selected
