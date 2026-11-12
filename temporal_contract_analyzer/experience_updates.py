"""One evidence-linked delta; deterministic composition, never policy generation."""
from copy import deepcopy

from . import experience_memory as memory, taxonomy
from .core import EvidenceError
from ._session_runtime.schema_validator import validate


def schema(visible, ledger, parents):
    def array(values, nullable=False):
        values=list(values)
        result=dict(type=['array','null'] if nullable else 'array',items=dict(type='string'))
        if values:result['items']['enum']=values
        else:result['maxItems']=0
        return result
    fields = dict(action=dict(type='string', enum=['no_update', 'new', 'revise']),
        reason=dict(type='string', minLength=1), basis=array(ledger),
        parent_sha256=dict(type=['string', 'null'], enum=[None]+list(parents)),
        labels=array([v['code'] for v in visible['analysis']['obligation_labels']], True),
        requires=array([f['predicate'] for f in visible['analysis']['facts'] if f['state']=='known'], True),
        excludes=array([f['predicate'] for f in visible['analysis']['facts'] if f['state']=='contradicted'], True),
        changes=dict(type='array', maxItems=16, items=dict(type='object', properties=dict(
            operation=dict(type='string', enum=['add', 'replace', 'remove']),
            rule_id=dict(type=['string', 'null']),
            category=dict(type=['string', 'null'], enum=[None]+list(memory.CATEGORIES)),
            body=dict(type=['string', 'null'], maxLength=2400), support=array(ledger),
            causal_status=dict(type='string', enum=['documented_relation', 'observed_relation', 'hypothesis', 'unknown'])),
            required=['operation','rule_id','category','body','support','causal_status'], additionalProperties=False)),
        unresolved=dict(type='array', items=dict(type='string')))
    # Match the existing composition contract in the actual structured output:
    # new IDs are assigned by Python; replace/remove identify parent rules.
    item=fields['changes']['items'];branches=[]
    parent_ids=sorted({r['id'] for parent in parents.values() for r in parent['rules']})
    for operation in ('add','replace','remove'):
        if operation!='add' and not parent_ids:continue
        branch=deepcopy(item);props=branch['properties']
        props['operation']=dict(type='string',enum=[operation])
        props['rule_id']=dict(type='null') if operation=='add' else dict(type='string',enum=parent_ids)
        if operation=='remove':
            props['category']=dict(type='null');props['body']=dict(type='null')
        else:
            props['category']=dict(type='string',enum=list(memory.CATEGORIES))
            props['body']=dict(type='string',minLength=1,maxLength=2400)
        branches.append(branch)
    fields['changes']['items']=dict(anyOf=branches)
    return dict(type='object', properties=fields, required=list(fields), additionalProperties=False)


