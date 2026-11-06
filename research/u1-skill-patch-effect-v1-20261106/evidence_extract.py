"""Offline extraction of archived events/scores, without invoking the scorer."""
import json,csv
from pathlib import Path
OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
def main():
 assert read(OUT/'completion.json')['sessions']==6
 rows=read(OUT/'results.json');excerpts=[];commands=[]
 for r in rows:
  raw=read(Path(r['raw_score']));d=Path(r['path'])/'jobs/j-001';tr=read(d/'trajectory-index.json')
  excerpts.append(dict(id=r['id'],arm=r['arm'],replicate=r['replicate'],raw_score=r['raw_score'],target_pointer='/schedules/start-switch-admission',target=raw['schedules']['start-switch-admission'],other_failed_assertions={k:[a for a in v.get('assertions',[]) if a.get('passed') is False] for k,v in raw['schedules'].items() if any(a.get('passed') is False for a in v.get('assertions',[]))},accepted_completion_pass=raw['observed_effects']['accepted-after-hide']))
  for c in tr['commands']:
   if c['exit_code'] in [0,None]:continue
   category='workspace_without_git_metadata' if c['exit_code'] in [128,129] and 'git ' in c['command'] else 'candidate_check_assertion'
   commands.append(dict(id=r['id'],arm=r['arm'],replicate=r['replicate'],event_line=c['line'],exit_code=c['exit_code'],category=category,command=c['command'],actual_output=c['output']))
 (OUT/'score-excerpts.json').write_text(json.dumps(excerpts,ensure_ascii=False,indent=2)+'\n')
 (OUT/'nonzero-commands.json').write_text(json.dumps(commands,ensure_ascii=False,indent=2)+'\n')
 print('Archived extraction only:',len(excerpts),'scores,',len(commands),'nonzero commands')
if __name__=='__main__':main()
