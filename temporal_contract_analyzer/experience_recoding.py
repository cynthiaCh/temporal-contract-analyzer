"""Validate explicit source-reviewed label annotations; never infer from legacy IDs."""
from copy import deepcopy
import json
from pathlib import Path

from . import taxonomy, experience_memory as memory
from .core import EvidenceError, sha


def _candidate(store, parent_sha256, review_path, version, install=True):
    """Create an unactivated taxonomy-only child from a supplied AI audit sheet."""
    parent=next((b for b in memory.records(store) if b['sha256']==parent_sha256),None)
    if parent is None:raise EvidenceError('Unknown recoding parent')
    review_path=Path(review_path).resolve()
    review=json.loads(review_path.read_text(encoding='utf-8'))
    memory.object_fields(review,{'schema_version','taxonomy_version','taxonomy_sha256','parent_sha256',
        'body_sha256','reviewer','AI_assisted','independent_human_approval','scope','sources','rules',
        'unassigned_labels','limitations'},'source label review')
    if review['schema_version']!='experience-source-label-review-v1' \
            or review['taxonomy_version']!=taxonomy.VERSION or review['taxonomy_sha256']!=taxonomy.fingerprint() \
            or review['parent_sha256']!=parent_sha256 or review['body_sha256']!=parent['body_sha256'] \
            or review['AI_assisted'] is not True or review['independent_human_approval'] is not False \
            or review['scope']!='taxonomy_only_no_policy_or_effect_claim' or not memory.text(review['reviewer']):
        raise EvidenceError('Label review identity, scope or taxonomy mismatch')
    memory.strings(review['limitations'],'review limitations')
    if not isinstance(review['sources'],list) or not review['sources']:
        raise EvidenceError('Missing visible source inputs')
    sources={}
    for source in review['sources']:
        memory.object_fields(source,{'file','sha256','kind'},'label source')
        if source['kind'] not in ('original_task','visible_document','original_source'):
            raise EvidenceError('Classification may only use original task and candidate-visible material')
        path=Path(source['file']);raw=path.read_bytes()
        if sha(raw)!=source['sha256'] or str(path) in sources:
            raise EvidenceError('Duplicate or changed classification source')
        sources[str(path)]=(source,raw.decode('utf-8').splitlines())
    rules=review['rules']
    if not isinstance(rules,list) or len(rules)!=len(parent['rules']):
        raise EvidenceError('Review every original rule, without adding or removing one')
    labels=set()
    for rule, original in zip(rules,parent['rules']):
        memory.object_fields(rule,{'rule_id','body_sha256','labels','notes'},'rule label review')
        if rule['rule_id']!=original['id'] or rule['body_sha256']!=memory.digest(original['body']):
            raise EvidenceError('Rule order or body binding changed')
        memory.strings(rule['notes'],'rule notes')
        if not isinstance(rule['labels'],list):raise EvidenceError('Rule labels must be a list')
        codes=[]
        for label in rule['labels']:
            memory.object_fields(label,{'code','basis','reason','evidence'},'label finding')
            if label['basis'] not in ('documented_requirement','source_fact','preservation_inference') \
                    or not memory.text(label['reason']) or not isinstance(label['evidence'],list) or not label['evidence']:
                raise EvidenceError('A label needs reasoning and original source evidence')
            codes.append(label['code'])
            for anchor in label['evidence']:
                memory.object_fields(anchor,{'file','sha256','line','quote'},'label source anchor')
                if anchor['file'] not in sources or type(anchor['line']) is not int \
                        or not isinstance(anchor['quote'],str) or not 1<=len(anchor['quote'])<=160:
                    raise EvidenceError('Invalid label source anchor')
                source,lines=sources[anchor['file']]
                if anchor['sha256']!=source['sha256'] or not 1<=anchor['line']<=len(lines) \
                        or anchor['quote'] not in lines[anchor['line']-1]:
                    raise EvidenceError('Label citation does not match its frozen source line')
        labels.update(taxonomy.labels(codes))
    aggregate=taxonomy.labels(list(labels),allow_empty=False)
    omitted=review['unassigned_labels']
    if not isinstance(omitted,list):raise EvidenceError('Record why remaining labels are not established')
    remaining=[]
    for item in omitted:
        memory.object_fields(item,{'code','reason'},'unassigned label')
        if not memory.text(item['reason']):raise EvidenceError('Missing unassigned-label reason')
        remaining.append(item['code'])
    taxonomy.labels(remaining)
    if set(remaining)!=set(taxonomy.CODES)-labels:
        raise EvidenceError('Assigned and unassigned labels must partition the codebook')
    result=deepcopy(parent)
    for key in ('sha256','body_sha256'):result.pop(key)
    code=sha(review_path.read_bytes())
    result.update(version=version,parent_sha256=parent_sha256,taxonomy_version=taxonomy.VERSION,labels=aggregate)
    result['review']=dict(status='candidate',kind='ai_assisted',source_sha256=code,
        limitations=list(dict.fromkeys(parent['review']['limitations']+review['limitations']+[
            'Source-reviewed taxonomy recoding only; pending real expert acceptance.',
            'No new behavior replay or repair-effect evidence is created by recoding.'])))
    extra=[dict(path=str(review_path),sha256=code)]+[
        dict(path=source['file'],sha256=source['sha256']) for source in review['sources']]
    for source in extra:
        if source not in result['audit']['sources']:result['audit']['sources'].append(source)
    result['audit']['rule_links'] += [dict(rule_id=r['rule_id'],source_sha256=code,pointer=f'/rules/{i}')
                                    for i,r in enumerate(rules)]
    result['audit']['notes'] += ['Explicit per-rule source-based seven-label recoding, not a T1-T4 lookup.',
        'Rule text and applicability unchanged; labels and provenance are program-composed from an AI audit.']
    sealed=memory.seal(result)
    pending={s['sha256']:Path(s['path']).read_bytes() for s in extra}
    memory.validate(sealed,lambda digest:pending[digest] if digest in pending else (Path(store)/'sources'/digest).read_bytes())
    if sealed['rules']!=parent['rules'] or any(sealed[k]!=parent[k] for k in ('requires','excludes','body_sha256')):
        raise EvidenceError('Taxonomy recoding changed guidance or applicability')
    if not install:return sealed
    return memory.add(store,sealed,[s['path'] for s in extra])


def candidate(store,parent_sha256,review_path,version,install=True):
    try:return _candidate(store,parent_sha256,review_path,version,install)
    except EvidenceError:raise
    except (KeyError,TypeError,IndexError,AttributeError) as error:
        raise EvidenceError('Malformed source annotation; candidate not completed') from error
