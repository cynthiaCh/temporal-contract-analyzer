"""Extract tool/service incidents without treating ordinary failed self-checks as infrastructure."""
import json
from pathlib import Path
O=Path(__file__).resolve().parent
def main():
 rows=[]
 for r in json.loads((O/'actual-schedule.json').read_text()):
  d=O/'runs'/r['slot'];events=d/'events.jsonl'
  if not events.exists():continue
  for n,line in enumerate(events.read_text().splitlines(),1):
   try:e=json.loads(line)
   except ValueError:rows.append({'slot':r['slot'],'event_line':n,'category':'malformed_event','raw':line});continue
   item=e.get('item',{})
   if e.get('type')=='item.completed' and item.get('type')=='command_execution' and item.get('exit_code') not in [0,None]:
    rows.append({'slot':r['slot'],'event_line':n,'category':'nonzero_candidate_tool_command','exit_code':item['exit_code'],'command':item.get('command'),'output':item.get('aggregated_output'),'interpretation':'A failed git/self-check/diff command is retained; it is not by itself a service, source-read or oracle infrastructure failure.'})
   elif e.get('type')=='turn.failed':rows.append({'slot':r['slot'],'event_line':n,'category':'service_turn_failed','event':e})
   elif item.get('type')=='error':rows.append({'slot':r['slot'],'event_line':n,'category':'configured_hook_trust_notice' if 'dangerously-bypass-hook-trust' in item.get('message','') else 'native_error_item','message':item.get('message')})
  meter=d/'meter/ledger.json'
  if meter.exists():
   for event in json.loads(meter.read_text())['events']:
    if event.get('denied'):rows.append({'slot':r['slot'],'category':'native_guard_denial','event':event})
 (O/'execution-anomalies.json').write_text(json.dumps({'rows':rows,'service_failures':sum(r['category']=='service_turn_failed' for r in rows),'guard_denials':sum(r['category']=='native_guard_denial' for r in rows),'nonzero_tool_commands':sum(r['category']=='nonzero_candidate_tool_command' for r in rows),'not_model_calls':True},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
