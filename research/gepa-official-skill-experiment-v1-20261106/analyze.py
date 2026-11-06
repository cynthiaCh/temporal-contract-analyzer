"""Post-selection reporting only; never imported by the optimizer."""
import json,collections,subprocess
from runtime import *

def cost(rows):
 return dict(codex_sessions=len(rows),task_executions=sum('phase' in r for r in rows),input_tokens=sum(r.get('usage',{}).get('input_tokens',0) for r in rows),cached_input_tokens=sum(r.get('usage',{}).get('cached_input_tokens',0) for r in rows),output_tokens=sum(r.get('usage',{}).get('output_tokens',0) for r in rows),seconds=sum(r.get('including_score_seconds',r.get('seconds',0)) for r in rows),tool_calls=sum(r.get('tool_calls',0) for r in rows),native_requests=sum(r.get('model_requests',r.get('native_requests_after',0)-r.get('native_requests_before',0)) or 0 for r in rows))

def main():
 p=frozen();rows=read(OUT/'task-results.json');refs=read(OUT/'reflection-calls.json');selection=read(OUT/'selection.freeze.json') if (OUT/'selection.freeze.json').exists() else None
 groups={}
 for key in ['train','val','test']:
  rs=[r for r in rows if r['split']==key];groups[key]=dict(executions=len(rs),whole_pass=sum(r['metric']==1 for r in rs),execution_failures=[r['id'] for r in rs if r['category']!='behavior'],cost=cost(rs))
 records=[]
 for r in rows:
  d=Path(r['path'])/'jobs/j-001';tr=read(d/'trajectory-index.json') if (d/'trajectory-index.json').exists() else {}
  records.append(dict(id=r['id'],case=r['case'],split=r['split'],arm=r['arm'],replicate=r['replicate'],skill_sha256=r['skill_sha256'],whole_pass=r['metric']==1,category=r['category'],changed_paths=r.get('changed_paths',[]),original_check_losses=(r.get('score') or {}).get('original_check_losses',[]),original_assertion_failures=(r.get('score') or {}).get('original_assertion_failures',[]),original_assertion_not_emitted=(r.get('score') or {}).get('original_assertion_not_emitted',[]),actual_tool_evidence=[dict(line=c['line'],command=c['command'],exit_code=c['exit_code']) for c in tr.get('commands',[])],artifact=str(d)))
 save(OUT/'EVIDENCE.json',records)
 proposals=[dict(key=f.parent.name,candidate=read(f),validation=read(f.parent/'validation.json'),review=read(f.parent/'review.json') if (f.parent/'review.json').exists() else None) for f in (OUT/'candidates').glob('*/candidate.json')]
 result=read(OUT/'official-result.json') if (OUT/'official-result.json').exists() else None
 total=cost(rows+refs);total['codex_sessions']=len(rows)+len(refs);total['task_executions']=len(rows);total['reflection_callable_requests']=len(refs);total['reflection_native_requests']=requests_used()
 summary=dict(status='COMPLETE' if (OUT/'completion.json').exists() else 'INCOMPLETE',official_version=read(OUT/'environment/official.json'),selection=selection,official_result=result,groups=groups,candidates=proposals,budgets=dict(optimization_used=sum(r['phase']=='opt' for r in rows),optimization_cap=24,test_used=sum(r['phase']=='test' for r in rows),test_cap=12,reflection_native_used=requests_used(),reflection_cap=6),costs=dict(execution_train=cost([r for r in rows if r['split']=='train']),validation_selection=cost([r for r in rows if r['split']=='val']),final_test=cost([r for r in rows if r['phase']=='test']),reflection=cost(refs),total=total),proposals_generated=len(proposals)-1,admitted_new_candidates=(len(result['candidates'])-1 if result else None),official_metric_calls=(result.get('total_metric_calls') if result else None),adapter_batch_calls=len(read(OUT/'adapter-evaluations.json')),reflection_dataset_calls=len(read(OUT/'reflection-datasets.json')),nonzero_shell_commands=sum(len(r['shell_failures']) for r in rows),cache_hits=0,merge_enabled=False,merge_occurred=False,independent_generalization_cases=0,results=rows)
 save(OUT/'summary.json',summary)
 audit=dict(head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),diff=subprocess.check_output(['git','diff'],text=True),status=subprocess.check_output(['git','status','--short'],text=True),frozen_inputs_verified=True,formal_resume=False,all_additions_inside_study=True)
 save(OUT/'audit.json',audit);print(json.dumps(dict(status=summary['status'],groups={k:{a:b for a,b in v.items() if a!='cost'} for k,v in groups.items()},costs=summary['costs'],selection=selection),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
