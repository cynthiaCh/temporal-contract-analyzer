"""Public-source business applicability and obligation coverage, without cluster IDs."""
import re
from . import experience_memory as memory, taxonomy
from .core import EvidenceError

VERSION='business-source-coverage-v5'
MAX_CANDIDATES=6
MAX_EXPERIENCES=3
MAX_CHARACTERS=8000


def require_summaries(bundles, summaries):
    """New retrieval uses reviewed abstracts; old previews are not a fallback."""
    from .compact_experience import validate_summary
    for bundle in bundles:
        value=(summaries or {}).get(bundle['sha256'])
        if value is None:
            raise EvidenceError('Reviewed Abstract required for experience '+bundle['id']+'; use experience-memory/library, not a historical snapshot')
        validate_summary(value)
        if value['review']['decision']!='accept' or value['source_record']!=bundle['sha256']:
            raise EvidenceError('Reviewed Abstract is not current for experience '+bundle['id'])


def recall(task,sources,bundles,*,summaries=None,learning=None,model=None):
    require_summaries(bundles,summaries)
    docs='\n'.join(text for name,text in sources.items() if name.lower().endswith('.md'))
    query=task+'\n'+task+'\n'+docs+'\n'+'\n'.join(sources.values())
    hits=memory.search_records(bundles,query,limit=max(1,len(bundles)),include_all=True,
        text_for_index=lambda bundle:summaries[bundle['sha256']]['text'])['results'] if bundles else []
    scores={h['sha256']:h['score'] for h in hits}
    from .experience_learning import score
    weights={b['sha256']:score((learning or {}).get(b['sha256']),model) for b in bundles}
    ordered=sorted(bundles,key=lambda b:(-scores.get(b['sha256'],0),-weights[b['sha256']],b['sha256']))
    candidates=[dict(sha256=b['sha256'],id=b['id'],text=memory.render(b),requires=b['requires'],excludes=b['excludes'],
        lexical_score=scores.get(b['sha256'],0),summary=summaries[b['sha256']]['text']) for b in ordered[:MAX_CANDIDATES]]
    return dict(schema_version=VERSION,bank_count=len(bundles),weights=weights,candidates=candidates,
        omitted_candidate_sha256s=[b['sha256'] for b in ordered[MAX_CANDIDATES:]],
        candidate_policy='reviewed_abstract_top6_full_text_verification')


def schema(candidates,*,concise=False):
    def obj(props):return dict(type='object',properties=props,required=list(props),additionalProperties=False)
    text=dict(type='string',minLength=1,**({'maxLength':240} if concise else {}))
    quote=dict(type='string',minLength=1,**({'maxLength':240} if concise else {}))
    evidence=dict(type='array',items=obj(dict(file=text,quote=quote)),**({'maxItems':2} if concise else {}))
    codes=[x['sha256'] for x in candidates]
    obligation=obj(dict(id=text,text=text,evidence=dict(evidence,minItems=1)))
    premise=obj(dict(condition=text,status=dict(type='string',enum=['supported','contradicted','unknown']),evidence=evidence))
    predicate=obj(dict(kind=dict(type='string',enum=['requires','excludes']),predicate=dict(type='string',enum=list(taxonomy.definition()['mechanism_predicates'])),
                       state=dict(type='string',enum=['known','contradicted','unknown']),evidence=evidence))
    row=obj(dict(sha256=dict(type='string',enum=codes),relevance=dict(type='string',enum=['direct','transferable'] if concise else ['direct','transferable','weak','not_applicable','unknown']),
        premises=dict(type='array',items=premise,**({'maxItems':5} if concise else {})),
        predicate_findings=dict(type='array',items=predicate,**({'maxItems':len(taxonomy.definition()['mechanism_predicates'])} if concise else {})),object_mapping=text,contribution=text,
        covered_obligations=dict(type='array',items=text,**({'maxItems':8} if concise else {})),supporting_evidence=evidence,
        redundant_with=dict(type='array',items=dict(type='string',enum=codes),**({'maxItems':len(codes)} if concise else {})),reason=text))
    if concise:
        brief=obj(dict(sha256=dict(type='string',enum=codes),relevance=dict(type='string',enum=['weak','not_applicable','unknown']),reason=text))
        row=dict(anyOf=[row,brief])
    return obj(dict(business_obligations=dict(type='array',minItems=1,maxItems=8 if concise else 20,items=obligation),
                    assessments=dict(type='array',minItems=0,maxItems=len(codes) if concise else 2*len(codes),items=row)))


