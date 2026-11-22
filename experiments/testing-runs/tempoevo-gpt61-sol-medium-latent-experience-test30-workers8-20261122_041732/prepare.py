"""Zero-model input replay, grader calibration and fresh trajectory preparation."""
import csv,hashlib,json,os,shutil,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent/'temporal-contract-analyzer';sys.path.insert(0,str(REPO))
from temporal_contract_analyzer.tempoevo_v4 import Trajectory
from temporal_contract_analyzer.core import canonical,sha
from temporal_contract_analyzer import business_retrieval as retrieval
from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend
from temporal_contract_analyzer.swe_tempoc_inputs import case_input

def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
plan=read(ROOT/'plan.json');parents=read(ROOT/'parent-results.json');bank=read(ROOT/'memory-snapshot.json')
rows=list(csv.DictReader((ROOT/'testing_30_cases.csv').open(encoding='utf-8-sig')))
assert len(rows)==30 and [r['case_id'] for r in rows]==[r['case_id'] for r in parents]
bench=ROOT.parent/'swe-tempoc';selections={};provenance=[];files={}
for row in parents:
    cid=row['case_id'];t=Path(row['result_source'])/'batch'/cid/'trajectory'
    p=read(t/'protocol.json');state=read(t/'state.json');delivery=read(t/'delivery.json')
    assert state['status']=='scored' and state['gold_result']['valid'] is True
    assert p['model_settings']['model']=='gpt-6.1-sol' and p['model_settings']['reasoning_effort']=='medium'
    assert p['memory_snapshot']==bank and p['condition']=='structured'
    stages=[s for s in state['stages'] if s['kind']=='selection']
    assert delivery['reason'] in ('public_business_applicability_and_coverage','invalid_business_selection_discarded')
    output=read(t/'stages'/stages[-1]['key']/'result.json').get('output') if delivery['reason']=='public_business_applicability_and_coverage' else None
    selection=dict(output=output,delivery_sha256=sha(canonical(delivery).encode()))
    sources={f.relative_to(t/'original').as_posix():f.read_text() for f in (t/'original').rglob('*') if f.is_file()}
    assert retrieval.replay(selection,p['task'],sources,[e['bundle'] for e in bank['entries']])==delivery
    current=case_input(cid,bench);assert current['task']==p['task']
    current_sources={f.relative_to(current['candidate']).as_posix():f.read_text() for f in Path(current['candidate']).rglob('*') if f.is_file()}
    assert current_sources==sources,(cid,'source mismatch')
    for f in (bench/p['public_case_record']['manifest']).parent.rglob('*'):
        if f.is_file() and '__pycache__' not in f.parts:files[f.relative_to(bench).as_posix()]=sha(f.read_bytes())
    selections[cid]=selection
    provenance.append(dict(rank=row['rank'],case_id=cid,parent=str(t),parent_protocol_sha256=sha((t/'protocol.json').read_bytes()),parent_delivery_sha256=sha((t/'delivery.json').read_bytes()),delivery_sha256=selection['delivery_sha256'],experience_present=bool(delivery['experience_text']),selected_sha256s=delivery['selected_sha256s'],historical_selection_stages=stages,historical_model_usage_newly_executed=False))
write(ROOT/'frozen-selections.json',selections);write(ROOT/'retrieval-provenance.json',provenance)
code="import sys,json,hashlib;from pathlib import Path;f=json.load(sys.stdin);bad=[k for k,v in f.items() if not (Path('/opt/swe-tempoc')/k).is_file() or hashlib.sha256((Path('/opt/swe-tempoc')/k).read_bytes()).hexdigest()!=v];print(json.dumps(dict(files_checked=len(f),mismatches=bad)))"
proc=subprocess.run(['docker','run','--rm','-i','--pull=never','--network','none','--read-only','--entrypoint','python3',plan['backend']['grader_image'],'-B','-c',code],input=json.dumps(files),capture_output=True,text=True,check=True)
check=json.loads(proc.stdout);write(ROOT/'selected-case-image-verification.json',check);assert not check['mismatches']

