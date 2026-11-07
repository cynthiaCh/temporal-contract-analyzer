"""Evidence-only execution gate: never judges Contract content quality."""
import json,re,sys
from pathlib import Path
from run import OUT,read,save,hashes,sha,frozen

def check(call):
 frozen();folder=OUT/'runs'/call;rec=read(folder/'receipt.json');events=[json.loads(x) for x in (folder/'events.jsonl').read_text().splitlines()];proof=[]
 for n,e in enumerate(events,1):
  item=e.get('item',{})
  if e.get('type')!='item.completed' or item.get('type')!='command_execution' or item.get('exit_code')!=0:continue
  output=item.get('aggregated_output','');normalized=[re.sub(r'^\s*\d+\s+','',x).strip() for x in output.splitlines()]
  for p in (OUT/'materials/candidate/src').glob('*'):
   lines=[x.strip() for x in p.read_text().splitlines() if len(x.strip())>=20 and not x.strip().startswith('//')]
   matched=[x for x in lines if x in normalized]
   unique=[x for x in matched if any(y in x for y in ['checkPreparation','schedulePreparationRetry','state.current','this.state','usePreparation','globalThis.','data-loading'])]
   if len(matched)>=3 and unique:proof.append({'event_line':n,'command':item.get('command'),'candidate_file':str(p.relative_to(OUT/'materials/candidate')),'tool_output_sha256':sha(output),'matched_body_lines':matched,'distinctive_lines':unique})
 native=rec.get('native',{});work=hashes(folder/'workspace')==read(OUT/'scope-and-sources.json')['candidate_files']
 blocked=native.get('blocked_tools',0)+native.get('blocked_requests',0)
 good=rec['status']=='completed' and bool(proof) and work and not blocked and native.get('tool_attempts',0)>0
 result={'status':'PASS' if good else 'FAIL','call_id':call,'gate_type':'execution validity only; no quality-based selection','successful_source_body_reads':proof,'source_body_read_proven':bool(proof),'no_denied_or_out_of_bounds_tool_attempts':not blocked,'read_only_workspace_unchanged':work,'model_request_count':native.get('started'),'tool_hook_attempts':native.get('tool_attempts'),'completed_tool_items':rec.get('tools'),'report_content_quality_not_used':True,'limitation':'evidence proves successful observed command body reads and whitelist enforcement, not every source/claim understood'}
 save(folder/'validity.json',result)
 if call=='k0-1':save(OUT/'first-baseline-gate.json',result)
 print(json.dumps({'call':call,'gate':result['status'],'body_read_evidence':len(proof)},ensure_ascii=False))
 return good
if __name__=='__main__':sys.exit(0 if check(sys.argv[1]) else 1)