def payload(task,sources,ast,recalled):
    return dict(task=task,sources=sources,ast=ast,candidates=recalled['candidates'],
        predicate_definitions=taxonomy.definition()['mechanism_predicates'],schema=schema(recalled['candidates'],concise=True),
        instruction='Use ONLY the current original TASK and public source as normative evidence. '
        'Identify concrete business obligations and preservation checkpoints, not one obligation per generic taxonomy label. '
        'When the task requests preserving existing behavior, inspect the original operations and observable outcomes at callback-capable boundaries. '
        'Absence of an explicit prose deadline is not evidence that existing observable behavior may be weakened. '
        'Do not impose one universal boundary policy: infer ownership, settlement, cancellation and publication from this source. '
        'Assess EVERY candidate against its full applicability, exclusions, preservation and verification text. '
        'Candidate summaries are incomplete retrieval previews; use the full candidate text when judging applicability. '
        'For direct/transferable, enumerate all material scenario prerequisites as premises; map business operations, objects and owners to current public code, '
        'and cover every declared requires/excludes predicate exactly once with source evidence. Known/contradicted assert the FULL predicate meaning; unknown is not false. '
        'Progress reception/decoding/audit, document saving/submission, and query cancellation are different operations; generic lifecycle/reentry overlap alone does not make guidance applicable. '
        'Experience citations from its original training task do not establish requirements in this task. Cite only current TASK or exact current source paths/quotes. '
        'Use unique business obligation IDs and reference only those IDs in covered_obligations. Explain a concrete contribution; identify redundancy. '
        'Return each candidate exactly once. Invalid or conflicting candidate rows are rejected individually; missing or unsupported assessments are never filled in or admitted. '
        'For weak/not_applicable/unknown return ONLY sha256, relevance and one short reason; no evidence, mappings or predicate analysis. '
        'Write detailed assessments for at most 3 direct/transferable candidates; use brief rows for the rest. '
        'Use at most 8 distinct business obligations. Every explanation and exact quote must be at most 240 characters; choose short exact excerpts, never rewrite quotations. '
        'Use at most 2 evidence excerpts per evidence list and at most 5 premises per detailed assessment. Do not repeat the same explanation across fields. '
        'Keep the entire JSON concise (target under 20000 characters); do not fill unused capacity or invent support. '
        'Return structured output only; do not edit code or access scores, references, historical case/cluster identifiers or Gold. '
        'All applicability judgments and proposed obligations remain fallible hypotheses for source-based repair, not correctness or effectiveness certificates.')


def replay(selection,task,sources,bundles,*,summaries=None,learning=None,model=None):
    """Revalidate a frozen selector result without another model call."""
    from .core import canonical,sha
    if not isinstance(selection,dict) or set(selection)!={'output','delivery_sha256'}:
        raise EvidenceError('Frozen selection requires output and delivery digest')
    if selection['output'] is None:
        result=dict(selected_sha256s=[],experience_text=None,reason='invalid_business_selection_discarded')
        result['provisional_sha256s']=[]
        if sha(canonical(result).encode())==selection['delivery_sha256']:return result
    else:
        result=select(selection['output'],recall(task,sources,bundles,summaries=summaries,learning=learning,model=model),task,sources,bundles)
        result['provisional_sha256s']=[]
        if sha(canonical(result).encode())==selection['delivery_sha256']:return result
    raise EvidenceError('Frozen experience delivery mismatch')


