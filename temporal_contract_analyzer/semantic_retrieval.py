"""Public-evidence applicability assessment and bounded diverse delivery.

Model assessments are fallible relevance judgments, never behavioral scores.
The frozen approved bank and deterministic mechanism gate remain prerequisites.
"""
from . import experience_memory as memory
from .core import EvidenceError

VERSION = 'evidence-semantic-retrieval-v1'
MAX_CANDIDATES = 20
MAX_EXPERIENCES = 5
MAX_CHARACTERS = 16000


def recall(task, sources, analysis, bundles):
    from .experience_updates import route_view
    from .experience_routing import input_digest
    review=dict(input_sha256=input_digest(analysis,task,sources),reviewer='unreviewed_model_analysis',approved=False,
        blocking_issues=[],scope_unknowns=[],evidence=[],reason='Source-bound mechanism recall; not semantic admission.')
    preliminary=route_view(dict(task=task,sources=sources,analysis=analysis,review=review),bundles,max_experiences=max(1,len(bundles)))
    eligible=set(preliminary['selected_sha256s'])
    query='\n'.join([task,analysis['contract']]+[x['statement'] for x in analysis['obligation_labels']])
    corpus=[b for b in bundles if b['sha256'] in eligible]
    hits=memory.search_records(corpus,query,limit=100,include_all=True)['results'] if corpus else []
    scores={h['sha256']:h['score'] for h in hits}
    by_sha={b['sha256']:b for b in bundles}
    # Mechanism filtering precedes text ranking. Lexical zero alone never proves inapplicability.
    codes=sorted(eligible,key=lambda code:(-scores.get(code,0),code))[:MAX_CANDIDATES]
    candidates=[dict(sha256=code,id=by_sha[code]['id'],text=memory.render(by_sha[code]),
                     lexical_score=scores.get(code,0)) for code in codes]
    return dict(schema_version=VERSION,mechanism_route=preliminary['route'],
        eligible_count=len(eligible),candidates=candidates,
        omitted_candidate_sha256s=sorted(eligible-set(codes)),
        max_experiences=MAX_EXPERIENCES,max_characters=MAX_CHARACTERS)


def schema(candidates,analysis):
    def obj(props):return dict(type='object',properties=props,required=list(props),additionalProperties=False)
    string=dict(type='string',minLength=1)
    evidence=dict(type='array',items=obj(dict(file=string,quote=string)))
    codes=[c['sha256'] for c in candidates]
    obligations=['O'+str(n) for n,_ in enumerate(analysis['obligation_labels'],1)]
    row=obj(dict(sha256=dict(type='string',enum=codes),
        relevance=dict(type='string',enum=['direct','transferable','weak','not_applicable','unknown']),
        premises=dict(type='array',minItems=1,items=obj(dict(condition=string,
            status=dict(type='string',enum=['supported','contradicted','unknown']),evidence=evidence))),
        object_mapping=string,contribution=string,
        covered_obligations=dict(type='array',items=dict(type='string',enum=obligations)),
        supporting_evidence=evidence,
        redundant_with=dict(type='array',items=dict(type='string',enum=codes)),
        reason=string))
    return obj(dict(assessments=dict(type='array',minItems=len(codes),maxItems=len(codes),items=row)))


def payload(task,sources,ast,analysis,recall_result):
    return dict(task=task,sources=sources,ast=ast,analysis=analysis,
        obligations=[dict(id='O'+str(n),text=x['statement']) for n,x in enumerate(analysis['obligation_labels'],1)],
        candidates=recall_result['candidates'],schema=schema(recall_result['candidates'],analysis),
        instruction='Assess EVERY supplied experience against the original public task and source. '
        'Labels and generic facts such as asynchronous callbacks, ownership or reentry are insufficient. '
        'Read the full applicability, exclusions, preservation and proposed rules. List all material scenario prerequisites, '
        'including domain-specific operations such as retained audit/history, decoding, save completion, or query cancellation. '
        'Mark a missing premise unknown, or contradicted if publicly disproved; do not invent evidence to fill it. '
        'Do not apply progress audit rules to saving or queries just because lifecycle labels overlap. '
        'Cross-domain transfer is allowed ONLY with an explicit mapping of source operations/owners to the current code '
        'and source-supported obligations. Explain the concrete repair contribution and cite exact original public quotes. '
        'For direct/transferable require all material premises supported, nonempty source evidence and covered obligation IDs. '
        'Mark weak topical similarity weak; do not fill a five-entry quota. Identify genuinely redundant guidance using redundant_with. '
        'Unknown relevance is preferable to an unsupported analogy. This is relevance assessment, not effectiveness verification. '
        'Experience never establishes new task obligations. Return one assessment per candidate, including rejected candidates.')


