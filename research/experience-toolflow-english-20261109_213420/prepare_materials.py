"""Deterministic English material builder. No model, scorer, runner or scheduler."""
import ast,hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent
from citations import catalog,schema,INSTRUCTIONS,fingerprint
from qualifiers import GUIDANCE,cues
from toolflow import PREDICATES,canonical,digest,maintenance_prompt,reflection_prompt
from experience_translations import RULES,render
from english_validation import require_english_material

def read(p):return json.loads(Path(p).read_text())
def save(p,x):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sources():
 root=A/'materials/candidate'
 result={str(f.relative_to(root)):f.read_text() for f in root.rglob('*') if f.is_file() and f.suffix in ['.md','.py']}
 result['TASK']=(A/'materials/task.md').read_text();return result

def main():
 manifest=read(A/'source-manifest.json');parent=Path(manifest['source_batch']);library=[];lineage=[]
 for entry in read(parent/'frozen-library.json'):
  primary=entry['primary_class'];text=render(primary);new={**entry,'text':text,'version':entry['version']+'-english-1','text_sha256':digest(text)}
  new['sha256']=digest(canonical({k:v for k,v in new.items() if k!='sha256'}));library.append(new)
  folder=A/'experience'/primary;folder.mkdir(parents=True,exist_ok=True);(folder/'experience.md').write_text(text)
  old_chunks=re.split(r'(?m)^R\d{2}[^\n]*\n',entry['text'])[1:];assert len(old_chunks)==len(RULES[primary])
  records=[]
  for i,((category,body),original) in enumerate(zip(RULES[primary],old_chunks),1):
   records.append({'rule_id':'R%02d'%i,'category':category,'parent_body_sha256':digest(original.strip()),'english_body_sha256':digest(body),'review':'AI-assisted execution-agent translation review; no independent human approval','meaning_changes_intended':False})
  save(folder/'translation-review.json',{'origin':'English translation derived by execution agent; not raw model output or a newly trained candidate','parent_registry_version':entry['version'],'parent_entry_sha256':entry['sha256'],'parent_text_sha256':entry['text_sha256'],'english_text_sha256':new['text_sha256'],'requires_unchanged':new['requires']==entry['requires'],'excludes_unchanged':new['excludes']==entry['excludes'],'primary_class_unchanged':new['primary_class']==entry['primary_class'],'rules':records,'limits':'Translation creates new experimental wording. Historical scores do not validate the English wording. No new model or repair run has been performed.'})
  lineage.append({'primary_class':primary,'source_registry':str(parent/'frozen-library.json'),'parent_entry_sha256':entry['sha256'],'parent_text_sha256':entry['text_sha256'],'translated_entry_sha256':new['sha256'],'translated_text_sha256':new['text_sha256'],'status':'DERIVED_ENGLISH_TRANSLATION_NOT_EFFECT_VALIDATED','production_enabled':False})
 save(A/'frozen-library.json',library);save(A/'translation-lineage.json',lineage)
 src=sources();cat=catalog(src);save(A/'materials/source-catalog.json',cat);save(A/'materials/extraction.schema.json',schema(cat,read(A/'extraction.schema.json')))
 structure=[]
 for f in sorted((A/'materials/candidate').rglob('*.py')):
  tree=ast.parse(f.read_text());structure.append({'file':str(f.relative_to(A/'materials/candidate')),'classes':[{'name':n.name,'line':n.lineno} for n in ast.walk(tree) if isinstance(n,ast.ClassDef)],'functions':[{'name':n.name,'line':n.lineno} for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]})
 astinfo={'status':'parsed','summary':structure,'limitations':'Python AST structure only; no temporal-policy inference; no AST match does not imply a mechanism is absent.'};save(A/'materials/ast.json',astinfo)
 public={'TASK':src['TASK'],'taxonomy':read(A/'taxonomy.json')['classes'],'predicates':PREDICATES,'AST':astinfo,'source_catalog':cat,'qualifier_cues':cues(src['TASK'],cat)}
 save(A/'materials/public-analysis-material.json',public)
 prefix='Write all generated prose in English. Preserve exact source quotations, source-span IDs, predicate keys and other opaque identifiers. TASK is virtual text in this prompt, not /workspace/TASK. Read current candidate files separately.\n'
 prompt=prefix+GUIDANCE+INSTRUCTIONS+json.dumps(public,ensure_ascii=False)
 assert all(entry['text'] not in prompt for entry in library)
 (A/'prompts/preanalysis.md').write_text(prompt)
 task=src['TASK'];contract=(A/'materials/automatic-contract.md').read_text();common=maintenance_prompt(task,contract)
 (A/'prompts/maintenance-AUTO.md').write_text(common)
 for entry in library:(A/('prompts/maintenance-with-'+entry['primary_class']+'.md')).write_text(maintenance_prompt(task,contract,entry['text']))
 (A/'prompts/reflection-compatibility-template.md').write_text(reflection_prompt({'status':'EMPTY_TEMPLATE_NOT_MODEL_INPUT','training_material':'Insert an authorized, source-pinned English training payload; no test feedback.'}))
 save(A/'protocol.json',{'version':'english-research-materials-1','status':'PREPARED_NOT_EXECUTED','authorization':'Translate model-visible prompts and associated material into English; offline validation only.','source_batch':str(parent),'model_calls':0,'new_scoring_calls':0,'paid_execution_entry_point':None,'future_models':{'extract':{'model':'gpt-6-sol','effort':'low','requests':12,'seconds':600},'repair':{'model':'gpt-5.6-terra','effort':'low','requests':24,'seconds':600},'reflect':{'model':'gpt-5.6-terra','effort':'medium','requests':12,'seconds':600}},'concurrency':1,'language':'English for generated prose, taxonomy labels, predicate definitions, shared instructions and experience bodies; preserve verbatim source evidence and opaque keys.','unchanged':'Predicate keys, class IDs, required/excluded premises, conservative routing, output schema limits, models and resource limits.','taxonomy_field_change':'name_zh becomes name_en; class definitions and mechanism lists retain meaning.','translation_identity':'English experience versions and hashes are new. Originals remain frozen. Translation is execution-agent-derived, not a new model candidate.','reflection_interfaces':'Current query rules-object instructions are training-only. The old toolflow reflection helper is translated for compatibility and is not a replacement for the repaired rules-object protocol.','maintenance_examples':'Both with-experience prompts are rendering fixtures only. Future execution must use an admitted analysis and route 0 or 1 entry; these examples do not constitute selection or authorization.','historical_analysis':'English historical Contract/analysis are reused only for offline prompt and route regression checks. No new extraction, route observation or effectiveness result.','production_update':False,'create_commit':False})
 for folder in [A/'prompts',A/'experience',A/'materials']:
  for f in folder.rglob('*'):
   if f.is_file() and f.suffix in ['.md','.json','.py']:
    require_english_material(f.read_text(),str(f.relative_to(A)))
 print('Prepared English-only model material; no model or scoring calls')

if __name__=='__main__':main()
