"""Offline application of pre-reflection frozen acceptance criteria."""
from pathlib import Path
import json,time
A=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text())
def save(n,d):(A/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
rows=read(A/'actual-schedule.json');assert len(rows)==6 and not (A/'acceptance.json').exists()
vectors=read(A/'behavior-vectors.json');targets=read(A/'training-targets.json')['targets'];evidence=read(A/'experience-evidence.json');pairs=[]
for i in [1,2]:
 a=next(v for v in vectors if v['slot']==f'base-{i}');b=next(v for v in vectors if v['slot']==f'reval-{i}');ev=evidence[b['slot']]
 gains=[k for k in targets if not a['effects'].get(k) and b['effects'].get(k)]
 losses=[k for k,v in a['effects'].items() if v and k not in a['forbidden'] and not b['effects'].get(k)]
 common_loss=[k for k,v in a['assertions'].items() if v and k in b['assertions'] and not b['assertions'][k]]
 absent=[k for k,v in a['assertions'].items() if v and k not in b['assertions']]
 pairs.append({'repeat':i,'target_gains':gains,'baseline_required_losses':losses,'baseline_common_assertion_losses':common_loss,'baseline_passed_assertions_absent':absent,'original_required_losses':b['required_losses_vs_original'],'original_common_assertion_losses':b['common_assertion_losses_vs_original'],'forbidden':b['forbidden'],'valid':b['infrastructure_valid'] and b['scoring_valid'],'business_patch_changed':any(x.startswith('src/') for x in b['file_changes'].get('changed',[])),'experience_applied':ev['applied'],'verification_observed':ev['verified_by_agent'],'unsupported_policy':ev['unsupported_policy'],'other_confirmed_preservation_loss':ev['confirmed_preservation_loss'],'conditional_absent_assertions_review':ev['conditional_assertions_review']})
actual_gain=any(p['target_gains'] and p['business_patch_changed'] and p['experience_applied'] for p in pairs)
no_loss=all(not(p['baseline_required_losses'] or p['baseline_common_assertion_losses'] or p['original_required_losses'] or p['original_common_assertion_losses'] or p['forbidden'] or p['unsupported_policy'] or p['other_confirmed_preservation_loss']) for p in pairs)
accepted=actual_gain and no_loss and all(p['valid'] and p['experience_applied'] and p['verification_observed'] and p['conditional_absent_assertions_review']=='PASS' for p in pairs)
save('acceptance.json',{'accepted':bool(accepted),'AI_assisted':True,'independent_human_approval':False,'criteria':'PLAN.md frozen before reflection','actual_target_gain':actual_gain,'no_confirmed_preservation_loss_or_unsupported_policy':no_loss,'pairs':pairs,'model_seed_equivalence_claim':False,'no_experience_edits':True})
if not accepted:
 done={x['slot'] for x in rows};save('stop.json',{'reason':'一次反思未找到可接纳同题经验','time':time.time(),'unstarted':[s for s in read(A/'schedule.json')['slots'] if s['slot'] not in done],'no_second_reflection_or_rerun':True})
print(json.dumps(read(A/'acceptance.json'),ensure_ascii=False,indent=2))
