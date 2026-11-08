"""Read-only evidence audit, no runner imports or execution of historical code."""
import hashlib,json,subprocess
from pathlib import Path
A=Path(__file__).resolve().parent;R=A.parents[1];H=R/'research/transfer-reflection-crosslang-20261108_202000'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(A/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
assert not (A/'initial-state.json').exists()
tracked=[R/p for p in subprocess.check_output(['git','ls-files','-z'],cwd=R).decode().split('\0') if p]
protected={str(p):sha(p) for p in tracked+list(H.rglob('*')) if p.is_file()}
config=Path.home()/'.codex/config.toml';protected[str(config)]=sha(config)
save('protected-files.json',protected)
save('initial-state.json',{'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'status':subprocess.check_output(['git','status','--short'],text=True),'tracked_diff':subprocess.check_output(['git','diff','--binary'],text=True),'preexisting_untracked':'research/transfer-reflection-crosslang-20261108_202000/','instructions':'No applicable AGENTS.md in ancestors/repository/research or audited batch; unrelated archived AGENTS.md not applicable.'})
selected={'js-exp-1':{'item_11':'archive-only','item_13':'mixed: syntax/source inspection plus patch inspection','item_16':'archive-only','item_18':'archive-only','item_19':'mixed: business source/patch/reject inspection','item_20':'archive-only','item_22':'archive-only','item_23':'mixed: patch and business-source inspection/dry-run','item_24':'mixed: patch/copy inspection','item_25':'archive-related diff construction against business source'},'js-exp-2':{'item_14':'archive-only','item_16':'archive-only','item_17':'archive-only','item_18':'archive-only','item_19':'mixed: patch/source inspection','item_21':'archive-only','item_22':'archive-only','item_23':'archive-only','item_24':'archive-only','item_25':'archive-only','item_26':'archive-only'}}
prompts=[];actions=[];filechanges=[];saved=[]
for p in sorted((H/'runs').iterdir()):
 rec=json.loads((p/'receipt.json').read_text())
 if rec['phase']!='repair':continue
 text=(p/'actual-prompt.md').read_text();prompts.append({'slot':p.name,'path':str(p/'actual-prompt.md'),'sha256':sha(p/'actual-prompt.md'),'ambiguous_archive_clause_count':text.count('；补丁从独立工作区归档。'),'explicit_before_after_or_patch_directory_requirement':False})
 saved.append({'slot':p.name,'files':{n:(p/n).exists() for n in ['frozen-start.json','actual-prompt.md','events.jsonl','stderr.log','raw-answer.txt','patch.diff','receipt.json','score.stdout.json','score.stderr.txt']},'workspace_retained':(p/'workspace').is_dir(),'separate_original_tree_snapshot':(p/'original').exists(),'separate_final_tree_snapshot':(p/'final-candidate').exists()})
 for line_n,line in enumerate((p/'events.jsonl').read_text().splitlines(),1):
  e=json.loads(line);i=e.get('item',{})
  if e.get('type')!='item.completed':continue
  if i.get('type')=='command_execution' and i.get('id') in selected.get(p.name,{}):actions.append({'slot':p.name,'event_line':line_n,'item_id':i['id'],'classification':selected[p.name][i['id']],'command':i['command'],'exit_code':i['exit_code'],'output_sha256':hashlib.sha256(i.get('aggregated_output','').encode()).hexdigest()})
  if i.get('type')=='file_change':
   for ch in i.get('changes',[]):
    if 'patch-archive/' in ch.get('path','') or ch.get('path','').endswith('.patch'):
     filechanges.append({'slot':p.name,'event_line':line_n,'item_id':i['id'],'path':ch.get('path'),'kind':ch.get('kind'),'note':'Specific historical patch-artifact edit, not a general suffix-based deletion policy.'})
save('history-audit.json',{'prompts':prompts,'existing_runner_outputs':saved,'archive_commands':actions,'patch_artifact_changes':filechanges,'findings':['Runner already retains mutable workspace, start hash, actual prompt, event/tool-output stream, stderr, raw answer, ledger, diff and official score.','Actual prompt contains ambiguous archive clause; no explicit demand for before/after copies or named patch directories. Causality of every model action is not established.','Actual commands prove duplicate patch construction, reverse/reapply checks, reject/backup cleanup and repeated patch repair inside business workspace.','Original diff subprocess return code is not checked; final snapshot is mutable workspace only; exception path can skip diff/score archival.','native_backend binds host cli-output and meter directories inside agent namespace; host archive paths are present in recorded launch command; business workspace also contains model-created archive copies.','No shared non-frozen general-purpose session archiver found in searched research paths; archive_outputs.py is a different historical anonymization workflow.'],'cost_savings_or_repair_rate_estimate':None,'model_calls':0,'maintenance_executions':0,'score_reruns':0})
