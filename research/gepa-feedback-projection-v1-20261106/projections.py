"""Feedback projection only. No executor, scorer, model or optimizer invocation.
Research evidence is kept separately from the model-facing data returned here.
"""
import copy,hashlib,json,re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
OUT=Path(__file__).resolve().parent
TRAIN=('transfer-progress-composition-v4-vanilla','download-polling-restoration-low-cue-react18')
def read(p):return json.loads(Path(p).read_text())
def sha(x):return hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()
class ProjectionError(ValueError):pass
@dataclass
class Context:
    materials_root:Path
    allowed_run_root:Path
    arm:str
    paired_parents:dict|None=None
    def bind(self,row):
        if row['case'] not in TRAIN or row.get('split')!='train':raise ProjectionError('Only the two frozen train sources are eligible')
        folder=Path(row['path']).resolve()
        if folder.name!=row['id']:raise ProjectionError('Job identifier/path mismatch')
        if self.allowed_run_root.resolve() not in folder.parents:raise ProjectionError('Run outside this isolated arm/archive scope')
        if self.arm in ['F0','F1'] and row.get('arm')!=self.arm:raise ProjectionError('Cross-arm row')
        if row.get('category')!='behavior':raise ProjectionError('No trustworthy behavior result; stop rather than invent directional evidence')
        actual=read(folder/'manifest.json');frozen=read(self.materials_root/'protocol.json')['cases'][row['case']]
        if actual['id']!=row['id'] or actual['input_files']!=frozen['input_files']:raise ProjectionError('Wrong frozen candidate')
        ev=read(row['evaluation']);entry=ev['jobs']['j-001'];score_path=(folder/entry['result_path']).resolve()
        if score_path!=Path(row['raw_oracle']).resolve() or folder not in score_path.parents:raise ProjectionError('Score is not bound to this job')
        raw=read(score_path)
        if raw['case_id']!=row['case'] or ev.get('calibration_verdict')!='PASS' or int(raw['verdict']=='PASS')!=row['metric']:raise ProjectionError('Score/case/calibration mismatch')
        cp=Path(frozen['manifest']);cm=read(cp)
        if sha(cp.read_bytes())!=frozen['manifest_sha256'] or any(sha(Path(path).read_bytes())!=h for path,h in frozen['oracle_files'].items()):raise ProjectionError('Frozen calibration/scorer inputs changed')
        effectspec=read(cp.parent/cm['oracle']['effects'])['variants']['ungranted'];expected_checks={**{'required:'+k:raw['observed_effects'][k] is True for k in effectspec['required']},**{'forbidden:'+k:raw['observed_effects'][k] is False for k in effectspec['forbidden']}}
        if row['score']['checks']!=expected_checks or ev.get('manifest_sha256')!=frozen['manifest_sha256']:raise ProjectionError('Stale or mismatched detailed behavior record')
        for s in raw.get('schedules',{}).values():
            if s.get('runtimeError'):raise ProjectionError('Runtime error is not a behavioral difference')
        return folder,raw
    def source(self,case,path,lo,hi):
        p=self.materials_root/'materials'/case/('task.md' if path=='original task' else 'input/'+path)
        lines=p.read_text().splitlines();end=min(len(lines),hi)
        if lo<1 or lo>end:raise ProjectionError('Invalid visible-source reference')
        return dict(path=path,start_line=lo,end_line=end,visible_file_sha256=sha(p.read_bytes()),snapshot='frozen candidate start; inspect the supplied actual diff for changes')
@dataclass
class Packet:
    data:dict
    private_evidence_index:dict
    metadata:dict