def calibrate(row):
    cid=row['case_id'];r=ROOT/'calibration'/cid;r.mkdir(parents=True)
    case=case_input(cid,bench);manifest=case['case_record']['manifest'];m=read(bench/manifest)
    write(r/'case.json',dict(manifest=manifest))
    ev=dict(image=plan['backend']['grader_image'],inputs={str(r/'case.json'):'/checks/case.json',str(REPO/'tools/tempoevo-docker/gold.py'):'/checks/gold.py'},command=['/usr/bin/python3','/checks/gold.py'],seconds=180)
    controls=[]
    for name,overlay in [('original',None),('reference',m['references']['bounded']),('negative',m['mutants'][0])]:
        subject=r/name;shutil.copytree(case['candidate'],subject)
        if overlay:shutil.copytree((bench/manifest).parent/overlay,subject,dirs_exist_ok=True)
        output=r/'checks'/name;output.mkdir(parents=True)
        raw=NativeV4Backend({}).evaluate('gold',dict(candidate=str(subject),evaluator=ev),output)
        write(output/'result.json',raw)
        item=dict(control=name,valid=raw.get('valid'),passed=raw.get('passed'),verdict=raw.get('verdict'),error=raw.get('error'));controls.append(item)
        assert item['valid'] is True and item['passed']==(name=='reference'),(cid,item)
    print(json.dumps(dict(calibrated=cid)),flush=True)
    return dict(case_id=cid,controls=controls)
# Reuse scorer witnesses only after exact source, image and evaluator identity checks.
previous=Path(plan['calibration_source'])
old_preflight=read(previous/'preflight.json');assert old_preflight['valid'] and old_preflight['calibration_controls']==90
old_bank=read(previous/'memory-snapshot.json');assert old_bank==bank
old_rows={r['case_id']:r for r in read(previous/'batch/progress.json')}
receipts=[]
for row in rows:
    cid=row['case_id'];old_t=Path(old_rows[cid]['root'])/'trajectory';old_p=read(old_t/'protocol.json');old_b=read(old_t/'binding.json')
    parent_t=Path(next(r for r in parents if r['case_id']==cid)['result_source'])/'batch'/cid/'trajectory'
    parent_p=read(parent_t/'protocol.json')
    assert old_p['task']==parent_p['task'] and old_p['original_inventory']==parent_p['original_inventory']
    assert old_p['backend']==parent_p['backend']==plan['backend']
    for path,digest in old_b['evaluators'].items():assert sha(Path(path).read_bytes())==digest,(cid,path,'changed evaluator')
    for control in ('original','reference','negative'):
        source=previous/'calibration'/cid/'checks'/control/'result.json';raw=read(source)
        assert raw.get('valid') is True and raw['passed']==(control=='reference')
        target=ROOT/'calibration'/cid/'checks'/control/'result.json';target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        receipts.append(dict(case_id=cid,control=control,source=str(source),sha256=sha(source.read_bytes())))
shutil.copyfile(previous/'calibration.json',ROOT/'calibration.json')
write(ROOT/'calibration-reuse.json',dict(valid=True,controls=90,source=str(previous),model_independent=True,evaluator_hashes_unchanged=True,source_image_parity=True,receipt_hashes=receipts))
args=[sys.executable,'-B',str(REPO/'tools/tempoevo-docker/prepare_selected.py'),'--root',str(ROOT/'batch'),'--selection-file',str(ROOT/'testing_30_cases.csv'),'--swe-tempoc-root',str(bench),'--evaluation-split',str(REPO/'cases/split.json'),'--solver-image',plan['backend']['solver_image'],'--grader-image',plan['backend']['grader_image'],'--binary',plan['binary'],'--model-config',str(ROOT/'model-profiles.json'),'--model-profile','sol61-medium','--store',str(ROOT/'experience-library'),'--memory-snapshot',str(ROOT/'memory-snapshot.json'),'--mode','testing','--condition','latent_experience','--frozen-selections',str(ROOT/'frozen-selections.json'),'--retrieval-profile','business-source-v1','--limit','30']
write(ROOT/'prepare-command.json',args)
with (ROOT/'prepare-selected.log').open('w') as log:proc=subprocess.run(args,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
assert proc.returncode==0,'Inspect prepare-selected.log'
subprocess.run([sys.executable,'-B',str(ROOT/'validate.py')],cwd=REPO,check=True)
