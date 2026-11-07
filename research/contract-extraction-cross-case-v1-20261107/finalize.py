"""Offline artifact/config/source protection verification, never a model call."""
import json,csv,subprocess,re
from pathlib import Path
from run import OUT,ROOT,read,save,sha,hashes,frozen,global_snapshot,prompt_for
import request_guard as guard

def main():
 frozen();execution=read(OUT/'execution-complete.json');req=read(OUT/'requests.json');meter=read(OUT/'request-meter/ledger.json');assert execution['status']=='COMPLETE' and len(req)==8
 initial=read(OUT/'initial-state.json');g=lambda *a:subprocess.check_output(['git',*a],cwd=ROOT)
 assert g('rev-parse','HEAD').decode().strip()==initial['head'] and sha(g('diff','--binary'))==initial['unstaged_diff'] and sha(g('diff','--cached','--binary'))==initial['staged_diff']
 for p,h in initial['protected_files'].items():assert sha((ROOT/p).read_bytes())==h,p
 for p,h in read(OUT/'source-and-exposure.json')['review_sources'].items():assert sha(Path(p).read_bytes())==h,p
 source=read(OUT/'source-and-exposure.json')['cases'];cfg=sha((OUT/'research-config.toml').read_bytes());equivalence=[]
 for slot in read(OUT/'schedule.json')['order']:
  call=slot['call_id'];p=OUT/'runs'/call;valid=read(p/'validity.json');assert valid['status']=='PASS'
  before=read(p/'configuration-before.json');after=read(p/'configuration-after.json');assert before['research_config_sha256']==after['profile_config_sha256']==cfg
  assert hashes(p/'workspace')==source[slot['case']]['candidate_files']
  skill=(OUT/('contract_extraction_K0.md' if slot['phase']=='K0' else 'contract_extraction_K1.md')).read_text();actual=(p/'actual-prompt.md').read_text();assert actual==prompt_for(skill,slot['case'])
  output=json.loads((p/'raw-answer.txt').read_text());assert output['report']==(p/'contract.md').read_text() and len(output['report'])<=6000
  trace=read(p/'read-trace.json')
  for x in trace['hook_tool_attempts']:assert not x['denied'] and guard.read_command(x['event'])
  equivalence.append({'call_id':call,'case':slot['case'],'skill':slot['phase'],'repeat':slot['repeat'],'outer_prompt_sha256':sha(actual.replace(skill,'<SKILL>',1)),'config_sha256':cfg,'prompt_sha256':sha(actual),'source_body_files':[x['candidate_file'] for x in valid['source_body_evidence']]})
 for case in ['C1','C3']:assert len({x['outer_prompt_sha256'] for x in equivalence if x['case']==case})==1
 save(OUT/'input-config-equivalence.json',{'only_task_case_material_and_skill_vary':True,'per_case_outer_prompt_identical':True,'all_eight_profile_configs_byte_identical_before_and_after':True,'source_workspaces_unchanged':True,'model_and_effort':'gpt-6-sol/low','configured_service_tier':'priority','actual_server_route_attested':False,'slots':equivalence})
 keys=['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens'];usage={k:sum(x['usage'].get(k,0) for x in req) for k in keys};post={k:sum(x['event'].get('token_usage',{}).get(k,0) for x in meter['events'] if x['event'].get('hook_event_name')=='PostModelRequest') for k in keys};assert usage==post
 assert meter['started']==meter['completed']==sum(x['native']['started'] for x in req)<=49
 assert all(x['status']=='completed' and x['native']['started']<=12 and x['seconds']<600 and not x['native']['blocked_tools'] for x in req)
 costs={'sessions':8,'cases':2,'requests':meter['started'],'tool_hook_attempts':meter['tool_attempts'],'completed_tool_items':sum(x['tools'] for x in req),'usage':usage,'input_includes_cached':True,'reasoning_subset_of_output':True,'session_seconds_sum':sum(x['seconds'] for x in req),'by_slot':[{'call_id':x['call_id'],'case':x['case'],'condition':x['phase'],'repeat':x['repeat'],'requests':x['native']['started'],'tools':x['tools'],'seconds':x['seconds'],'report_characters':x.get('report_characters'),'usage':x['usage']} for x in req],'usd':None,'pricing_limit':'No applicable price verified; no invented dollar cost.','no_model_prerun_retry_or_reflection':True}
 save(OUT/'costs.json',costs)
 # Review rows are mechanically checked, not automatically judged for quality.
 if (OUT/'item-review.csv').exists():
  rows=list(csv.DictReader((OUT/'item-review.csv').open(encoding='utf-8-sig')))
  for row in rows:
   path,n=row['model_reference'].rsplit(':',1);assert row['model_quote'] in (ROOT/path).read_text().splitlines()[int(n)-1]
   assert row['pending_normative_assessment']=='NOT_SCORED_PENDING_CONFIRMATION' and row['confirmed_contract_increment']=='NOT_ASSESSABLE'
 assert not list((OUT/'.runtime').rglob('auth.json'))
 save(OUT/'final-validation.json',{'status':'PASS_ARTIFACT_AND_PROTECTION_CHECKS','source_reading_valid_all_slots':True,'all_review_quotes_resolve':(OUT/'item-review.csv').exists(),'pending_approval_preserved':True,'skills_standards_sources_and_preexisting_files_unchanged':True,'HEAD_and_git_diffs_unchanged':True,'global_configuration_before':{'sha256':initial['global_config_sha256'],'mtime':initial['global_config_mtime']},'global_configuration_after':global_snapshot(),'global_config_bytes_unchanged':global_snapshot()['sha256']==initial['global_config_sha256'],'research_config_identical_all_slots':True,'server_route_attested':False,'counting_and_usage_reconcile':True,'temporary_auth_removed':True,'no_business_changes_scoring_reflection_or_commit':True,'not_an_independent_human_review':True})
 print(json.dumps({'sessions':8,'requests':meter['started'],'tools':costs['completed_tool_items'],'usage':usage,'seconds':costs['session_seconds_sum']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
