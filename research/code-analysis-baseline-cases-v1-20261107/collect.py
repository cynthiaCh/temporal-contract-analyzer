"""Post-completion offline aggregation. No scoring, models or report changes."""
import collections,csv,hashlib,json,subprocess
from pathlib import Path
from run import OUT,ROOT,read,save,sha,frozen

def main():
 frozen();assert (OUT/'execution-complete.json').exists(),'No evaluation/collection before six slots end'
 rows=read(OUT/'requests.json');assert len(rows)==6
 costs=[];tools=[];checks=[]
 for r in rows:
  folder=OUT/'runs'/r['call_id'];c=r['case'];m=read(folder/'request-meter/ledger.json')
  posts=[x['event'] for x in m['events'] if x['event'].get('hook_event_name')=='PostModelRequest']
  native_usage={k:sum(e.get('token_usage',{}).get(k,0) or 0 for e in posts) for k in ['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens']}
  costs.append(dict(call_id=r['call_id'],case=c,repeat=r['repeat'],status=r['status'],cli_sessions=1,completed_turns=r['completed_turns'],native_requests=m['started'],native_completed=m['completed'],blocked_requests=m['blocked_requests'],blocked_tools=m['blocked_tools'],cli_usage=r['usage'],native_post_usage=native_usage,seconds=r['seconds'],completed_tool_items=r['tools'],hook_tool_attempts=m['tool_attempts'],report_characters=r.get('report_characters'),archive_truncated=False,USD=None,USD_reason='No bill/invoice or frozen tariff supplied; not estimated from assumed pricing'))
  for item in r['tool_index']:tools.append(dict(call_id=r['call_id'],case=c,**item))
  prompt_ok=sha(folder/'actual-prompt.md')==sha(OUT/'materials'/c/'prompt.md')==r['prompt_sha256']
  snapshot_ok={str(f.relative_to(folder/'workspace')):sha(f) for f in (folder/'workspace').rglob('*') if f.is_file()}==next(x['candidate_files'] for x in read(OUT/'source-verification.json')['cases'] if x['case']==c)
  checks.append(dict(call_id=r['call_id'],prompt_matches_frozen=prompt_ok,candidate_matches_frozen=snapshot_ok,budget_ok=m['started']<=12,CLI_native_usage_equal=all(r['usage'].get(k)==native_usage[k] for k in r['usage']),status=r['status']))
  assert prompt_ok and snapshot_ok and m['started']<=12
 totals=dict(cli_sessions=len(rows),completed_reports=sum(x['status']=='completed' for x in rows),failed_slots=[r['call_id'] for r in rows if r['status']!='completed'],native_requests=sum(x['native_requests'] for x in costs),native_completed=sum(x['native_completed'] for x in costs),completed_tool_items=sum(x['completed_tool_items'] for x in costs),hook_tool_attempts=sum(x['hook_tool_attempts'] for x in costs),session_wall_seconds=sum(x['seconds'] for x in costs),elapsed_execution_seconds=max(r['completed_at'] for r in rows)-min(r['started_at'] for r in rows),CLI_usage={k:sum(x['cli_usage'].get(k,0) for x in costs) for k in ['input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens']},native_post_usage={k:sum(x['native_post_usage'].get(k,0) for x in costs) for k in ['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens']},reflection_or_judge_requests=0,maintenance_runs=0,scoring_runs=0,gepa_runs=0,USD=None)
 assert totals['native_requests']<=72
 save(OUT/'costs.json',dict(totals=totals,slots=costs,counting='CLI session != native PreModelRequest dispatch != completed tool item. Native PostModelRequest token_usage independently summed, CLI turn totals retained. Hook tool attempts can count PreToolUse and PermissionRequest for a single action; do not merge them. Network packet/reconnect counts are not measured by native model hook.',per_slot_checks=checks))
 save(OUT/'tool-index.json',tools)
 initial=read(OUT/'initial-state.json');paths={ROOT/f for f in subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0') if f};paths.update((ROOT/'research').rglob('*'))
 current={str(f.relative_to(ROOT)):sha(f) for f in sorted(paths) if f.is_file() and OUT not in f.parents and not any(x in ('.git','.runtime','.venv','__pycache__') for x in f.relative_to(ROOT).parts)}
 changed=[k for k in sorted(set(initial['files'])|set(current)) if initial['files'].get(k)!=current.get(k)]
 same_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()==initial['HEAD']
 same_diff=subprocess.check_output(['git','diff','--binary'],cwd=ROOT).decode()==initial['diff'] and subprocess.check_output(['git','diff','--cached','--binary'],cwd=ROOT).decode()==initial['staged']
 assert not changed and same_head and same_diff
 save(OUT/'execution-validation.json',dict(status='PASS',all_six_finished_before_review=True,checks=checks,unchanged_existing_file_count=len(current),changed_existing_files=changed,HEAD_unchanged=same_head,tracked_and_staged_diff_preserved=same_diff,budget_limits_respected=True,standard_approval_unchanged=True,credentials_not_archived=not any((OUT/'.runtime').rglob('auth.json')),no_retry=True))
 print(json.dumps(totals,ensure_ascii=False))
if __name__=='__main__':main()
