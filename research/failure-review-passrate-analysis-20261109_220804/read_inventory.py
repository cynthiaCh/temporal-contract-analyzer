"""Stream the immutable ZIP ledger; never extract or execute archive code."""
import collections,hashlib,io,json,time,zipfile
from pathlib import Path
A=Path(__file__).resolve().parent
ZIP=Path('/home/sribd/Downloads/wangshu/failure-review-export-20261029.zip')
PREFIX='failure-review-export-20261029/'

def save(name,value):(A/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def array_items(stream):
 decoder=json.JSONDecoder();buf='';pos=0;started=False;done=False
 while True:
  chunk=stream.read(1024*1024)
  if chunk:buf=buf[pos:]+chunk;pos=0
  while True:
   while pos<len(buf) and buf[pos].isspace():pos+=1
   if not started:
    if pos==len(buf):break
    if buf[pos]!='[':raise ValueError('Inventory must be a JSON array')
    started=True;pos+=1;continue
   while pos<len(buf) and (buf[pos].isspace() or buf[pos]==','):pos+=1
   if pos==len(buf):break
   if buf[pos]==']':pos+=1;done=True;break
   try:value,end=decoder.raw_decode(buf,pos)
   except json.JSONDecodeError:
    if not chunk:raise
    break
   pos=end;yield value
  if done:
   if buf[pos:].strip() or stream.read(1).strip():raise ValueError('Trailing inventory data')
   return
  if not chunk:raise ValueError('Truncated inventory array')

def identity(x):
 return {k:x.get(k) for k in ['case_id','model','system_identity','source_unit','independent_unit_id','condition','base_condition','variant','reasoning_effort','effort','status','valid_scored','verdict','started_at_utc','completed_at_utc','started_at','completed_at','run_id','session_id','input_tree_sha256','source_manifest_sha256','prompt_sha256','runner_sha256','candidate_sha256','candidate_tree_sha256','submission_sha256','group','runtime','role','timeout_seconds','candidate_complete','infrastructure_valid','scoring_admissible','scoring_status','base_tree_sha256','workspace_input_tree_sha256','case_manifest_sha256','actual_prompt_sha256','workflow_profile','study_design','harness','harness_version','arm','replicate','contamination_findings','agent_task_done','trace_completed','delivery_verified','termination_reason','tool_eligible'] if k in x}

def main():
 start=time.time();raw_runs=(A/'raw-run-receipts.jsonl').open('w');runs=[];scores={};outers={};stats=collections.Counter();keys=collections.Counter();models=collections.Counter();statuses=collections.Counter();counter_by_name=collections.Counter()
 with zipfile.ZipFile(ZIP) as z:
  export_summary=json.loads(z.read(PREFIX+'summary.json'));save('export-summary.json',export_summary)
  index=[json.loads(l) for l in z.read(PREFIX+'index.jsonl').decode().splitlines()];save('nonpass-index.json',index)
  with z.open(PREFIX+'discovery-inventory.json') as raw:
   for row in array_items(io.TextIOWrapper(raw,encoding='utf-8')):
    stats['inventory_entries']+=1;path=row['path'];name=Path(path).name;counter_by_name[name]+=1;x=row.get('data',{})
    if not isinstance(x,dict):stats['nonobject_inventory_data']+=1;continue
    if name=='run.json' and x.get('case_id') and (x.get('model') or x.get('system_identity')):
     raw_runs.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n')
     reduced=identity(x);reduced.update(path=path,root=row.get('root'),receipt_sha256=hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
     runs.append(reduced);keys.update(x.keys());models[str(x.get('model') or x.get('system_identity'))]+=1;statuses[(str(x.get('status')),str(x.get('verdict')),str(x.get('valid_scored')))]+=1
    if name=='score.json':
     schedules=x.get('schedules') or {};runtime=[]
     if isinstance(schedules,dict):runtime=[str(k) for k,v in schedules.items() if isinstance(v,dict) and v.get('runtimeError')]
     scores[path]={'case_id':x.get('case_id'),'variant':x.get('variant'),'verdict':x.get('verdict'),'status':x.get('status'),'runtime_error_schedules':runtime,'observed_effect_count':len(x.get('observed_effects') or {}),'scope_checks':x.get('scope_checks'),'receipt_sha256':hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
    elif name=='result.json':outers[path]=identity(x)
    if stats['inventory_entries']%10000==0:print('streamed',stats['inventory_entries'],'runs',len(runs),flush=True)
  members=z.infolist();save('archive-structure.json',{'files':len(members),'uncompressed_bytes':sum(m.file_size for m in members),'top_level':collections.Counter(m.filename[len(PREFIX):].split('/')[0] for m in members),'discovery_entry':{'uncompressed_bytes':z.getinfo(PREFIX+'discovery-inventory.json').file_size},'ZIP_bytes':ZIP.stat().st_size})
 raw_runs.close();save('run-receipts.json',runs);save('score-projections.json',scores);save('outer-projections.json',outers)
 save('inventory-audit.json',{'stats':stats,'runs':len(runs),'scores':len(scores),'outers':len(outers),'run_field_counts':keys,'models':models,'statuses':[{'status':k[0],'verdict':k[1],'valid_scored':k[2],'count':v} for k,v in statuses.most_common()],'basename_counts':counter_by_name,'seconds':time.time()-start})
 print(json.dumps({'runs':len(runs),'scores':len(scores),'models':models,'statuses':[(k,v) for k,v in statuses.most_common(20)],'seconds':time.time()-start},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
