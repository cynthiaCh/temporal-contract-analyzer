"""Single-source citation spans; never repair or reinterpret model statements."""
import copy,hashlib,json
from pathlib import Path
from schema_validator import validate

VERSION='source-span-ids-1'
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def fingerprint(x):return hashlib.sha256(canonical(x).encode()).hexdigest()


def catalog(sources):
    rows=[]
    for file,text in sorted(sources.items()):
        for number,line in enumerate(text.splitlines(),1):
            for start in range(0,len(line),80):
                quote=line[start:start+80]
                if not quote.strip():continue
                rows.append({'id':'S%04d'%(len(rows)+1),'file':file,'line':number,
                             'start_column':start,'end_column':start+len(quote),'quote':quote})
    return {'version':VERSION,'files_sha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in sorted(sources.items())},'entries':rows}


def schema(catalog_value,legacy_schema):
    result=copy.deepcopy(legacy_schema)
    ids=[r['id'] for r in catalog_value['entries']]
    if not ids:raise ValueError('No source spans')
    for properties in [result['properties'],result['properties']['facts']['items']['properties'],
                       result['properties']['claims']['items']['properties']]:
        original=properties.pop('evidence')
        properties['evidence_ids']={**{k:v for k,v in original.items() if k!='items'},
                                    'items':{'type':'string','enum':ids}}
    for obj in [result,result['properties']['facts']['items'],result['properties']['claims']['items']]:
        obj['required']=['evidence_ids' if k=='evidence' else k for k in obj['required']]
    return result


def verify_catalog(value,sources):
    if value!=catalog(sources):raise ValueError('Source span catalog/input drift')
    return True


def normalize(raw,sources,legacy_schema,expected_catalog_sha256):
    """Return an explicitly derived legacy view, without changing any claim."""
    value=catalog(sources)
    if fingerprint(value)!=expected_catalog_sha256:raise ValueError('Source span catalog digest mismatch')
    validate(raw,schema(value,legacy_schema))
    by_id={r['id']:r for r in value['entries']}
    selected=[]
    def refs(ids):
        out=[]
        for source_id in ids:
            if source_id not in by_id:raise ValueError('Unknown source span ID')
            r=by_id[source_id];selected.append(r)
            out.append({k:r[k] for k in ['file','line','quote']})
        return out
    def convert(obj):
        return {**{k:copy.deepcopy(v) for k,v in obj.items() if k!='evidence_ids'},
                'evidence':refs(obj['evidence_ids'])}
    result=convert({k:v for k,v in raw.items() if k not in ['facts','claims']})
    result['facts']=[convert(row) for row in raw['facts']]
    result['claims']=[convert(row) for row in raw['claims']]
    validate(result,legacy_schema)
    return result,{'version':VERSION,'origin':'program_derived_citation_fields_only',
      'raw_model_object_sha256':fingerprint(raw),'source_catalog_sha256':fingerprint(value),
      'derived_analysis_sha256':fingerprint(result),'selected_spans':selected,
      'statement_contract_category_or_fact_state_modified':False,'semantic_entailment_checked':False}


INSTRUCTIONS='''Read the current candidate source and task once; extract the candidate
automatic Contract, one T1-T4 mechanism class (unknown allowed), source facts and
premises. Only candidate-visible source/docs/TASK and the public taxonomy are
available; no case IDs, score, reference patch, history or expected class.
Return the typed object matching the supplied schema. evidence_ids contains ONLY
IDs from the generated source-span catalog below. Do NOT transcribe filenames,
line numbers, quotations or another copy of a source fragment. Python derives
those fields from exact frozen spans; it will NOT fix or reinterpret claims.
Use a relevant span whose actual meaning supports the claim, not merely a nearby
line. Every known/contradicted fact needs one ID, unknown may use no ID. Provide
each predicate exactly once. The catalog, source bodies and span IDs are visible
inputs, not external evaluator data. Actual source-body reading is still required.
Only read tools; no code edits, tests, networking or tools beyond candidate reads.
Allowed commands: pwd, ls, rg, cat, nl, head, tail, wc and sed numeric line prints;
2>/dev/null and || true are allowed. No general shell redirection or scripts.
Keep Contract <=1400 characters; claims <=4; top evidence_ids <=3; fact/claim
evidence_ids <=1. No wrapper/report, no JSON encoded in a string.
Distinguish reported defect, requirement, source fact and preservation inference.
Do not preserve the reported defective behavior or prescribe a unique repair
when the task permits alternatives. Check conditions, negation, event order,
record/resource ownership, retained history versus visible output, and physical
cancellation versus settlement. Use predicate definitions literally; adjacent
mechanisms do not establish one another. Honest scope limitations are unknowns,
not automatically contradictory business policies. Claims and premises need
subsequent AI-assisted semantic review; valid IDs do not prove entailment.
Frozen public material:
'''