class F0Projector:
    def __init__(self,context):
        self.context=context;ns=dict(OUT=context.materials_root,read=read,Path=Path,re=re,json=json)
        self.legacy=(OUT/'feedback_f0_legacy.py').read_text();exec(compile(self.legacy,str(OUT/'feedback_f0_legacy.py'),'exec'),ns);self._old=ns['feedback']
    def project(self,row,parent=None):
        self.context.bind(row)
        # Archive JSON sorts object keys. Restore the original live normalizer's
        # required/forbidden insertion order from the frozen effect specification.
        scope=read(self.context.materials_root/'protocol.json')['cases'][row['case']];cp=Path(scope['manifest']);cm=read(cp);rules=read(cp.parent/cm['oracle']['effects'])['variants']['ungranted'];ordered=copy.deepcopy(row);ordered['score']['checks']={k:row['score']['checks'][k] for k in ['required:'+x for x in rules['required']]+['forbidden:'+x for x in rules['forbidden']]}
        # Exact old function and old field order. No retrospective parent enrichment.
        d=self._old(ordered);return Packet(d,{},dict(version='F0',legacy_body_unchanged=True,additional_truncation=False))

# Research-side lookup only. No hidden key is serialized into model-facing data.
T_DESC={
'warm-bootstrap':'Ordinary startup receives the initial input in history and current presentation.',
'start-switch-admission':'Navigation during source startup preserves input-admission, history, and current-consumer behavior.',
'accepted-after-hide':'Already accepted work can complete across hiding with history and presentation assessed separately.',
'frame-in-order':'Ordinary full-result completion retains streaming history and presentation.',
'frame-reversed':'Reversed decode completion retains history without current-display rollback.',
'cleanup-switch':'Navigation triggered during cleanup retains lifecycle handoff behavior.',
'cleanup-hide':'Hiding triggered during cleanup retains lifecycle handoff behavior.',
'composed-reverse-cleanup-switch':'Delayed decoding and cleanup navigation retain their separate effects when combined.',
'retry-preserved':'Replacement within one visit retains record/notice behavior and current-result ownership.',
'telemetry-scope':'The diagnostic consumer retains its distinct reception behavior.',
'record-byte-count-included':'The public queue record shape remains within the task authorization.'}
D_DESC={
'download-retries-until-ready-once':'Active foreground preparation retries pending responses and delivers after readiness.',
'download-waits-after-pending':'The foreground waiting state remains consistent with ongoing pending preparation.',
'download-close-clears-loading':'Closing clears the foreground waiting state.',
'download-close-ignores-ready':'Late readiness does not complete a closed foreground access.',
'download-close-ignores-pending':'A late pending response does not restart work for a closed foreground access.',
'download-reopen-ignores-old-ready':'An earlier access cannot complete a reopened foreground access.',
'download-reopen-current-completes-once':'The current reopened access can still complete.',
'background-active-retries-to-ready':'The adjacent active background consumer retains its preparation behavior.',
'background-continuation-policy-violated':'The adjacent background lifecycle policy is preserved.'}

def _assertions(raw):return [(k,i,a) for k,s in raw.get('schedules',{}).items() for i,a in enumerate(s.get('assertions',[]))]
def _extra_items(actual,expected):
    if not isinstance(actual,list) or not isinstance(expected,list):return []
    rest=Counter(json.dumps(v,sort_keys=True) for v in expected);extra=[]
    for v in actual:
        key=json.dumps(v,sort_keys=True)
        if rest[key]:rest[key]-=1
        else:extra.append(v)
    return extra
