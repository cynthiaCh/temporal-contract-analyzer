"""Training-only immutable provisional memory. Never approves long-term records."""
from contextlib import contextmanager
import fcntl
import json
from pathlib import Path
from .core import EvidenceError,canonical,sha
from . import experience_memory as memory,taxonomy
from .experience_reflection import immutable

@contextmanager
def locked(pool):
    pool=Path(pool);pool.mkdir(parents=True,exist_ok=True)
    with (pool/'lock').open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX);yield pool

def validate_snapshot(snapshot):
    value={k:v for k,v in snapshot.items() if k!='sha256'}
    if snapshot.get('schema_version')!='online-training-snapshot-v1' or snapshot.get('sha256')!=sha(canonical(value).encode()):raise EvidenceError('Online snapshot digest mismatch')
    for row in snapshot['entries']:
        record=row['record'];bundle=row['bundle'];raw=canonical(record).encode()
        memory.validate(bundle,lambda digest:raw if digest==sha(raw) else b'')
    return snapshot

def capture(pool,root,task_id):
    pool=Path(pool)
    with locked(pool):
        entries=[]
        for p in sorted((pool/'entries').glob('*.json')):
            row=json.loads(p.read_text())
            if p.stem!=sha(canonical(row).encode()):raise EvidenceError('Online candidate digest mismatch')
            if row['origin_root']!=str(root) and row['task_id']!=task_id:entries.append(row)
    value=dict(schema_version='online-training-snapshot-v1',entries=entries)
    return validate_snapshot(dict(value,sha256=sha(canonical(value).encode())))

def append(pool,root,task_id,record):
    pool=Path(pool)
    record={k:v for k,v in record.items() if k not in ('published_sha256','published_proposal_sha256','publication_kind')}
    # Supplements add no changed guidance. Their source remains in the candidate pool.
    if record['reflection_update']['operation']=='evidence':return dict(status='evidence_only',candidate_sha256=None)
    raw=canonical(record).encode();digest=sha(raw);exp=record['experience']
    rules=[dict(id='R%02d'%i,**r) for i,r in enumerate(exp['rules'],1)]
    payload=dict(schema_version=memory.BUNDLE_VERSION_V2,id='online-'+digest[:24],version='v1',parent_sha256=None,taxonomy_version=taxonomy.VERSION,
        labels=exp['labels'],requires=exp['requires'],excludes=exp['excludes'],rules=rules,
        review=dict(status='candidate',kind='ai_assisted' if record['origin']=='success' else 'human',source_sha256=digest,limitations=exp.get('limitations',[])+['Unreviewed provisional training guidance; effectiveness unknown.']),
        audit=dict(sources=[dict(path='online-source.json',sha256=digest)],rule_links=[dict(rule_id=r['id'],source_sha256=digest,pointer='/experience/rules/'+str(i)) for i,r in enumerate(rules)],outcome_refs=[],notes=['Training-only; not approved for long-term retrieval.']))
    bundle=memory.seal(payload);memory.validate(bundle,lambda code:raw)
    row=dict(origin_root=str(root),task_id=task_id,record=record,bundle=bundle)
    code=sha(canonical(row).encode())
    with locked(pool):immutable(pool/'entries'/(code+'.json'),row)
    return dict(status='available_for_subsequent_training',candidate_sha256=bundle['sha256'],entry_sha256=code)

def usage(pool,root,attempt,selected,accepted):
    if not selected:return
    pool=Path(pool)
    row=dict(origin_root=str(root),attempt=attempt,selected_sha256s=selected,accepted=accepted,effectiveness_verified=False)
    with locked(pool):immutable(pool/'usage'/(sha(canonical(row).encode())+'.json'),row)
