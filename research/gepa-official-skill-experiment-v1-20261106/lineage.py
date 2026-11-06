"""Read-only reconstruction of official lineage and sample tradeoffs after execution."""
import difflib,json
from runtime import *
def main():
 events=[json.loads(l) for l in (OUT/'official-events.jsonl').read_text().splitlines()];rows=read(OUT/'task-results.json');byid={r['id']:r for r in rows};batches=read(OUT/'adapter-evaluations.json');lineage=[];cur={}
 for e in events:
  d=e['data'];it=d.get('iteration')
  if e['event']=='on_candidate_selected':cur[it]=dict(iteration=it,parent_pool_idx=d['candidate_idx'],parent_sha256=sha(d['candidate']['temporal_skill']),parent_text=d['candidate']['temporal_skill'],selected_at=e['at'])
  if e['event']=='on_proposal_end':
   x=cur[it];s=d['new_instructions']['temporal_skill'];x.update(proposal_sha256=sha(s),proposal_at=e['at'],changes='\n'.join(difflib.unified_diff(x['parent_text'].splitlines(),s.splitlines(),fromfile='parent-skill',tofile='proposed-skill')))
  if e['event'] in ['on_candidate_accepted','on_candidate_rejected'] and it in cur:cur[it].update(official_decision=e['event'],decision=d)
 for it,x in sorted(cur.items()):
  if 'proposal_at' not in x:continue
  parent=[b for b in batches if b.get('at',0)>=x['selected_at'] and b.get('at',0)<x['proposal_at'] and b.get('capture_traces')]
  child=[b for b in batches if b.get('at',0)>=x['proposal_at'] and b.get('candidate_key')==sha(json.dumps({'temporal_skill':next(read(f)['temporal_skill'] for f in (OUT/'candidates').glob('*/candidate.json') if sha(read(f)['temporal_skill'])==x['proposal_sha256'])},sort_keys=True))]
  comparisons=[]
  if parent and child:
   pp={byid[i]['case']:byid[i] for i in parent[-1].get('task_ids',[])}
   for ident in child[0].get('task_ids',[]):
    c=byid[ident];a=pp[c['case']];ac=(a.get('score') or {}).get('checks',{});cc=(c.get('score') or {}).get('checks',{});aa=(a.get('score') or {}).get('assertions',{});ca=(c.get('score') or {}).get('assertions',{})
    comparisons.append(dict(case=c['case'],parent_task=a['id'],child_task=c['id'],parent_whole=a['metric'],child_whole=c['metric'],previously_passed_check_losses=[k for k,v in ac.items() if v and not cc.get(k)],previously_failed_check_gains=[k for k,v in ac.items() if not v and cc.get(k)],previously_passed_assertion_failures=[k for k,v in aa.items() if v and k in ca and not ca[k]],previously_passed_assertion_not_emitted=[k for k,v in aa.items() if v and k not in ca]))
  x.pop('parent_text');x['paired_sample_tradeoffs']=comparisons;lineage.append(x)
 save(OUT/'candidate-lineage.json',lineage)
if __name__=='__main__':main()
