"""Offline A→B→C demonstration. Uses synthetic LLM responses; no model/provider."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from temporal_contract_analyzer.tempoevo_v4 import Trajectory,MODEL,CONTRACT_FIELDS
from temporal_contract_analyzer import experience_memory
from temporal_contract_analyzer.tempoevo_backend import NativeV4Backend

class SyntheticBackend:
    def execute(self,kind,payload,model,limits,directory):
        if kind=='action':
            n=int(payload['candidate_sources']['main.py'].split('=')[1])+1
            return dict(valid=True,model=MODEL,requests=1,tokens=None,candidate_sources={'main.py':'value = '+str(n)+'\n'})
        contract=dict({k:[] for k in CONTRACT_FIELDS},scope=['Public value task'],obligations=[dict(id='value',text='The public value must be 2.')],supporting_evidence=[dict(file='TASK',quote='The public value must be 2.')])
        if kind=='contract':output=contract
        elif kind=='diagnosis':output=dict(diagnosis='implementation_gap',contract_after=payload['contract_before'],routing_analysis=None,structured_delta=[],supporting_evidence=contract['supporting_evidence'],remaining_unknowns=[],explanation='Synthetic implementation-only diagnosis.')
        else:output=dict(labels=['I'],requires=['entry_snapshot'],excludes=[],rules=[dict(category='verification',body='Check the accepted value before publication.')],limitations=['Synthetic demonstration only; no empirical benefit established'])
        return dict(valid=True,model=MODEL,requests=1,tokens=None,output=output)
    def evaluate(self,kind,payload,directory):return NativeV4Backend({}).evaluate(kind,payload,directory)

if __name__=='__main__':
    root=Path(sys.argv[1]).resolve();root.mkdir()
    source=root/'public';source.mkdir();(source/'main.py').write_text('value = 0\n')
    store=root/'memory';experience_memory.initialize(store)
    loop=Trajectory(root/'trajectory');loop.prepare(dict(task='The public value must be 2.',candidate=str(source),store=str(store),mode='learning',condition='contract',visible_evaluator=dict(command=[sys.executable,str(Path(__file__).with_name('visible_checks.py'))])))
    state=loop.run(SyntheticBackend(),execute=True)
    print(json.dumps(dict(status=state['status'],valid_attempts=len(state['attempts']),root=str(root),model_calls=0,kind='synthetic_model_offline_evaluator_demo'),indent=2))