def select(result,recall_result,analysis,task,sources,bundles):
    from ._session_runtime.schema_validator import validate
    from .tempoevo_v4 import evidence_valid
    validate(result,schema(recall_result['candidates'],analysis))
    candidates={c['sha256']:c for c in recall_result['candidates']}
    rows=result['assessments'];codes=[r['sha256'] for r in rows]
    if len(set(codes))!=len(codes) or set(codes)!=set(candidates):
        raise EvidenceError('Semantic assessment must cover each recalled candidate exactly once')
    accepted=[];decisions=[]
    for row in rows:
        for premise in row['premises']:
            evidence_valid(premise['evidence'],task,sources)
        evidence_valid(row['supporting_evidence'],task,sources)
        if row['sha256'] in row['redundant_with']:raise EvidenceError('Experience cannot duplicate itself')
        supported=all(p['status']=='supported' and p['evidence'] for p in row['premises'])
        applicable=row['relevance'] in ('direct','transferable') and supported and bool(row['supporting_evidence']) and bool(row['covered_obligations'])
        decisions.append(dict(row,admitted=bool(applicable),selection_reason='eligible' if applicable else 'unsupported_or_irrelevant'))
        if applicable:accepted.append(row)
    selected=[];covered=set();used_characters=0
    by_sha={b['sha256']:b for b in bundles}
    while accepted and len(selected)<MAX_EXPERIENCES:
        accepted.sort(key=lambda row:(-len(set(row['covered_obligations'])-covered),
            row['relevance']!='direct',-candidates[row['sha256']]['lexical_score'],row['sha256']))
        row=accepted.pop(0);code=row['sha256'];chosen={r['sha256'] for r in selected}
        redundant=bool(chosen & set(row['redundant_with'])) or any(code in r['redundant_with'] for r in selected)
        terms=set(memory._terms(candidates[code]['text']))
        for previous in selected:
            other=set(memory._terms(candidates[previous['sha256']]['text']))
            if terms and len(terms & other)/len(terms | other)>=.85:redundant=True
        decision=next(d for d in decisions if d['sha256']==code)
        if redundant:decision['selection_reason']='redundant';continue
        size=len(memory.delivery_text([by_sha[r['sha256']] for r in selected+[row]]) or '')
        if size>MAX_CHARACTERS:decision['selection_reason']='text_budget';continue
        selected.append(row);covered.update(row['covered_obligations']);used_characters=size;decision['selection_reason']='selected'
    for d in decisions:
        if d['selection_reason']=='eligible':d['selection_reason']='entry_limit'
    selected_bundles=[by_sha[r['sha256']] for r in selected]
    return dict(selected_sha256=None if len(selected)!=1 else selected[0]['sha256'],
        selected_sha256s=[r['sha256'] for r in selected],experience_text=memory.delivery_text(selected_bundles),
        provisional_sha256s=[],reason='evidence_semantic_selection' if selected else 'no_semantically_applicable_experience',
        route=dict(schema_version=VERSION,ranking='new_obligation_coverage_then_directness_then_bm25',
            max_experiences=MAX_EXPERIENCES,max_characters=MAX_CHARACTERS,selected_characters=used_characters,
            recalled_count=len(candidates),semantically_admitted_count=sum(d['admitted'] for d in decisions),
            assessments=decisions))
