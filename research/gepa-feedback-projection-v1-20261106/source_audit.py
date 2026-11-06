"""Read-only provenance/admission check. Never execute candidates, probes or models."""
import json,hashlib,collections
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];BENCH=ROOT.parent/'temporal-contract-bench-git'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
 corpus=BENCH/'experiments/temporal-diagnostics-v1/corpus.json';shared=BENCH/'evidence/results.json';c=read(corpus);e=read(shared);payload={k:v for k,v in e.items() if k!='content_sha256'};canonical=(json.dumps(payload,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode();assert hashlib.sha256(canonical).hexdigest()==e['content_sha256']
 by=collections.defaultdict(list)
 for n,r in enumerate(e['runs']):
  if r.get('agent_started') is True or isinstance(r.get('input_tokens'),(float,int)) and r['input_tokens']>0:by[r['case_id']].append((n,r))
 rows=[dict(x,registry=str(corpus),registry_position=i,source_root=str(BENCH)) for i,x in enumerate(c['cases'])]
 local=ROOT/'experiments/local-cases.json'
 for i,r in enumerate(read(local)['cases']):rows.append(dict(r,registry=str(local),registry_position=i,source_root=str(ROOT),source_kind='local_authored_diagnostic'))
 group=collections.defaultdict(list)
 for r in rows:group[r['independent_unit_id']].append(r)
 exclusion=read(BENCH/'studies/case-admission-exclusions-v1/registry.json');blocked={r['case_id'] for r in exclusion['cases'] if r.get('block_new_runs')}
 output=[]
 for unit,members in sorted(group.items()):
  records=[(n,r) for x in members for n,r in by[x['id']]];witnesses=[]
  for n,r in records[:3]:
   raw=BENCH/r['path'];witnesses.append(dict(json_pointer=f'/runs/{n}',case_id=r['case_id'],id=r['id'],condition=r.get('condition'),model=r.get('model'),effort=r.get('effort'),input_tokens=r.get('input_tokens'),agent_started=r.get('agent_started'),status=r.get('status'),receipt_sha256=r.get('receipt_sha256'),raw_receipt_path=str(raw),raw_receipt_locally_present=raw.is_file()))
  details=[]
  for m in members:
   cp=Path(m['source_root'])/m['manifest'];cm=read(cp);oracle=cm.get('oracle',{});oracle=oracle if isinstance(oracle,dict) else {'entry':oracle};files={k:dict(path=str(cp.parent/v),exists=(cp.parent/v).is_file(),sha256=sha(cp.parent/v) if (cp.parent/v).is_file() else None) for k,v in oracle.items() if isinstance(v,str)}
   supported=m['adapter'] in ['legacy-js','python'] and 'latent-maintenance' in m['conditions'] and m['id'] not in blocked
   details.append(dict(case_id=m['id'],adapter=m['adapter'],prior_exposure_label=m.get('prior_exposure'),source_kind=m.get('source_kind'),registry=m['registry'],registry_position=m['registry_position'],manifest=str(cp),manifest_sha256=sha(cp),candidate_base_exists=(cp.parent/'base').is_dir(),trusted_verification_files=files,supported_by_existing_executor=supported,source_cluster=str(cp.parent).split('/arms/')[0],new_runs_blocked=m['id'] in blocked))
  output.append(dict(unit=unit,cases=details,historical_started_receipts=len(records),exposure_witnesses=witnesses,novel_holdout_admissible=False if records else None,reason='positive historical model-start evidence in same source unit' if records else 'absence of exported receipts does not prove unexposed; needs further audit'))
 assert len(c['cases'])==94 and len(group)==47
 assert all(r['historical_started_receipts']>0 for r in output)
 mirror=ROOT.parent/'swe-tempoc/experiments/temporal-diagnostics-v1/corpus.json';mirrorinfo=None
 if mirror.is_file():
  mc=read(mirror)['cases'];extra=sorted({x['id'] for x in mc}-{x['id'] for x in c['cases']});mirrorinfo=dict(path=str(mirror),sha256=sha(mirror),cases=len(mc),additional_case_ids=extra);assert not extra
 save('source-verification.json',dict(status='BLOCKED_SOURCE_ADMISSION',scope='registered bench corpus, analyzer local registrations, locally identified swe-tempoc catalog mirror',bench_cases=len(c['cases']),local_cases=len(rows)-len(c['cases']),source_units=len(group),source_units_with_model_start_evidence=len(output),confirmed_new_units=0,minimum_new_units_required=5,shared_archive=dict(path=str(shared),sha256=sha(shared),sealed_content_sha256=e['content_sha256'],seal_verified=True,record_count=len(e['runs']),basis='positive usage/agent_started; no reliance on absence or creation-time labels'),catalog=dict(path=str(corpus),sha256=sha(corpus)),mirror=mirrorinfo,units=output,limits=['Shared archive is a sealed exported receipt index; some raw original receipts are absent locally. This prevents stronger raw-receipt authentication, not conservative exposure exclusion.','Historical author/agent exposure is not reset by new IDs, source revisions, a different model, or task repartitioning.','No oracle reruns or new task authoring performed. Existing verification files are inventoried; fresh calibration/hash attestation for new holdouts was not established.']))
 save('split.json',dict(status='NOT_ADMITTED',train=['transfer-progress-composition-v4-vanilla','download-polling-restoration-low-cue-react18'],train_role='historically exposed targeted development only',val=[],test=[],val_minimum=2,test_minimum=3,reason='All47 registered source units already have model-start evidence; no five qualifying new units confirmed. No exposed cases substituted.',formal_execution_allowed=False))
 print('SOURCE_GATE_BLOCKED: 94 bench cases + 2 local; 47/47 source units exposed; qualifying new units 0')
if __name__=='__main__':main()
