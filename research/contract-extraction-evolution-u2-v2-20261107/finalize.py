"""Offline archive, cost and protection checks; no model or maintenance scoring."""
import json,csv,re,subprocess,time
from pathlib import Path
from run import OUT,ROOT,read,save,sha,hashes,frozen,prompt_for
import request_guard as guard

def main():
 frozen();requests=read(OUT/'requests.json');meter=read(OUT/'request-meter/ledger.json');assert [x['call_id'] for x in requests]==['k0-1','k0-2','reflect-1','k1-1','k1-2']
 assert all(x['status']=='completed' for x in requests)
 extraction=[x for x in requests if x['phase']!='reflection'];trace=[];prompt_checks=[];body_files={}
 K0=(OUT/'contract_extraction_K0.md').read_text();K1=(OUT/'contract_extraction_K1.md').read_text()
 for x in extraction:
  call=x['call_id'];p=OUT/'runs'/call;valid=read(p/'validity.json');assert valid['status']=='PASS' and valid['source_body_read_proven']
  actual=(p/'actual-prompt.md').read_text();skill=K0 if x['phase']=='K0' else K1
  assert actual==prompt_for(skill) and actual.count(skill)==1
  assert json.loads((p/'raw-answer.txt').read_text())['report']==(p/'contract.md').read_text()
  assert hashes(p/'workspace')==read(OUT/'scope-and-sources.json')['candidate_files']
  hook=read(p/'read-trace.json')['hook_tool_attempts']
  for e in hook:assert not e['denied'] and guard.read_command(e['event']);trace.append({'call':call,**e})
  body_files[call]=sorted({a['candidate_file'] for a in valid['successful_source_body_reads']})
  prompt_checks.append({'call_id':call,'prompt_sha256':sha(actual),'skill_sha256':sha(skill),'normalized_outer_prompt_sha256':sha(actual.replace(skill,'<SKILL>',1)),'source_hashes':read(OUT/'scope-and-sources.json')['candidate_files'],'validity_evidence':str(p/'validity.json'),'report_characters':x['report_characters']})
 assert len({x['normalized_outer_prompt_sha256'] for x in prompt_checks})==1
 assert (OUT/'runs/k0-1/actual-prompt.md').read_bytes()==(OUT/'runs/k0-2/actual-prompt.md').read_bytes()
 assert (OUT/'runs/k1-1/actual-prompt.md').read_bytes()==(OUT/'runs/k1-2/actual-prompt.md').read_bytes()
 v1=OUT.parent/'contract-extraction-evolution-u2-v1-20261107';assert (OUT/'runs/k0-1/actual-prompt.md').read_bytes()==(v1/'runs/k0-1/actual-prompt.md').read_bytes()
 # Identical frozen tool/model/provider options for every extraction slot (only per-slot mounts differ).
 def args(cmd):
  o=[];i=cmd.index('/opt/codex')+2
  while i<len(cmd):
   if cmd[i] in ['-c','-m','--enable','--disable','--sandbox','--output-schema']:o+=cmd[i:i+2];i+=2
   else:i+=1
  return o
 assert all(args(x['command'])==args(extraction[0]['command']) for x in extraction)
 save(OUT/'input-equivalence.json',{'only_skill_text_changes_between_K0_K1':True,'all_outer_prompt_sha256_equal':True,'v1_K0_prompt_byte_identical':True,'candidate_bytes_equal_all_slots':True,'extraction_cli_options_equal':True,'options':args(extraction[0]['command']),'by_slot':prompt_checks,'source_body_files_read':body_files,'scope':'The reflection prompt intentionally differs and receives development feedback; no baseline outputs or feedback in extraction prompts.'})
 # Reflection lineage includes v2 only. No v1 invalid output was read by this builder.
 rb=read(OUT/'baseline-review.freeze.json');rf=read(OUT/'reflection.freeze.json')
 for manifest in [rb['files'],rf['files'],read(OUT/'K1.freeze.json')['files']]:
  for p,h in manifest.items():assert sha(Path(p).read_bytes())==h,p
 assert sha((OUT/'reflection-template.md').read_bytes())==read(OUT/'reflection-design.freeze.json')['template_sha256']
 assert (OUT/'contract_extraction_K1.md').read_text()==json.loads((OUT/'runs/reflect-1/raw-answer.txt').read_text())['skill']
 assert read(OUT/'K1-boundary-review.json')['semantic_scope_review']['status']=='PASS'
 # Verify literal review quotes, locations, IDs, source line citation bounds.
 data=read(OUT/'review-data.json');assert len(data['items'])==28 and len(data['timer'])==16
 for row in data['items']+data['timer']:
  path,line=row['model_reference'].rsplit(':',1);assert row['model_quote'] in (ROOT/path).read_text().splitlines()[int(line)-1]
 for x in extraction:
  report=(OUT/'runs'/x['call_id']/'contract.md').read_text()
  for filename,line in re.findall(r'/workspace/(src/[A-Za-z0-9_.-]+):(\d+)',report):
   assert (OUT/'materials/candidate'/filename).exists() and 0<int(line)<=len((OUT/'materials/candidate'/filename).read_text().splitlines())
 # Native accounting is reconciled independently to output turn usage.
 keys=['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens']
 usage={k:sum(x['usage'].get(k,0) for x in requests) for k in keys}
 nativeusage={k:sum(e['event'].get('token_usage',{}).get(k,0) for e in meter['events'] if e['event'].get('hook_event_name')=='PostModelRequest') for k in keys};assert usage==nativeusage
 assert meter['started']==meter['completed']==sum(x['native']['started'] for x in requests)<=49
 assert not meter['blocked_requests'] and all(not x['native']['blocked_tools'] for x in requests)
 for x in requests:assert x['native']['started']<= (1 if x['phase']=='reflection' else 12) and x['seconds']<600
 r=next(x for x in requests if x['phase']=='reflection');assert r['native']['started']==1 and r['native']['tool_attempts']==0 and r['tools']==0
 costs={'batch':'v2','top_level_sessions':5,'native_model_requests':meter['started'],'native_model_responses':meter['completed'],'request_cap':49,'tool_hook_attempts':meter['tool_attempts'],'completed_tool_items':sum(x['tools'] for x in requests),'usage':usage,'input_includes_cached':True,'reasoning_subset_of_output':True,'total_formal_session_seconds':sum(x['seconds'] for x in requests),'by_slot':[{'call_id':x['call_id'],'requests':x['native']['started'],'tools':x['tools'],'seconds':x['seconds'],'usage':x['usage'],'report_characters':x.get('report_characters')} for x in requests],'by_phase':{phase:{k:sum(x['usage'].get(k,0) for x in requests if x['phase']==phase) for k in keys} for phase in ['K0','reflection','K1']},'dollar_cost':None,'pricing_limit':'No verified applicable price; USD not fabricated.','no_retry_or_extra_model_prerun':True,'v1_incurred_costs_separate':read(OUT/'v1-incurred-costs.json')}
 save(OUT/'costs.json',costs)
 summary={'status':'COMPLETED_DEVELOPMENT_EXPERIMENT','batch':'v2 full rerun after infrastructure repair; not selective replay','case':'U2 exposed development case','AI_agent_evaluation':True,'independent_human_review':False,'formal_sessions':5,'native_model_requests':meter['started'],'first_baseline_gate':'PASS','valid_extractions':4,'reflection_requests':1,'K1_unedited':True,'K1_production_adopted':False,'normative_obligations_preserved':['O1','O3'],'scoped_description_improvements':['O2 waiting interval, state writers/consumer and unknown field semantics','O5 close and response callback facts','O6 request identity/shared state/conditional interleaving'],'timer_progress':'T1/T2/T4 more explicit; T3 concrete adjacent-background queued work after close still partial','unchanged_partial':['O4 overall','O7 adjacent background close behavior'],'observed_new_unsupported_requirements':[],'observed_semantic_reversals':[],'observed_lost_confirmed_obligations':[],'conclusion':'Limited within-case improvement in evidence-grounded boundary descriptions and unknown handling; no new confirmed business obligations recovered. Not complete coverage or generalization.','no_numeric_quality_total':True,'environment_limit':'global config service_tier changed after last slot copy by observed mtime; no formal per-slot config hashes; see global-config-observation.json','no_repair_success_claim':True,'no_maintenance_scoring':True,'no_GEPA':True,'no_ReAct':True,'v1_outputs_used_for_reflection_or_comparison':False,'no_commits':True,'costs_file':'costs.json'}
 save(OUT/'summary.json',summary)
 ini=read(OUT/'initial-state.json');g=lambda *a:subprocess.check_output(['git',*a],cwd=ROOT)
 assert g('rev-parse','HEAD').decode().strip()==ini['head'];assert sha(g('diff','--cached','--binary'))==ini['staged_diff'];assert sha(g('diff','--binary'))==ini['unstaged_diff']
 for n,h in ini['protected_files'].items():assert sha((ROOT/n).read_bytes())==h,n
 observed=read(OUT/'global-config-observation.json');assert sha((Path.home()/'.codex/config.toml').read_bytes())==observed['current_sha256'];assert observed['removing_only_field_matches_initial']
 for n,h in read(OUT/'scope-and-sources.json')['source_files'].items():assert sha(Path(n).read_bytes())==h,n
 assert not list((OUT/'.runtime').rglob('auth.json'))
 save(OUT/'final-validation.json',{'status':'PASS_MINIMAL_OFFLINE_CHECKS','not_a_quality_or_human_approval_verdict':True,'v1_all_prior_bytes_unchanged':True,'original_standards_evaluation_and_history_unchanged':True,'head_and_git_diffs_unchanged':True,'all_preexisting_tracked_files_unchanged':True,'global_config_unchanged':False,'global_config_observation':'service_tier added after last per-slot copy according to mtime; origin unknown; not overwritten; see global-config-observation.json','candidate_readonly_hashes_equal':True,'extraction_cli_options_identical':True,'formal_profile_config_hashes':'not separately persisted; copy-order evidence only','outer_prompts_only_skill_diff':True,'review_quotes_resolve':True,'model_source_citation_bounds_valid':True,'request_and_usage_counts_reconcile':True,'four_extractions_read_source_bodies':body_files,'temporary_auth_removed':True,'K1_equals_raw_reflection':True,'frozen_inputs_unchanged':True,'remaining_limits':['AI executing-agent review, not independent human review','citation bounds and exact quotes do not mechanically prove full semantic correctness','one exposed case, two repetitions, no statistics or repair inference']})
 print(json.dumps({'status':summary['status'],'sessions':5,'requests':meter['started'],'tools':costs['completed_tool_items'],'usage':usage,'seconds':costs['total_formal_session_seconds'],'report_characters':{x['call_id']:x.get('report_characters') for x in extraction}},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
