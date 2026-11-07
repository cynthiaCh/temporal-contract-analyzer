import json,re,sys
from pathlib import Path
from run import OUT,read,save,sha,hashes,frozen

def check(call):
 frozen();p=OUT/'runs'/call;r=read(p/'receipt.json');slot=next(x for x in read(OUT/'schedule.json')['order'] if x['call_id']==call);base=OUT/'materials'/slot['case']/'candidate';proof=[]
 for n,e in enumerate((json.loads(x) for x in (p/'events.jsonl').read_text().splitlines()),1):
  item=e.get('item',{})
  if e.get('type')!='item.completed' or item.get('type')!='command_execution' or item.get('exit_code')!=0:continue
  output=item.get('aggregated_output','');normalized=[re.sub(r'^\s*\d+\s+','',x).strip() for x in output.splitlines()]
  for q in (base/'src').glob('*'):
   lines=[x.strip() for x in q.read_text().splitlines() if len(x.strip())>=20 and not x.strip().startswith(('//','import '))];matched=[x for x in lines if x in normalized]
   body=[x for x in matched if any(y in x for y in ['return ','=>','if(','if (','.then(','dispatchEvent','queueMicrotask'])]
   if len(matched)>=3 and body:proof.append({'event_line':n,'command':item.get('command'),'candidate_file':str(q.relative_to(base)),'matched_body_lines':matched,'tool_output_sha256':sha(output)})
 source=read(OUT/'source-and-exposure.json')['cases'][slot['case']]['candidate_files'];native=r['native'];before=read(p/'configuration-before.json');after=read(p/'configuration-after.json')
 cfg=sha((OUT/'research-config.toml').read_bytes());ok=r['status']=='completed' and proof and not native['blocked_requests'] and not native['blocked_tools'] and native['tool_attempts']>0 and hashes(p/'workspace')==source and before['research_config_sha256']==cfg and after['profile_config_sha256']==cfg
 result={'status':'PASS' if ok else 'FAIL','call':call,'case':slot['case'],'quality_not_used':True,'source_body_evidence':proof,'source_unchanged':hashes(p/'workspace')==source,'configuration_locked':before['research_config_sha256']==after['profile_config_sha256']==cfg,'no_rejected_or_out_of_bounds_tools':not native['blocked_tools'],'requests':native['started'],'completed_tool_items':r['tools'],'server_route_attested':False}
 save(p/'validity.json',result)
 if call==read(OUT/'schedule.json')['order'][0]['call_id']:save(OUT/'first-run-gate.json',result)
 print(json.dumps({'call':call,'status':result['status'],'source_body_files':len(proof)},ensure_ascii=False));return bool(ok)
if __name__=='__main__':sys.exit(0 if check(sys.argv[1]) else 1)
