"""Offline post-freeze unblinding, token accounting and preservation verification."""
import json,csv,hashlib,subprocess
from collections import Counter
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent.parent
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
 freeze=read(OUT/'review.freeze.json');assert freeze['rows']==132
 for n,h in freeze['files'].items():assert sha(OUT/n)==h
 assert sha(OUT/'private-report-labels.json')==freeze['label_map_sha256']
 labels=read(OUT/'private-report-labels.json');reviews=list(csv.DictReader((OUT/'review.csv').open()));requests=read(OUT/'requests.json');assert len(requests)==9 and len({r['call_id'] for r in requests})==9
 for n,h in read(OUT/'protocol.json')['files'].items():assert sha(Path(n))==h
 assert sha(OUT/'protocol.json')==(OUT/'protocol.sha256').read_text().strip()
 kf=read(OUT/'K1.freeze.json');assert sha(OUT/'analysis_skill_K1.md')==kf['skill_sha256']
 assert read(OUT/'runs/a05/raw-answer.txt')['skill']==(OUT/'analysis_skill_K1.md').read_text()
 K0=(OUT/'analysis_skill_K0.md').read_text();K1=(OUT/'analysis_skill_K1.md').read_text()
 source_inputs={u['unit']:u['candidate_files'] for u in read(OUT/'source-verification.json')['inputs']}
 for r in requests:
  assert r['native']['started']<= (1 if r['mode']=='reflection' else 12)
  if r['mode']=='analysis':
   expected=(OUT/'materials'/r['unit']/'K0.prompt.md').read_text().replace(K0,K0 if r['phase']=='K0' else K1,1)
   assert (Path(r['path'])/'actual-prompt.md').read_text()==expected
   work=Path(r['path'])/'workspace';actual={str(f.relative_to(work)):sha(f) for f in work.rglob('*') if f.is_file()};assert actual==source_inputs[r['unit']]
 for n,h in kf['input_files'].items():assert sha(Path(n))==h
 for n,h in read(OUT/'reflection.freeze.json')['files'].items():assert sha(Path(n))==h
 unblinded=[dict(**r,phase=labels[r['anonymous_id']]['phase'],replicate=labels[r['anonymous_id']]['replicate'],call_id=labels[r['anonymous_id']]['call_id']) for r in reviews]
 with (OUT/'unblinded-review.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=unblinded[0]);w.writeheader();w.writerows(unblinded)
 meter=read(OUT/'request-meter/ledger.json');assert meter['started']<=97
 for aid,r in labels.items():assert sha(OUT/'anonymous-review'/aid/'report.md')==r['report_sha256']
 costs=[];keys=['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens']
 for r in requests:
  ev=[e['event'] for e in meter['events'] if e['call_id']==r['call_id'] and e['event'].get('hook_event_name')=='PostModelRequest'];pres=[e for e in meter['events'] if e['call_id']==r['call_id'] and e['event'].get('hook_event_name')=='PreModelRequest' and not e['denied']]
  usage={k:sum((e.get('token_usage') or {}).get(k,0) or 0 for e in ev) for k in keys};missing=sum(not e.get('token_usage') for e in ev)
  reconciliation={k:r['usage'].get(k)==usage[k] for k in ['input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens']} if r['status']=='completed' else None
  if reconciliation:assert all(reconciliation.values())
  costs.append(dict(call_id=r['call_id'],phase=r['phase'],unit=r.get('unit'),replicate=r.get('replicate'),status=r['status'],seconds=r['seconds'],native_requests=len(pres),native_post_events=len(ev),failed_native_requests=sum(e.get('status')!='completed' for e in ev),requests_without_token_receipt=missing,known_usage_only=bool(missing),tools=r['tools'],characters=r.get('report_characters'),usage_reconciliation=reconciliation,**usage))
 def total(rows):return dict(sessions=len(rows),seconds=sum(r['seconds'] for r in rows),native_requests=sum(r['native_requests'] for r in rows),failed_native_requests=sum(r['failed_native_requests'] for r in rows),requests_without_token_receipt=sum(r['requests_without_token_receipt'] for r in rows),tools=sum(r['tools'] for r in rows),**{k:sum(r[k] for r in rows) for k in keys})
 paired=[]
 for unit in ['U1','U2']:
  for rep in [1,2]:
   A=next(r for r in requests if r['phase']=='K0' and r['unit']==unit and r['replicate']==rep);B=next(r for r in requests if r['phase']=='K1' and r['unit']==unit and r['replicate']==rep)
   a=next(a for a,r in labels.items() if r['call_id']==A['call_id']);b=next(a for a,r in labels.items() if r['call_id']==B['call_id']);ar={r['standard_id']:r['assessment'] for r in unblinded if r['anonymous_id']==a};br={r['standard_id']:r['assessment'] for r in unblinded if r['anonymous_id']==b}
   valid=A['status']==B['status']=='completed'
   paired.append(dict(unit=unit,replicate=rep,K0_call=A['call_id'],K1_call=B['call_id'],K0_anonymous=a,K1_anonymous=b,semantic_pair_assessable=valid,K0_characters=A.get('report_characters'),K1_characters=B.get('report_characters'),partial_or_omitted_to_correct=[k for k,v in br.items() if v=='正确覆盖' and ar[k] in ['部分覆盖','遗漏','与证据矛盾']] if valid else None,newly_explicit_reasonable_unknown=[k for k,v in br.items() if v=='合理保留未知' and ar[k] in ['部分覆盖','遗漏']] if valid else None,previous_correct_now_partial_or_wrong=[k for k,v in ar.items() if v=='正确覆盖' and br[k] not in ['正确覆盖','合理保留未知']] if valid else None,criteria=dict(K0=ar,K1=br)))
 counts={phase:{u:dict(Counter(r['assessment'] for r in unblinded if r['phase']==phase and r['unit']==u)) for u in ['U1','U2']} for phase in ['K0','K1']}
 summary=dict(status='COMPLETE_WITH_ONE_EXECUTION_FAILURE',scope='user-confirmed-standard-driven analysis-only development reuse; no repair/generalization evaluation',standard_confirmation='User confirmed scope and explicitly authorized marker updates; original unknowns preserved',evaluation_reviewer='unblinded executing-agent proxy; no new LLM judge or independent human blind evaluation',K0_sha256=sha(OUT/'analysis_skill_K0.md'),K1_sha256=sha(OUT/'analysis_skill_K1.md'),K0_characters=len((OUT/'analysis_skill_K0.md').read_text()),K1_characters=len((OUT/'analysis_skill_K1.md').read_text()),K1_same_as_K0=False,model='gpt-6-sol',effort='low',top_level_sessions=9,analysis_slots=8,valid_analysis_reports=7,reflection_requests=1,maintenance_runs=0,maintenance_score_runs=0,gepa_searches=0,retries_executed=0,blocked_retry_attempts=meter['blocked_requests'],failed_slot='a03',failure_reason='TLS stream disconnect; next retry prevented before dispatch; no replacement',costs=dict(total=total(costs),by_phase={phase:total([r for r in costs if r['phase']==phase]) for phase in ['K0','reflection','K1']},requests=costs,monetary_cost=None,token_cost_limit='Totals include all reported native usage; one failed request has no token receipt, its usage remains unknown and is not asserted zero.'),pairs=paired,assessment_counts_descriptive_only=counts,no_combined_quality_score=True,conclusion='Partial development-internal improvement in handle publication and request/activity interval analysis; obsolete-source fresh-input relation remains incomplete, with validation breadth losses and one local direction conflict. Not merely length, not overall or repair superiority.')
 save(OUT/'summary.json',summary)
 initial=read(OUT/'initial-state.json');approved=read(OUT/'standard-confirmation-update.json')['after'];changed=[]
 for n,h in initial['protected_files'].items():
  f=ROOT/n
  if not f.is_file() or sha(f)!=h:
   assert n in approved and sha(f)==approved[n],n;changed.append(n)
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==initial['head'];assert subprocess.check_output(['git','diff','--cached'],cwd=ROOT,text=True)==initial['staged_diff']
 actual_changed=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines();assert set(actual_changed)==set(changed)
 assert not list((OUT/'.runtime').rglob('auth.json'))
 for u in read(OUT/'source-verification.json')['inputs']:
  for n,h in u['candidate_files'].items():assert sha(OUT/'materials'/u['unit']/'candidate'/n)==h
 save(OUT/'final-validation.json',dict(status='PASS',protected_existing_files_checked=len(initial['protected_files']),only_explicitly_authorized_standard_markers_changed=changed,other_existing_files_changed=[],head_unchanged=True,staged_diff_unchanged=True,immutable_protocol_inputs_verified=True,review_frozen_before_unblinded_summary=True,review_rows=132,nine_unique_sessions=True,native_requests=meter['started'],native_post_events=meter['completed'],source_inputs_readonly_unchanged=True,no_credential_profiles_left=True,no_new_dependencies_or_commits=True))
 print(json.dumps(dict(costs=summary['costs']['total'],pairs=[{k:v for k,v in r.items() if k!='criteria'} for r in paired],counts=counts),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