def compose(value, visible, ledger, parents):
    """Return one composed rule list and its exact origin pointers, or None."""
    try:
        validate(value, schema(visible, ledger, parents))
    except (ValueError, KeyError, TypeError) as error:
        raise EvidenceError('Invalid reflection output: '+str(error)) from error
    if not value['basis']:
        raise EvidenceError('Extraction needs traceable basis IDs')
    if value['action'] == 'no_update':
        if value['changes'] or any(value[k] is not None for k in ('parent_sha256','labels','requires','excludes')):
            raise EvidenceError('no_update cannot carry a hidden change')
        return None
    parent = parents.get(value['parent_sha256'])
    if (value['action'] == 'new' and (value['parent_sha256'] is not None or not value['changes'])) \
            or (value['action'] == 'revise' and parent is None):
        raise EvidenceError('One new candidate or one exact parent revision is required')
    if not any(ledger[k]['kind'] in ('original_task','source_document') for k in value['basis']):
        raise EvidenceError('Candidate changes need task/source support, not prior rules or observations alone')
    items = [(deepcopy(r), dict(parent_index=i)) for i,r in enumerate(parent['rules'])] if parent else []
    touched = set()
    for index, change in enumerate(value['changes']):
        op, code = change['operation'], change['rule_id']
        if not change['support'] or len(set(change['support'])) != len(change['support']):
            raise EvidenceError('Each change needs existing evidence IDs without duplicates')
        if not any(ledger[k]['kind'] in ('original_task', 'source_document')
                   for k in change['support']):
            raise EvidenceError('Observations alone do not establish a normative policy')
        if op == 'remove':
            if change['body'] is not None or change['category'] is not None:
                raise EvidenceError('Removal cannot also introduce text')
        elif not memory.text(change['body']) or change['category'] not in memory.CATEGORIES:
            raise EvidenceError('Added or replaced rules need their single original body')
        if op == 'add':
            if code is not None:
                raise EvidenceError('New rule numbering is program-owned')
            items.append((dict(id=None, category=change['category'], body=change['body']), dict(change_index=index)))
        else:
            if code in touched or code is None:
                raise EvidenceError('Conflicting or unbound rule delta')
            matches = [i for i,(r,_) in enumerate(items) if r['id']==code]
            if len(matches) != 1:
                raise EvidenceError('Rule delta does not identify an existing parent rule')
            touched.add(code)
            at = matches[0]
            if op == 'remove':
                items.pop(at)
            else:
                items[at] = (dict(id=code,category=change['category'],body=change['body']),dict(change_index=index))
    if not items:
        raise EvidenceError('A candidate cannot remove all guidance')
    if len({(r['category'],r['body']) for r,_ in items})!=len(items):
        raise EvidenceError('Duplicate rule text is not an incremental update')
    rules, origins = [], []
    for i,(rule, origin) in enumerate(items,1):
        rules.append(dict(rule,id=f'R{i:02d}'))
        origins.append(origin)
    result = dict(rules=rules, origins=origins, parent=parent)
    for key in ('labels','requires','excludes'):
        result[key] = deepcopy(value[key] if value[key] is not None else parent[key] if parent else [])
        memory.strings(result[key], key, taxonomy.CODES if key=='labels' else taxonomy.definition()['mechanism_predicates'],
                       nonempty=key in ('labels','requires'))
    if set(result['requires']) & set(result['excludes']):
        raise EvidenceError('Conflicting applicability')
    if parent and result['rules']==parent['rules'] and all(set(result[k])==set(parent[k]) for k in ('labels','requires','excludes')):
        raise EvidenceError('Duplicate candidate: no actual incremental change')
    if not parent and any(result['rules']==b['rules'] and all(set(result[k])==set(b[k]) for k in ('labels','requires','excludes'))
                          for b in parents.values()):
        raise EvidenceError('An exact existing experience is not a new learned update')
    return result


def recover_program_numbering(value, visible, ledger, parents):
    """Explicit derived repair for a complete legacy new-only proposal.

    No rule text/policy is edited. An existing canonical hint may be discarded
    only when it equals the ID Python independently assigns at that position.
    Parent revisions and ambiguous references are never guessed.
    """
    if value.get('action')!='new' or value.get('parent_sha256') is not None:
        raise EvidenceError('Numbering recovery supports new proposals only; revisions need explicit rule identities')
    derived=deepcopy(value);changes=[]
    for index,change in enumerate(derived.get('changes',[]),1):
        if change.get('operation')!='add':raise EvidenceError('Numbering recovery cannot retarget a rule operation')
        code=change.get('rule_id');canonical=f'R{index:02d}'
        if code is not None:
            if code!=canonical:raise EvidenceError('Ambiguous model rule numbering cannot be recovered')
            changes.append(dict(pointer=f'/changes/{index-1}/rule_id',before=code,after=None,assigned_by_python=canonical))
            change['rule_id']=None
    if not changes:raise EvidenceError('No legacy numbering conflict to recover')
    composed=compose(derived,visible,ledger,parents)
    return derived,composed,dict(schema_version='program-numbering-recovery-v1',changes=changes,
        body_unchanged=[r['body'] for r in value['changes']]==[r['body'] for r in derived['changes']],
        applicability_unchanged=all(value[k]==derived[k] for k in ('labels','requires','excludes')),
        original_output_preserved=True,semantic_review='not_performed')


def route_view(visible, bundles):
    """Same router over a controlled prospective view; not expert activation."""
    from . import experience_routing as routing
    memory.object_fields(visible,{'task','sources','analysis','review'},'candidate-visible routing input')
    entries = [(routing.freeze_entry(memory.render(b), b['labels'], b['requires'], b['excludes'], b['version']), b)
               for b in bundles if b['taxonomy_version']==taxonomy.VERSION]
    decision = routing.route(visible['analysis'], visible['sources'], [e for e,_ in entries],
                             task=visible['task'], review=visible['review'])
    selected = next((b for e,b in entries if decision['selected'] and e['sha256']==decision['selected']['sha256']), None)
    return dict(route=decision, selected_sha256=None if selected is None else selected['sha256'],
                experience_text=None if selected is None else memory.render(selected))


def new_view(old, candidate):
    """A revision replaces its identity; independent additions retain real conflicts."""
    return [b for b in old if b['id'] != candidate['id']] + [candidate]