def select(result,recalled,task,sources,bundles):
    from collections import defaultdict
    from ._session_runtime.schema_validator import validate
    from .tempoevo_v4 import evidence_valid
    requested=schema(recalled['candidates'])
    # Validate the envelope first, then each independently useful obligation/row.
    # The requested model schema remains typed; host validation isolates row errors.
    envelope=dict(requested,properties=dict(requested['properties']))
    envelope['properties']['business_obligations']=dict(requested['properties']['business_obligations'],items={})
    envelope['properties']['assessments']=dict(requested['properties']['assessments'],items={})
    validate(result,envelope)
    candidates={x['sha256']:x for x in recalled['candidates']}
    bysha={b['sha256']:b for b in bundles}
    if len(candidates)!=len(recalled['candidates']) or not set(candidates)<=set(bysha):
        raise EvidenceError('Recalled candidate bank identity mismatch')
    issues=[];obligation_groups=defaultdict(list);assessment_groups=defaultdict(list)
    def issue(kind,index,error,code=None):
        value=dict(kind=kind,index=index,error=str(error))
        if code is not None:value['sha256']=code
        issues.append(value)
    for index,row in enumerate(result['business_obligations']):
        try:
            validate(row,requested['properties']['business_obligations']['items'])
            evidence_valid(row['evidence'],task,sources)
        except (EvidenceError,ValueError) as error:
            # Reserve an identifiable bad ID too: no row may borrow a different
            # definition under an ambiguous obligation identity.
            if isinstance(row,dict) and isinstance(row.get('id'),str):obligation_groups[row['id']].append((index,None))
            issue('invalid_obligation',index,error);continue
        obligation_groups[row['id']].append((index,row))
    obligations=[]
    for ident,group in obligation_groups.items():
        first=group[0][1]
        if first is None or any(row is None or row!=first for _,row in group):
            issue('conflicting_obligation',group[0][0],'Unusable or conflicting business obligation ID: '+ident);continue
        obligations.append(first)
        if len(group)>1:issue('identical_obligation_deduplicated',group[0][0],'Repeated identical business obligation ID: '+ident)
    if not obligations:raise EvidenceError('No unique source-grounded business obligations')
    ids={x['id'] for x in obligations}
    for index,row in enumerate(result['assessments']):
        code=row.get('sha256') if isinstance(row,dict) else None
        if not isinstance(code,str) or code not in candidates:
            issue('unrecognized_assessment',index,'Assessment does not identify a recalled candidate',code if isinstance(code,str) else None);continue
        assessment_groups[code].append((index,row))
    decisions=[];accepted=[];validated=0
    for code,candidate in candidates.items():
        group=assessment_groups.get(code,[])
        if not group:
            decisions.append(dict(sha256=code,admitted=False,selection_reason='missing_assessment'))
            issue('missing_assessment',None,'Candidate was not assessed',code);continue
        index,row=group[0]
        if any(other!=row for _,other in group[1:]):
            decisions.append(dict(sha256=code,admitted=False,selection_reason='conflicting_assessments'))
            issue('conflicting_assessments',index,'Conflicting duplicate candidate assessments',code);continue
        if len(group)>1:issue('identical_assessment_deduplicated',index,'Repeated identical candidate assessment',code)
        try:
            if set(row)=={'sha256','relevance','reason'}:
                brief=schema(recalled['candidates'],concise=True)['properties']['assessments']['items']['anyOf'][1]
                validate(row,brief)
                row=dict(row,premises=[],predicate_findings=[],object_mapping='Not admitted.',contribution='None.',
                    covered_obligations=[],supporting_evidence=[],redundant_with=[])
            validate(row,requested['properties']['assessments']['items'])
            if not set(row['covered_obligations'])<=ids:raise EvidenceError('Coverage references an unknown or rejected business obligation')
            if code in row['redundant_with']:raise EvidenceError('Experience cannot duplicate itself')
            for premise in row['premises']:evidence_valid(premise['evidence'],task,sources)
            for finding in row['predicate_findings']:evidence_valid(finding['evidence'],task,sources)
            evidence_valid(row['supporting_evidence'],task,sources)
            expected={(kind,key) for kind in ('requires','excludes') for key in candidate[kind]}
            findings={(f['kind'],f['predicate']):f for f in row['predicate_findings']}
            if len(findings)!=len(row['predicate_findings']) or not set(findings)<=expected:raise EvidenceError('Unexpected or duplicate applicability predicate finding')
        except (EvidenceError,ValueError) as error:
            decisions.append(dict(sha256=code,admitted=False,selection_reason='invalid_assessment',validation_error=str(error)))
            issue('invalid_assessment',index,error,code);continue
        validated+=1
        complete=set(findings)==expected
        supported=complete and all(f['state']==('known' if kind=='requires' else 'contradicted') and f['evidence'] for (kind,_),f in findings.items())
        premises=bool(row['premises']) and all(p['status']=='supported' and p['evidence'] for p in row['premises'])
        admitted=row['relevance'] in ('direct','transferable') and supported and premises and bool(row['supporting_evidence']) and bool(row['covered_obligations'])
        decisions.append(dict(row,admitted=bool(admitted),selection_reason='eligible' if admitted else 'unsupported_or_irrelevant'))
        if admitted:accepted.append(row)
    if candidates and not validated:
        raise EvidenceError('No independently valid candidate assessments: '+str(issues[:3]))
    selected=[];covered=set()
    while accepted and len(selected)<MAX_EXPERIENCES:
        accepted.sort(key=lambda x:(-len(set(x['covered_obligations'])-covered),x['relevance']!='direct',-recalled.get('weights',{}).get(x['sha256'],0),-candidates[x['sha256']]['lexical_score'],x['sha256']))
        row=accepted.pop(0);code=row['sha256'];chosen={x['sha256'] for x in selected}
        decision=next(x for x in decisions if x['sha256']==code)
        if selected and not (set(row['covered_obligations'])-covered):decision['selection_reason']='no_new_obligation_coverage';continue
        if chosen & set(row['redundant_with']) or any(code in x['redundant_with'] for x in selected):decision['selection_reason']='redundant';continue
        if len(memory.delivery_text([bysha[x['sha256']] for x in selected+[row]]) or '')>MAX_CHARACTERS:decision['selection_reason']='text_budget';continue
        selected.append(row);covered.update(row['covered_obligations']);decision['selection_reason']='selected'
    return dict(schema_version=recalled['schema_version'],reason='public_business_applicability_and_coverage',
        selected_sha256s=[x['sha256'] for x in selected],experience_text=memory.delivery_text([bysha[x['sha256']] for x in selected]),
        business_obligations=obligations,covered_obligations=sorted(covered),uncovered_obligations=[x['id'] for x in obligations if x['id'] not in covered],
        decisions=decisions,validation=dict(policy='per-entry-source-validation-v1',partial=bool(issues),validated_assessments=validated,eligible_assessments=sum(x['admitted'] for x in decisions),issues=issues),effectiveness_verified=False)
