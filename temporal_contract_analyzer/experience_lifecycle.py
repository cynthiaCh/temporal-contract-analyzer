"""Persistent exact-version handoff, editing and activation. No model dispatch here."""
from contextlib import contextmanager
from copy import deepcopy
import fcntl
import json
from pathlib import Path
import re

from . import archive, experience_memory as memory
from .core import EvidenceError, canonical, sha


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
    if value.get('origin_root'):
        root=Path(value['origin_root']);auth=load(root/'execution-authorization.json')
        state=load(root/'state.json',{})
        value.update(execution_authorized=bool(auth and not auth.get('cancelled')),origin_status=state.get('status'),origin_error=state.get('error'))
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


def edit(store,code,request):
    memory.object_fields(request,{'request_id','actor','reason','rules','labels','requires','excludes'},'human edit')
    nonce(request['request_id'])
    if not memory.text(request['actor']) or not memory.text(request['reason']):
        raise EvidenceError('Editing requires the actual editor name and reason')
    store=Path(store);binding=dict(parent_sha256=code,**request)
    with locked(store):
        receipt_path=store/'workflow/edit-requests'/(request['request_id']+'.json')
        old=load(receipt_path)
        if old is not None:
            if old['request']!=binding:raise EvidenceError('Edit request_id reused with different content')
            return next(b for b in memory.records(store) if b['sha256']==old['candidate_sha256'])
        parent=next((b for b in memory.records(store) if b['sha256']==code),None)
        if parent is None:raise EvidenceError('Unknown edit parent')
        if not isinstance(request['rules'],list) or [r.get('id') for r in request['rules'] if isinstance(r,dict)]!=[r['id'] for r in parent['rules']]:
            raise EvidenceError('This editor preserves rule IDs/count; edit bodies and categories, not a merge workbench')
        if all(request[k]==parent[k] for k in ('rules','labels','requires','excludes')):
            raise EvidenceError('No rule or applicability changes to save')
        evidence=dict(binding,kind='manual_revision',changed_rule_ids=[r['id'] for i,r in enumerate(request['rules']) if r!=parent['rules'][i]])
        raw=(json.dumps(evidence,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode();digest=sha(raw)
        evidence_path=store/'workflow/edits'/(request['request_id']+'.json')
        payload={k:deepcopy(v) for k,v in parent.items() if k in memory.FIELDS}
        payload.update(schema_version=memory.BUNDLE_VERSION_V2,version='edit-'+request['request_id'],parent_sha256=code,
            **{k:deepcopy(request[k]) for k in ('rules','labels','requires','excludes')})
        payload['review']=dict(status='candidate',kind='human',source_sha256=digest,
            limitations=['Human edit proposal, not acceptance; AI check and fresh exact-version effects pending.'])
        payload['audit']['sources'].append(dict(path=str(evidence_path),sha256=digest))
        payload['audit']['outcome_refs']=[]
        payload['audit']['notes'].append('Edited by '+request['actor']+': '+request['reason'])
        sealed=memory.seal(payload)
        memory.validate(sealed,lambda key:raw if key==digest else (store/'sources'/key).read_bytes())
        evidence_path.parent.mkdir(parents=True,exist_ok=True)
        if evidence_path.exists() and evidence_path.read_bytes()!=raw:raise EvidenceError('Immutable edit evidence conflicts')
        if not evidence_path.exists():
            from .experience_submission import publish
            publish(evidence_path,raw)
        existing=next((b for b in memory.records(store) if b['sha256']==sealed['sha256']),None)
        bundle=existing or memory.add(store,payload,[evidence_path])
        origin=metadata(store,code) or {}
        _update(store,bundle['sha256'],origin_root=origin.get('origin_root'),generation=origin.get('generation',0)+1,
            ai_status='pending',status='ai_check_pending' if origin.get('origin_root') else 'execution_not_authorized',
            edit=dict(actor=request['actor'],reason=request['reason'],request_id=request['request_id']),
            validation_job=None,validation_status='not_started')
        archive.atomic_json(receipt_path,dict(request=binding,candidate_sha256=bundle['sha256']))
        return bundle


def check_human_acceptance(store,code,request):
    value=metadata(store,code)
    if value and request['decision']=='accept' and value.get('ai_status')!='passed':
        raise EvidenceError('This exact edited/generated version needs its AI check before content acceptance; run an authorized worker')


def on_decision(store,row):
    """Caller holds decision.lock. Persist intent; never start a paid task."""
    value=metadata(store,row['candidate_sha256'])
    if not value:return
    state={'accept':'content_accepted_waiting_validation','revise':'revision_requested','reject':'rejected'}[row['decision']]
    _update(store,row['candidate_sha256'],human_decision_sha256=row['sha256'],status=state)
    if row['decision']=='revise' or row['decision']=='accept' and row.get('auto_enable') is False:
        from . import experience_approval as approval
        index=load(Path(store)/'active.json');code=row['candidate_sha256']
        current=[e for e in index['history'] if e['candidate_sha256']==code and e['action']=='activate']
        if current and current[-1]['actor'].startswith('workflow-worker:'):
            old=next(r for r in approval.decisions(store) if r['sha256']==current[-1]['source_decision_sha256'])
            _revoke_locked(store,old,row['reviewer'],'Review-only decision withdrew pending automatic enable')


def latest_acceptance(store,code):
    from . import experience_approval as approval
    rows=[r for r in approval.decisions(store) if r['candidate_sha256']==code]
    return rows[-1] if rows and rows[-1]['decision']=='accept' else None


def validation_finished(store,code,status,**fields):
    from . import experience_approval as approval
    with locked(store):
        rows=[r for r in approval.decisions(store) if r['candidate_sha256']==code]
        last=rows[-1] if rows else None
        state='awaiting_human_review' if last is None else {'reject':'rejected','revise':'revision_requested','accept':'content_accepted_validation_'+status}[last['decision']]
        return _update(store,code,validation_status=status,status=state,**fields)


def cancel(root):
    """Serialize stopping future execution with the final enable decision."""
    root=Path(root);protocol=load(root/'protocol.json')
    with locked(protocol['store']):
        file=root/'execution-authorization.json';auth=load(file)
        if not auth:raise EvidenceError('No execution authorization to cancel')
        auth['cancelled']=True;archive.atomic_json(file,auth)
        state=load(root/'state.json');state['status']='cancelled'
        archive.atomic_json(root/'state.json',state)
        return state


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


def revoke(store,code,request):
    memory.object_fields(request,{'actor','reason'},'authorization withdrawal')
    if not memory.text(request['actor']) or not isinstance(request['reason'],str):raise EvidenceError('Actual revoking operator is required')
    with locked(store):
        grant=latest_acceptance(store,code)
        if not grant or not grant.get('enable_authorization',{}).get('authorized'):raise EvidenceError('No current automatic enable authorization')
        return _revoke_locked(store,grant,request['actor'],request['reason'])


def maybe_enable(store,code,technical_actor):
    from . import experience_approval as approval, experience_screening as screening
    with locked(store):
        value=metadata(store,code) or {}
        rows=approval.decisions(store);selected=[r for r in rows if r['candidate_sha256']==code]
        row=selected[-1] if selected else None
        reason=None
        auth=load(Path(value['origin_root'])/'execution-authorization.json') if value.get('origin_root') else None
        if not auth or auth.get('cancelled'):reason='Workflow execution authorization missing or cancelled'
        elif not row or row['decision']!='accept':reason='No latest exact-version human acceptance'
        elif not row.get('enable_authorization',{}).get('authorized'):reason='Review-only or automatic enable authorization revoked'
        elif (Path(store)/'workflow/revocations'/(row['sha256']+'.json')).exists():reason='Automatic enable authorization withdrawn'
        elif value.get('ai_status')!='passed':reason='Exact-version AI check not passed'
        elif value.get('validation_status')!='passed' or not screening.qualified(store,code):reason='Exact-version effect validation not passed'
        if reason:
            status='cancelled' if auth and auth.get('cancelled') else 'awaiting_human_review' if not row else 'rejected' if row['decision']=='reject' else 'revision_requested' if row['decision']=='revise' else 'authorization_revoked' if 'withdrawn' in reason else value.get('status','waiting_enable_conditions')
            _update(store,code,enable_blocker=reason,status=status);return dict(enabled=False,reason=reason)
        bundles={b['sha256']:b for b in memory.records(store)};bundle=bundles[code]
        index=approval._index(store,bundles,rows);current=index['versions'].get(bundle['id'])
        if current==code:
            _update(store,code,status='enabled',enable_blocker=None);return dict(enabled=True,already_enabled=True)
        if current!=row['enable_authorization']['expected_current']:
            reason='Active version changed since human authorization'
            _update(store,code,status='waiting_enable_conditions',enable_blocker=reason);return dict(enabled=False,reason=reason)
        if current is not None and not approval._descendant(bundles,code,current):
            reason='Automatic enable cannot select an incompatible branch'
            _update(store,code,status='waiting_enable_conditions',enable_blocker=reason);return dict(enabled=False,reason=reason)
        approval._change(store,index,bundle,row,'activate',technical_actor,
            'Automatic execution of exact-version enable authorization by '+row['reviewer'])
        _update(store,code,status='enabled',enable_blocker=None,enabled_by=technical_actor,authorized_by=row['reviewer'])
        return dict(enabled=True,already_enabled=False)
