"""Same registry conversion as the reused controller, with a truthful version label."""
import time
from archive import save,sha
from toolflow import freeze_entry,canonical
import pilot
A=pilot.A

def main():
 pilot.check();assert not (A/'library-freeze.json').exists()
 assert pilot.read(A/'development/admission.json')['eligible']
 c=pilot.read(A/'development/experience-object.json');text=(A/'development/experience.md').read_text()
 entry=freeze_entry({'text':text,'requires':c['requires'],'excludes':c['excludes']},pilot.approved('D')['primary_class'])
 entry['version']='query-headroom-fresh-rules-1'
 entry['sha256']=pilot.runner.backend.sha(canonical({k:v for k,v in entry.items() if k!='sha256'}))
 save(A/'frozen-library.json',[entry])
 save(A/'registry-provenance.json',{'source':'development/experience-object.json','text_sha256':entry['text_sha256'],
  'operation':'Exact generated body and predicates projected through existing freeze_entry; management version label names this query batch, not the legacy transfer helper.',
  'no_rule_or_routing_change':True,'no_prior_experience_seed':True,'production_admitted':False})
 files={str(f):sha(f) for f in (A/'development').rglob('*') if f.is_file()}
 for f in ['frozen-library.json','registry-provenance.json','freeze_query_library.py']:files[str(A/f)]=sha(A/f)
 save(A/'library-freeze.json',{'time':time.time(),'files':files,'entries':1,'no_learning_after_this_point':True})
 print('LIBRARY FROZEN',entry['version'],entry['text_sha256'],flush=True)

if __name__=='__main__':main()