class F1Projector:
    def __init__(self,context):self.context=context;self.common=F0Projector(context)
    def project(self,row,parent=None):
        folder,raw=self.context.bind(row);p=self.common.project(row);data=copy.deepcopy(p.data);case=row['case'];transfer=case.startswith('transfer-');descriptions=T_DESC if transfer else D_DESC
        index={};facts=[]
        def origin(pointer,details=None):
            key='evidence-'+sha(row['id']+'|'+sha(Path(row['raw_oracle']).read_bytes())+'|'+pointer)[:16]
            index[key]=dict(job_id=row['id'],case=case,raw_score_path=row['raw_oracle'],raw_score_sha256=sha(Path(row['raw_oracle']).read_bytes()),json_pointer=pointer,details=details)
            return key
        def sources():
            if transfer:return [self.context.source(case,'original task',1,6),self.context.source(case,'README.md',8,26),self.context.source(case,'src/progress-source.js',8,30),self.context.source(case,'src/queue.js',8,19),self.context.source(case,'src/transfer.js',3,17),self.context.source(case,'src/panel.js',10,25)]
            return [self.context.source(case,'original task',1,5),self.context.source(case,'src/usePreparation.js',1,50),self.context.source(case,'src/DownloadDialog.jsx',1,50),self.context.source(case,'src/BackgroundExportPanel.jsx',1,60)]
        bindings=sources();covered=set()
        # Research-only instrumentation binding chooses the assessed surface. Private IDs
        # are never serialized; the event facts must independently match the raw trace.
        if transfer:
            for sk,ai,a in _assertions(raw):
                if a.get('passed') is not False:continue
                trace=raw['schedules'][sk].get('trace',[])
                for extra in _extra_items(a.get('actual'),a.get('expected')):
                    if not isinstance(extra,dict):continue
                    surface='progress.audit' if a.get('id','').endswith('.audit') else 'progress.visible' if a.get('id')=='retry.same-visit-no-rollback' else None
                    if surface is None:continue
                    matching=[(i,e) for i,e in enumerate(trace) if e.get('type')==surface and all(e.get(k)==extra.get(k) for k in ['fileId','attemptId','seq'])]
                    if not matching:continue
                    ti,event=matching[-1];prefix=trace[:ti];emits=[(j,e) for j,e in enumerate(prefix) if e.get('type')=='feed.emit' and e.get('fileId')==event.get('fileId') and e.get('seq')==event.get('seq')]
                    if not emits:continue
                    ei,emitted=emits[-1];assertref=origin(f'/schedules/{sk}/assertions/{ai}',dict(raw_assertion_id=a.get('id')))
                    if event['type']=='progress.audit' and emitted.get('deferred') is False:
                        navigations=[(j,e) for j,e in enumerate(prefix[:ei]) if e.get('type')=='host.select' and e.get('fileId')!=event.get('fileId')]
                        if not navigations:continue
                        ni,nav=navigations[-1]
                        starts=[(j,e) for j,e in enumerate(prefix[:ni]) if e.get('type')=='feed.start' and e.get('fileId')==event.get('fileId')]
                        if not starts:continue
                        si,_=starts[-1]
                        initial_progress=[(j,e) for j,e in enumerate(prefix[:ni]) if e.get('type') in ['progress.audit','progress.visible'] and e.get('fileId')==event.get('fileId') and j>si]
                        if not initial_progress:continue
                        pi,_=initial_progress[-1]
                        facts.append(dict(evidence=[assertref,origin(f'/schedules/{sk}/trace/{si}'),origin(f'/schedules/{sk}/trace/{pi}'),origin(f'/schedules/{sk}/trace/{ni}'),origin(f'/schedules/{sk}/trace/{ei}'),origin(f'/schedules/{sk}/trace/{ti}')],observed_events=['The earlier source started and produced progress before the observed navigation.','A different resource was selected after that initial progress.','The earlier source emitted a new input after that selection.','That new input was appended to the earlier operation history.'],confirmed_order=[[0,1],[1,2],[2,3]],actual_difference='There is an extra history entry from a newly emitted input of the earlier source; this is not merely completion of work accepted before navigation.',direction=['extra'],requirement=dict(task_explicit='Restore the initial progress and prevent display rollback while preserving navigation, cleanup and audit behavior.',source_fact='The source can emit synchronously, release removes reception, and recording and current presentation are distinct consumers.',scored_comparison='The trusted behavior record flags the additional history entry after navigation.',scope='Do not generalize to suppress history for already accepted work that completes later.'),source_binding_ids=list(range(len(bindings))),cause_hypotheses=['An input-admission or lifecycle-handoff window may be involved.'],unknowns=['The trace has no call-return markers and does not independently establish the exact candidate call stack, a guard placement or a patch.']))
                        covered.add(sk)
                    elif event['type']=='progress.visible' and emitted.get('deferred') is True:
                        newer=[(j,e) for j,e in enumerate(prefix[ei+1:],ei+1) if e.get('type')=='progress.visible' and e.get('fileId')==event.get('fileId') and e.get('attemptId')!=event.get('attemptId')]
                        if not newer:continue
                        nj,newer_event=newer[-1]
                        replacements=[e for e in prefix[ei:nj+1] if e.get('type')=='queue.record' and e.get('kind')=='retry' and e.get('attemptId')==newer_event.get('attemptId')]
                        if not replacements:continue
                        facts.append(dict(evidence=[assertref,origin(f'/schedules/{sk}/trace/{ei}'),origin(f'/schedules/{sk}/trace/{nj}'),origin(f'/schedules/{sk}/trace/{ti}')],observed_events=['An input of an earlier physical operation was accepted and its decode remained pending.','A replacement operation produced current presentation for the same resource.','The earlier decode then completed and updated that current presentation.'],confirmed_order=[[0,1],[1,2]],actual_difference='A result owned by the earlier physical operation was displayed after the replacement result. History completion and current presentation are separate effects.',direction=['ownership_mismatch','order_error'],requirement=dict(task_explicit='Full results must not roll current presentation backward; retry and other existing behavior must be preserved.',source_fact='Retry replaces a physical operation within the same visit, while a later resource selection creates another visit.',scored_comparison='The trusted record flags the earlier-operation presentation after replacement.',scope='A recorded history result is not automatically invalid merely because it is no longer eligible for current presentation.'),source_binding_ids=list(range(len(bindings))),cause_hypotheses=['The identity or ordering scope used for presentation may be narrower than the lifecycle relationship exercised.'],unknowns=['The trace alone does not show whether the execution agent understood this relationship or how it should be implemented.']))
                        covered.add(sk)
        else:
            for sk,s in raw.get('schedules',{}).items():
                snap=s.get('afterFirstPending');later=s.get('afterSecondPending');final=s.get('final')
                if not isinstance(snap,dict) or not isinstance(final,dict):continue
                if snap.get('retryScheduled') is True and snap.get('loading') is False and not snap.get('completed'):
                    failed=[(i,a) for i,a in enumerate(s.get('assertions',[])) if a.get('passed') is False]
                    if not any(isinstance(a.get('actual'),dict) and isinstance(a.get('expected'),dict) and a['actual'].get('waits') is False and a['expected'].get('waits') is True for i,a in failed) or not final.get('completed'):continue
                    refs=[origin(f'/schedules/{sk}/afterFirstPending'),origin(f'/schedules/{sk}/final')]+[origin(f'/schedules/{sk}/assertions/{i}',dict(raw_assertion_id=a.get('id'))) for i,a in failed]
                    facts.append(dict(evidence=refs,observed_events=['The snapshot after a pending response has a retry scheduled, no delivered completion, and the waiting/loading flag off.','A later snapshot shows preparation eventually completed.'],confirmed_order=[[0,1]],order_basis='Ordered snapshot stages in the trusted run, not timestamped callback tracing; no finer callback order is inferred.',actual_difference='Ongoing pending preparation lacks the waiting indication assessed by the trusted record, even though retry and eventual completion still occur.',direction=['missing'],requirement=dict(task_explicit='Keep checking pending preparation and deliver only after readiness.',source_fact='The hook exposes loading and retry state, and the dialog consumes that state. The adjacent consumer gives a lifecycle contrast, not an automatic foreground specification.',scored_comparison='The trusted record distinguishes successful eventual completion from the missing pending waiting indication.',scope='The precise meaning of the waiting flag between requests must still be judged from the original task and visible project evidence; the score is not a new business specification.'),source_binding_ids=list(range(len(bindings))),cause_hypotheses=['The callback transition may distinguish request completion from preparation completion differently from the assessed waiting behavior.'],unknowns=['The original short task does not explicitly define the waiting flag schema or all scheduler reentry guarantees.']))
                    covered.add(sk)
        # Never silently discard an unrecognized failing relationship.
        for sk,s in raw.get('schedules',{}).items():
            failed=[(i,a) for i,a in enumerate(s.get('assertions',[])) if a.get('passed') is False]
            if not failed or sk in covered:continue
            facts.append(dict(evidence=[origin(f'/schedules/{sk}/assertions/{i}',dict(raw_assertion_id=a.get('id'))) for i,a in failed],observed_events=['The trusted current-run observation contains a behavioral comparator mismatch.'],confirmed_order=[],actual_difference='The available structured projection does not establish a safe effect-specific direction for this comparator.',direction=[],requirement=dict(task_explicit='Use the original task and visible source; do not infer a new obligation from a failure label.'),source_binding_ids=list(range(len(bindings))),cause_hypotheses=[],unknowns=['Direction, relevant event order and effect ownership require additional source-bound interpretation; no missing/extra/early/late category is forced.']))
        for fact in facts:fact['cause_hypotheses']=[dict(hypothesis=h,support='cited event evidence and source bindings; not a unique cause') for h in fact['cause_hypotheses']]
        positives=[]
        for key,passed in row['score']['checks'].items():
            if not passed:continue
            ident=key.split(':',1)[1]
            if ident not in descriptions:raise ProjectionError('No source-bound behavior description')
            positives.append(dict(behavior=descriptions[ident],observation='Passed in this current execution on the assessed path; not a universal proof.',comparison_object='current execution; no paired parent supplied' if parent is None else 'current execution',evidence=origin('/observed_effects/'+ident),source_binding_ids=list(range(len(bindings)))))
        comparison=dict(against_unchanged_start=dict(passed_check_losses=len(row['score']['original_check_losses']),passed_assertion_failures=len(row['score']['original_assertion_failures']),meaning='These counts compare with the unchanged candidate source, not a parent skill execution.'),against_parent_execution=dict(available=False,gained=None,lost=None,reason='No paired parent execution was supplied. Do not interpret unavailable as zero.'))
        if parent is not None:
            self.context.bind(parent)
            if not self.context.paired_parents or self.context.paired_parents.get(row['id'])!=parent['id']:raise ProjectionError('Unregistered or stale paired parent')
            if parent['case']!=case:raise ProjectionError('Cross-case parent')
            a=parent['score']['checks'];b=row['score']['checks'];g=[descriptions[k.split(':',1)[1]] for k,v in a.items() if not v and b.get(k)];lost=[descriptions[k.split(':',1)[1]] for k,v in a.items() if v and not b.get(k)];comparison['against_parent_execution']=dict(available=True,comparison='Explicit same-arm same-case paired execution only; no lookup of other candidate history.',parent_skill_sha256=parent['skill_sha256'],current_skill_sha256=row['skill_sha256'],gained=g,lost=lost)
        validations=[]
        for v in data['Generated_Outputs']['visible_validation']:
            cmd=v['command'];kind='unclassified'
            if 'node --check' in cmd:kind='syntax or compound command; inspect original output'
            elif 'assert' in cmd or "<<'" in cmd:kind='behavioral probe or compound command; scope is only what it drives'
            elif 'git diff --check' in cmd:kind='format check, not behavior'
            validations.append(dict(event_line=v['event_line'],tool_observation_reference='same event_line in tool_observations',classification=kind,whole_shell_exit_code=v['exit_code'],per_subcommand_exit_codes='not separately captured; do not infer all subcommands failed or passed'))
        data['Generated_Outputs']['visible_validation']=validations
        data['Feedback']=dict(whole_behavior_score=row['metric'],directional_observations=facts,preserved_current_behaviors=positives,comparison_objects=comparison,visible_source_bindings=bindings,unknowns=['Observed events, scored comparator differences, visible requirements and causal hypotheses are distinct.','Passing a selected path does not establish all combinations.','No patch or root cause follows uniquely from these observations.','Only the current train record is projected; rejected-child history is not automatically added.'])
        text=json.dumps(data,ensure_ascii=False)
        if any(k in text for k in read(self.context.materials_root/'private-score-identifiers.json')):raise ProjectionError('Private scoring identifier escaped projection')
        return Packet(data,index,dict(version='F1',additional_truncation=False,validation_bodies_deduplicated=True,observations=len(facts),preserved_behaviors=len(positives),unresolved_directions=sum(not f['direction'] for f in facts),raw_vectors_or_reference_repairs_forwarded=False))
