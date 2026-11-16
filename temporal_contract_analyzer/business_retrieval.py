"""Public-source business applicability and obligation coverage, without cluster IDs."""
from . import experience_memory as memory, taxonomy
from .core import EvidenceError

VERSION='business-source-coverage-v1'
MAX_CANDIDATES=64
MAX_EXPERIENCES=5
MAX_CHARACTERS=16000


def recall(task,sources,bundles):
    # Text ranking orders the bounded candidate presentation, not final admission.
    docs='\n'.join(text for name,text in sources.items() if name.lower().endswith('.md'))
    query=task+'\n'+task+'\n'+docs+'\n'+'\n'.join(sources.values())
    hits=memory.search_records(bundles,query,limit=max(1,len(bundles)),include_all=True)['results'] if bundles else []
    scores={h['sha256']:h['score'] for h in hits}
    ordered=sorted(bundles,key=lambda b:(-scores.get(b['sha256'],0),b['sha256']))
    return dict(schema_version=VERSION,bank_count=len(bundles),
        candidates=[dict(sha256=b['sha256'],id=b['id'],text=memory.render(b),requires=b['requires'],excludes=b['excludes'],lexical_score=scores.get(b['sha256'],0)) for b in ordered[:MAX_CANDIDATES]],
        omitted_candidate_sha256s=[b['sha256'] for b in ordered[MAX_CANDIDATES:]],
        candidate_policy='approved_bank_text_order_without_label_or_unknown_fact_prefilter')


def schema(candidates):
    def obj(props):return dict(type='object',properties=props,required=list(props),additionalProperties=False)
    text=dict(type='string',minLength=1)
    evidence=dict(type='array',items=obj(dict(file=text,quote=text)))
    codes=[x['sha256'] for x in candidates]
    obligation=obj(dict(id=text,text=text,evidence=dict(evidence,minItems=1)))
    premise=obj(dict(condition=text,status=dict(type='string',enum=['supported','contradicted','unknown']),evidence=evidence))
    predicate=obj(dict(kind=dict(type='string',enum=['requires','excludes']),predicate=dict(type='string',enum=list(taxonomy.definition()['mechanism_predicates'])),
                       state=dict(type='string',enum=['known','contradicted','unknown']),evidence=evidence))
    row=obj(dict(sha256=dict(type='string',enum=codes),relevance=dict(type='string',enum=['direct','transferable','weak','not_applicable','unknown']),
        premises=dict(type='array',items=premise),predicate_findings=dict(type='array',items=predicate),object_mapping=text,contribution=text,
        covered_obligations=dict(type='array',items=text),supporting_evidence=evidence,redundant_with=dict(type='array',items=dict(type='string',enum=codes)),reason=text))
    return obj(dict(business_obligations=dict(type='array',minItems=1,maxItems=20,items=obligation),
                    assessments=dict(type='array',minItems=len(codes),maxItems=len(codes),items=row)))


def payload(task,sources,ast,recalled):
    return dict(task=task,sources=sources,ast=ast,candidates=recalled['candidates'],
        predicate_definitions=taxonomy.definition()['mechanism_predicates'],schema=schema(recalled['candidates']),
        instruction='Use ONLY the current original TASK and public source as normative evidence. '
        'Identify concrete business obligations and preservation checkpoints, not one obligation per generic taxonomy label. '
        'When the task requests preserving existing behavior, inspect the original operations and observable outcomes at callback-capable boundaries. '
        'Absence of an explicit prose deadline is not evidence that existing observable behavior may be weakened. '
        'Do not impose one universal boundary policy: infer ownership, settlement, cancellation and publication from this source. '
        'Assess EVERY candidate against its full applicability, exclusions, preservation and verification text. '
        'For direct/transferable, enumerate all material scenario prerequisites as premises; map business operations, objects and owners to current public code, '
        'and cover every declared requires/excludes predicate exactly once with source evidence. Known/contradicted assert the FULL predicate meaning; unknown is not false. '
        'Progress reception/decoding/audit, document saving/submission, and query cancellation are different operations; generic lifecycle/reentry overlap alone does not make guidance applicable. '
        'Experience citations from its original training task do not establish requirements in this task. Cite only current TASK or exact current source paths/quotes. '
        'Use unique business obligation IDs and reference only those IDs in covered_obligations. Explain a concrete contribution; identify redundancy. '
        'For weak/not_applicable/unknown entries use concise reasons and empty unsupported evidence/findings/coverage as appropriate; never invent support or fill a quota. '
        'Return structured output only; do not edit code or access scores, references, historical case/cluster identifiers or Gold. '
        'All applicability judgments and proposed obligations remain fallible hypotheses for source-based repair, not correctness or effectiveness certificates.')


