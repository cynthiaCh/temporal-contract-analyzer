"""Official GEPA adapter contract, with a fail-closed source gate.
The executor/reflection endpoints are injected, never instantiated by this module.
No official optimizer is run by import or by offline validation.
"""
from projections import F0Projector,F1Projector,sha
from guards import admission,skill_boundary,AdmissionBlocked
class ProjectionAdapter:
    propose_new_texts=None
    def __init__(self,arm,context,ledger,task_runner=None,review_provider=None):
        if arm not in ['F0','F1']:raise ValueError(arm)
        self.review_provider=review_provider;self.arm=arm;self.context=context;self.ledger=ledger;self.task_runner=task_runner;self.projector=(F0Projector if arm=='F0' else F1Projector)(context);self.research_packets=[]
    def evaluate(self,batch,candidate,capture_traces=False):
        split=admission()  # before any executor, model endpoint, budget charge or import
        allowed=skill_boundary(candidate,self.review_provider(candidate) if self.review_provider else None)
        if not allowed['allow_execution']:raise AdmissionBlocked('Candidate not reviewed; no task execution')
        if not batch or any(x['split'] not in ['train','val'] or x['case'] not in split[x['split']] for x in batch):raise AdmissionBlocked('Batch split mismatch/test supplied to optimizer')
        if self.task_runner is None:raise AdmissionBlocked('No authorized unchanged executor bridge supplied')
        self.ledger.reserve_task_batch(len(batch));rows=[]
        for task in batch:
            r=self.task_runner(task,candidate,self.arm)
            if r['arm']!=self.arm or r['case']!=task['case']:raise AdmissionBlocked('Runner association mismatch')
            rows.append(r)
        self.ledger.account_metrics(len(rows))
        from gepa import EvaluationBatch
        return EvaluationBatch(outputs=[dict(id=r['id'],metric=r['metric']) for r in rows],scores=[r['metric'] for r in rows],trajectories=rows if capture_traces else None,num_metric_calls=len(rows))
    def make_reflective_dataset(self,candidate,eval_batch,components_to_update):
        if list(components_to_update)!=['temporal_skill']:raise AdmissionBlocked('Wrong optimized component')
        data=[]
        for row in eval_batch.trajectories or []:
            if row.get('arm')!=self.arm or row.get('split')!='train' or row.get('skill_sha256')!=sha(candidate['temporal_skill']):raise AdmissionBlocked('Cross-arm or non-train reflection')
            packet=self.projector.project(row,parent=None);data.append(packet.data);self.research_packets.append(packet)
        return {'temporal_skill':data}
