"""Archived acceptance metadata and revocations; no editing or model dispatch."""
from contextlib import contextmanager
from copy import deepcopy
import fcntl
import json
import re
from pathlib import Path

from . import archive, experience_memory as memory
from .core import EvidenceError


def load(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


@contextmanager
def locked(store):
    with (Path(store)/'decision.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        yield


def path(store, code):
    if not isinstance(code,str) or not re.fullmatch('[a-f0-9]{64}',code):raise EvidenceError('Invalid version ID')
    return Path(store)/'workflow/versions'/(code+'.json')


def metadata(store, code):
    return load(path(store,code))


def view(store,code):
    value=metadata(store,code)
    if not value:return None
    value=deepcopy(value)
    value['content_review_available']=True
    if value.get('origin_root'):
        root=Path(value['origin_root'])
        state=load(root/'state.json',{})
        value.update(execution_authorized=False,legacy_origin_read_only=True,origin_status=state.get('status'),origin_error=state.get('error'))
    else:value['execution_authorized']=False
    return value


def _update(store,code,**fields):
    value=metadata(store,code) or dict(candidate_sha256=code)
    value.update(fields);archive.atomic_json(path(store,code),value);return value


def update(store,code,**fields):
    with locked(store):return _update(store,code,**fields)


def nonce(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}',value):
        raise EvidenceError('A stable request_id is required')
    return value


def on_decision(store,row):
    """Caller holds decision.lock. Persist intent; never start a paid task."""
    value=metadata(store,row['candidate_sha256'])
    if not value:return
    state={'accept':'content_accepted','revise':'revision_requested','reject':'rejected'}[row['decision']]
    _update(store,row['candidate_sha256'],human_decision_sha256=row['sha256'],status=state)
    if row['decision']=='revise' or row['decision']=='accept' and row.get('auto_enable') is False:
        from . import experience_approval as approval
        index=load(Path(store)/'active.json');code=row['candidate_sha256']
        current=[e for e in index['history'] if e['candidate_sha256']==code and e['action']=='activate']
        if current and current[-1]['actor'].startswith('workflow-worker:'):
            old=next(r for r in approval.decisions(store) if r['sha256']==current[-1]['source_decision_sha256'])
            _revoke_locked(store,old,row['reviewer'],'Review-only decision withdrew pending automatic enable')


def _revoke_locked(store,grant,actor,reason):
    from . import experience_approval as approval
    file=Path(store)/'workflow/revocations'/(grant['sha256']+'.json')
    if not file.exists():archive.atomic_json(file,dict(candidate_sha256=grant['candidate_sha256'],decision_sha256=grant['sha256'],actor=actor,reason=reason,at=archive.now()))
    saved=load(file);bundles={b['sha256']:b for b in memory.records(store)};rows=approval.decisions(store)
    index=approval._index(store,bundles,rows);bundle=bundles[grant['candidate_sha256']]
    if index['versions'].get(bundle['id'])==bundle['sha256']:
        approval._change(store,index,bundle,grant,'withdraw_enable',saved['actor'],saved['reason'])
    _update(store,bundle['sha256'],status='authorization_revoked',enable_blocker='Automatic enable authorization withdrawn',authorization_withdrawal=saved)
    return saved