def select(result,recalled,task,sources,bundles):
    from ._session_runtime.schema_validator import validate
    from .tempoevo_v4 import evidence_valid
    validate(result,schema(recalled['candidates']))
    candidates={x['sha256']:x for x in recalled['candidates']}
    obligations=result['business_obligations'];ids=[x['id'] for x in obligations]
    if len(ids)!=len(set(ids)):raise EvidenceError('Business obligations require unique IDs')
    for obligation in obligations:evidence_valid(obligation['evidence'],task,sources)
    rows=result['assessments'];codes=[x['sha256'] for x in rows]
    if len(codes)!=len(set(codes)) or set(codes)!=set(candidates):raise EvidenceError('Assess every recalled candidate exactly once')
    decisions=[];accepted=[]
    for row in rows:
        code=row['sha256'];candidate=candidates[code]
        if not set(row['covered_obligations'])<=set(ids):raise EvidenceError('Coverage references an unknown business obligation')
        if code in row['redundant_with']:raise EvidenceError('Experience cannot duplicate itself')
        for premise in row['premises']:evidence_valid(premise['evidence'],task,sources)
        for finding in row['predicate_findings']:evidence_valid(finding['evidence'],task,sources)
        evidence_valid(row['supporting_evidence'],task,sources)
        expected={(kind,key) for kind in ('requires','excludes') for key in candidate[kind]}
        findings={(f['kind'],f['predicate']):f for f in row['predicate_findings']}
        if len(findings)!=len(row['predicate_findings']) or not set(findings)<=expected:raise EvidenceError('Unexpected or duplicate applicability predicate finding')
        complete=set(findings)==expected
        supported=complete and all(f['state']==('known' if kind=='requires' else 'contradicted') and f['evidence'] for (kind,_),f in findings.items())
        premises=bool(row['premises']) and all(p['status']=='supported' and p['evidence'] for p in row['premises'])
        admitted=row['relevance'] in ('direct','transferable') and supported and premises and bool(row['supporting_evidence']) and bool(row['covered_obligations'])
        decisions.append(dict(row,admitted=bool(admitted),selection_reason='eligible' if admitted else 'unsupported_or_irrelevant'))
        if admitted:accepted.append(row)
    selected=[];covered=set();bysha={b['sha256']:b for b in bundles}
    while accepted and len(selected)<MAX_EXPERIENCES:
        accepted.sort(key=lambda x:(-len(set(x['covered_obligations'])-covered),x['relevance']!='direct',-candidates[x['sha256']]['lexical_score'],x['sha256']))
        row=accepted.pop(0);code=row['sha256'];chosen={x['sha256'] for x in selected}
        decision=next(x for x in decisions if x['sha256']==code)
        if selected and not (set(row['covered_obligations'])-covered):decision['selection_reason']='no_new_obligation_coverage';continue
        if chosen & set(row['redundant_with']) or any(code in x['redundant_with'] for x in selected):decision['selection_reason']='redundant';continue
        if len(memory.delivery_text([bysha[x['sha256']] for x in selected+[row]]) or '')>MAX_CHARACTERS:decision['selection_reason']='text_budget';continue
        selected.append(row);covered.update(row['covered_obligations']);decision['selection_reason']='selected'
    return dict(schema_version=VERSION,reason='public_business_applicability_and_coverage',
        selected_sha256s=[x['sha256'] for x in selected],experience_text=memory.delivery_text([bysha[x['sha256']] for x in selected]),
        business_obligations=obligations,covered_obligations=sorted(covered),uncovered_obligations=[x for x in ids if x not in covered],
        decisions=decisions,effectiveness_verified=False)
