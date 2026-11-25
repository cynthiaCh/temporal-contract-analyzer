"""Owner edits using the existing library and retrieval format, without review UI."""
from copy import deepcopy
from pathlib import Path
import json
import uuid

from . import compact_experience as compact, archive, taxonomy
from .core import EvidenceError, canonical, sha


def snapshot(file, value, item):
    return dict(id=item['id'], category=value.get('category', 'Uncategorized'),
                record=deepcopy(item), revision=sha(canonical(item).encode()),
                file=file.name)


def initialize(store):
    store=Path(store).expanduser().resolve()
    if not store.is_dir(): raise EvidenceError('Choose an existing directory')
    if (store/'memory.json').exists(): raise EvidenceError('Choose a categorized library, not an archive')
    with compact._locked(store):
        if not any(store.glob('*.json')):
            compact._write(store/'personal.json', dict(schema_version=compact.VERSION, category='Personal', experiences=[]))
    return listing(store)


def listing(store):
    return dict(entries=[snapshot(f, v, i) for f, v in compact.documents(store) for i in v['experiences']],
                sections=compact.SECTIONS, taxonomy=taxonomy.definition())


def history(store):
    folder=Path(store)/'.history'
    return dict(history=[dict(key=f.name, **json.loads(f.read_text(encoding='utf-8')))
                         for f in sorted(folder.glob('*.json'), reverse=True)] if folder.exists() else [])


def change(store, request):
    if request.get('action') not in ('save', 'delete'):
        raise EvidenceError('Unknown owner edit action')
    store=Path(store).expanduser().resolve()
    if not store.is_dir():
        raise EvidenceError('Choose a library directory')
    with compact._locked(store):
        values=compact.documents(store)
        matches=[(f,v,i) for f,v in values for i in v['experiences'] if i['id']==request['id']]
        match=matches[0] if matches else None
        if request.get('revision') is None:
            if match: raise EvidenceError('ID already exists')
        elif not match or snapshot(*match)['revision']!=request['revision']:
            raise EvidenceError('Experience changed outside this editor. Reload before saving.')
        if match:
            file,value,old=match
        else:
            file=store/'personal.json'
            value=next((v for f,v in values if f==file),
                       dict(schema_version=compact.VERSION, category='Personal', experiences=[]))
            old=None
        if request['action']=='delete':
            if old is None: raise EvidenceError('Experience not found')
            value['experiences'].remove(old)
        else:
            incoming=request['record']
            item=deepcopy(old) if old else dict(id=request['id'])
            for key in ['title','labels','requires','excludes']+[k for k,_ in compact.SECTIONS]:
                item[key]=incoming[key]
            # User save is authoritative. Keep the established consumer format.
            for key in ('pending_revision','proposal','evidence_ref','superseded','superseded_by'):
                item.pop(key,None)
            accepted=dict(reviewer='Library owner',decision='accept',at=archive.now())
            item['review']=accepted
            abstract=incoming.get('abstract','').strip()
            if not abstract: raise EvidenceError('Enter an Abstract for retrieval')
            item['summary']=dict(text=abstract, expert_questions=incoming.get('expert_questions','None.').strip() or 'None.',
                                 source_record=compact._bundle(file,item)[0]['sha256'], review=accepted.copy())
            compact._validate_item(file,value,item,set())
            if old is not None: value['experiences'][value['experiences'].index(old)]=item
            else: value['experiences'].append(item)
        if old is not None:
            folder=store/'.history'
            folder.mkdir(exist_ok=True)
            backup=dict(at=archive.now(), action=request['action'], **snapshot(file,value,old))
            compact._write(folder/(str(uuid.uuid4())+'.json'),backup)
        compact._write(file,value)
    return listing(store)
