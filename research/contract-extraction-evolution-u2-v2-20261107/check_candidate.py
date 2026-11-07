"""Mechanical candidate boundary checks; semantic review recorded separately."""
import json,re,difflib
from run import OUT,read,save,sha,frozen

def main():
 frozen();rec=read(OUT/'runs/reflect-1/receipt.json');raw=(OUT/'runs/reflect-1/raw-answer.txt').read_text();blocking=[]
 if rec['status']!='completed':blocking.append('reflection generation failed')
 obj=json.loads(raw) if raw.strip() else {};skill=obj.get('skill');changes=obj.get('changes')
 if not isinstance(skill,str) or not skill.strip() or len(skill)>4000:blocking.append('missing/empty/overlength skill')
 if not isinstance(changes,list) or any(not isinstance(x,dict) or set(x)!={'gap','change','expected_action'} or any(not isinstance(v,str) or not v.strip() for v in x.values()) for x in changes):blocking.append('changes malformed')
 if rec.get('native',{}).get('started')!=1 or rec.get('native',{}).get('tool_attempts') or rec.get('tools'):blocking.append('reflection was not single-request tool-free')
 forbidden=r'U2|download-polling|usePreparation|DownloadDialog|BackgroundExportPanel|checkPreparation|schedulePreparationRetry|cancelPreparationRetry|retryScheduled|\bloading\b|\bcompleted\b|\bpending\b|\bready\b|\btoken\b|src/|\.jsx?\b|O[1-7]\b|T[1-4]\b|package\.json|poll-until-ready|download-waits|reference/|e-0f86'
 matches=re.findall(forbidden,skill or '',re.I)
 if matches:blocking.append('case/source/answer identifiers in candidate')
 if isinstance(skill,str):
  (OUT/'contract_extraction_K1.md').write_text(skill)
  (OUT/'skill.diff').write_text(''.join(difflib.unified_diff((OUT/'contract_extraction_K0.md').read_text().splitlines(True),skill.splitlines(True),fromfile='contract_extraction_K0.md',tofile='contract_extraction_K1.md')))
 save(OUT/'skill-changes.json',{'changes':changes,'unaltered_model_candidate':True,'raw_output':str(OUT/'runs/reflect-1/raw-answer.txt')})
 result={'mechanical_status':'PASS' if not blocking else 'BLOCK','blocking':blocking,'identifier_hits':matches,'skill_sha256':sha(skill or ''),'same_as_K0':skill==(OUT/'contract_extraction_K0.md').read_text(),'candidate_unedited':True,'semantic_scope_review':'pending; no K1 execution authorized by this mechanical check alone'}
 save(OUT/'K1-boundary-review.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
