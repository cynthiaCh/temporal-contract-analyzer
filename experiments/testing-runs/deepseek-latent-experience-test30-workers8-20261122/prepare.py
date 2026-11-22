"""Prepare paired latent+experience ablation, with no new selection or Contract."""
import copy,csv,datetime,hashlib,json,os,subprocess,sys,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2];sys.path.insert(0,str(REPO))
from temporal_contract_analyzer.tempoevo_v4 import Trajectory
from temporal_contract_analyzer.core import canonical,sha
from temporal_contract_analyzer import business_retrieval as retrieval
PARENT=REPO/'.tempoevo/runs/run-20261121-093940-7eca6f'
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
assert not (ROOT/'plan.json').exists(),'Never overwrite a frozen run'
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
assert not any(r['status'] in ('preparing','running','stopping') for r in json.load(opener.open('http://127.0.0.1:8765/api/runs')))
rows=list(csv.DictReader((REPO/'review-drafts/table1-deepseek-20261122/case-results.csv').open(encoding='utf-8-sig')))
assert len(rows)==30
bank=read(PARENT/'batch/memory-snapshot.json');assert len(bank['entries'])==58
write(ROOT/'memory-snapshot.json',bank)
selections={};provenance=[]
for row in rows:
    cid=row['case_id'];rid=row['experience_source_run'];t=REPO/'.tempoevo/runs'/rid/'batch'/cid/'trajectory'
    p=read(t/'protocol.json');state=read(t/'state.json');assert (state.get('gold_result') or {}).get('valid') is True
    assert p['memory_snapshot']==bank and p['condition']=='structured' and p['retrieval_profile']=='business-source-v1'
    delivery=read(t/'delivery.json')
    selection_stages=[r for r in state['stages'] if r['kind']=='selection']
    stage=read(t/'stages'/selection_stages[-1]['key']/'result.json')
    output=stage['output'] if delivery['reason']=='public_business_applicability_and_coverage' else None
    assert delivery['reason'] in ('public_business_applicability_and_coverage','invalid_business_selection_discarded')
    selection=dict(output=output,delivery_sha256=sha(canonical(delivery).encode()))
    sources={f.relative_to(t/'original').as_posix():f.read_text() for f in (t/'original').rglob('*') if f.is_file()}
    assert retrieval.replay(selection,p['task'],sources,[e['bundle'] for e in bank['entries']])==delivery
    selections[cid]=selection
    provenance.append(dict(rank=int(row['rank']),case_id=cid,parent_run=rid,experience_count=len(delivery['selected_sha256s']),experience_present=bool(delivery['experience_text']),historical_selection_stages=[r['key'] for r in selection_stages],historical_selection_model_turns=sum(r.get('requests',0) for r in selection_stages),historical_selection_credits=sum(r.get('credits') or 0 for r in selection_stages)))
write(ROOT/'frozen-selections.json',selections);write(ROOT/'retrieval-provenance.json',provenance)
ident='run-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S')+'-latent-experience'
target=REPO/'.tempoevo/runs'/ident;target.mkdir()
old=read(PARENT/'lab.json');command=old['prepare_command'][:]
command[command.index('--root')+1]=str(target/'batch');command[command.index('--condition')+1]='latent_experience'
command+=['--memory-snapshot',str(ROOT/'memory-snapshot.json'),'--frozen-selections',str(ROOT/'frozen-selections.json')]
config=copy.deepcopy(old['config']);config.update(condition='latent_experience',workers=8)
meta=dict(id=ident,title='DeepSeek Flash low · latent + frozen58 experience · fixed30 · workers8',status='preparing',created_at=now(),config=config,model=old['model'],prepare_command=command,ablation=dict(parent=str(PARENT),memory_size=58,paired_selection_replay=True,contract_stage=False,plan=str(ROOT/'plan.json')))
write(target/'lab.json',meta)
plan=dict(id=ident,root=str(target),created_at=now(),workers=8,condition='latent_experience',model='DeepSeek-Flash',reasoning_effort='low',bank_size=58,case_count=30,action_limits=dict(requests=24,seconds=600),current_run_model_stages=['action'],historical_selection_usage='Reused, not newly executed. Historical model-turn and credit records retained in retrieval-provenance.json.',same_nonempty_experience_cases=sum(r['experience_present'] for r in provenance),no_experience_cases=sum(not r['experience_present'] for r in provenance),test_policy='One Action, final Gold only, no learning, no Contract, retain all valid outcomes; infrastructure failures recorded separately.',runtime_delta='New testing-only condition and source-validated selector replay; same Action instruction, source, experience text and limits as parent, contract field null. No Qoder adapter or grader changes.',prepare_command=command)
write(ROOT/'plan.json',plan)
with (target/'prepare.log').open('w') as log:result=subprocess.run(command,cwd=REPO,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,TCA_BENCH_ROOT=config['benchmark']))
assert result.returncode==0,'Inspect prepare.log'
prepared=read(target/'batch/progress.json');assert len(prepared)==30 and [r['case_id'] for r in prepared]==[r['case_id'] for r in rows]
checks=[]
for row,record in zip(prepared,provenance):
    t=Path(row['root'])/'trajectory';p=Trajectory(t).verify();oldroot=REPO/'.tempoevo/runs'/record['parent_run']/'batch'/row['case_id']/'trajectory';previous=read(oldroot/'protocol.json')
    for key in ('task','original_inventory','public_case_record','binary','model_settings','backend','limits','max_attempts','mode','learning_policy','retrieval_profile','memory_snapshot','protected_paths','feedback_fields'):
        assert p[key]==previous[key],(row['case_id'],key)
    assert p['total_request_cap']==24 and p['max_attempts']==1 and p['mode']=='testing'
    assert p['condition']=='latent_experience' and p['frozen_experience_delivery']==read(oldroot/'delivery.json')
    assert p['gold_evaluator']['image']==previous['gold_evaluator']['image'] and p['gold_evaluator']['command']==previous['gold_evaluator']['command']
    assert p['evaluation_split']['role']=='testing'
    state=read(t/'state.json');assert not state['stages'] and not state['attempts'] and state['contract'] is None
    checks.append(dict(case_id=row['case_id'],exact_delivery_replay=True))
write(ROOT/'paired-input-validation.json',dict(valid=True,cases=30,model_calls=0,checks=checks))
meta.update(status='prepared',prepared_cases=30,updated_at=now());write(target/'lab.json',meta)
with (target/'events.jsonl').open('a') as log:log.write(json.dumps(dict(at=now(),kind='READY',message='30 paired latent+experience cases validated; exact historical deliveries, no Contract; Action24turns/600s; model calls0.'))+'\n')
print(json.dumps(dict(id=ident,prepared=30,valid=True,workers=8,nonempty_experience=plan['same_nonempty_experience_cases'])),flush=True)
