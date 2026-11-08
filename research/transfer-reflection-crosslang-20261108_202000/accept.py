"""Apply pre-reflection frozen behavioral acceptance; no model calls."""
from pathlib import Path
import json,hashlib,time
A=Path(__file__).resolve().parent
read=lambda n:json.loads((A/n).read_text())
assert len(read('actual-schedule.json'))==9 and not (A/'acceptance.json').exists()
vs=read('behavior-vectors.json');targets=read('training-targets.json')['targets'];evidence=read('experience-evidence.json');pairs=[]
for i in [1,2]:
 a=next(v for v in vs if v['slot']==f'js-base-{i}');b=next(v for v in vs if v['slot']==f'js-exp-{i}');ev=evidence[b['slot']]
 gained=[k for k in targets if not a['effects'].get(k) and b['effects'].get(k)];lost=[k for k,v in a['assertions'].items() if v and not b['assertions'].get(k)];lost_effects=[k for k,v in a['effects'].items() if k!='record-byte-count-included' and v and not b['effects'].get(k)]
 pairs.append({'repeat':i,'target_gains':gained,'baseline_passed_assertions_lost':lost,'baseline_required_effects_lost':lost_effects,'original_passed_assertions_lost':b['assertions_lost_vs_original'],'business_files_changed':b['changed_original_files'],'forbidden':b['observed_forbidden_effects'],'valid':b['infrastructure_valid'] and b['scoring_valid'],'experience_applied_to_patch':ev['applied'],'experience_actually_verified':ev['verified_by_agent'],'unsupported_policy':ev['unsupported_policy']})
actual_gain=any(p['target_gains'] and p['business_files_changed'] and p['experience_applied_to_patch'] for p in pairs)
no_loss=all(not (p['baseline_passed_assertions_lost'] or p['baseline_required_effects_lost'] or p['original_passed_assertions_lost'] or p['forbidden'] or p['unsupported_policy']) for p in pairs)
accepted=bool(actual_gain and no_loss and all(p['valid'] and p['experience_applied_to_patch'] and p['experience_actually_verified'] for p in pairs))
d={'accepted':accepted,'time':time.time(),'frozen_rule':'PLAN.md prior to reflection; no criteria changed','actual_target_gain':actual_gain,'no_confirmed_preservation_loss_or_unsupported_policy':no_loss,'pairs':pairs,'AI_assisted':True,'human_approval':False,'no_random_sampling_seed_claim':True}
(A/'acceptance.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
if not accepted:
 done={r['slot'] for r in read('actual-schedule.json')};(A/'stop.json').write_text(json.dumps({'reason':'一次反思未找到可接纳经验','time':time.time(),'unstarted':[s for s in read('schedule.json')['slots'] if s['slot'] not in done],'no_second_reflection_or_retry':True},ensure_ascii=False,indent=2)+'\n')
print(json.dumps(d,ensure_ascii=False,indent=2))
