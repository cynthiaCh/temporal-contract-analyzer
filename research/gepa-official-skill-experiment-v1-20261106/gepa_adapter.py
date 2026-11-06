"""GEPAAdapter and observable plumbing. Search/selection stay in installed GEPA."""
import json,re,time
from pathlib import Path
import gepa
from gepa import EvaluationBatch
from runtime import OUT,TRAIN,VAL,TEST,read,save,sha,frozen,run_task,usage,ensure_review,candidate_record,requests_used,reflection_lm


DESCRIPTIONS={
 'transfer-progress-composition-v4-vanilla':{
 'warm-bootstrap':'Initial current-panel progress was not restored on the tested warm-source path. Visible grounding: task initial progress and producer synchronous start.',
 'start-switch-admission':'The tested switch during source startup did not preserve the required combination of progress history and current-panel effects. Visible grounding: task navigation/audit preservation; producer start, transfer cleanup and queue consumers.',
 'accepted-after-hide':'Already-started progress completion after hiding did not retain the tested separation between stored history and current-panel output. Visible grounding: README history/display distinction and queue callbacks.',
 'frame-in-order':'Ordinary ordered completion of full progress frames lost an expected display/history outcome. Visible grounding: preserve ordinary streaming, original progress record/receive callbacks.',
 'frame-reversed':'Reversed decode completion did not preserve history and prevent display rollback together. Visible grounding: task explicitly permits out-of-order full-frame decoding.',
 'cleanup-switch':'The tested navigation cleanup handoff did not retain its existing ownership/output behavior. Visible grounding: panel release and producer synchronous detach callback.',
 'cleanup-hide':'The tested hide cleanup handoff did not retain its existing ownership/output behavior. Visible grounding: panel hide/release and producer detach callback.',
 'composed-reverse-cleanup-switch':'Combining delayed decoding with navigation cleanup lost a required effect or ownership outcome. Visible grounding: async decode, navigation and cleanup are all visible preservation requirements.',
 'retry-preserved':'The tested replacement attempt did not preserve the existing retry record/notice/current-display combination. Visible grounding: retry retains a visit and starts another physical attempt; queue consumers differ.',
 'telemetry-scope':'Diagnostic consumer behavior changed. Visible grounding: README and telemetry implementation distinguish diagnostics from panel state.',
 'record-byte-count-included':'Queue record field behavior changed without task authorization. Visible grounding: README preserves the documented record shape.'},
 'download-polling-restoration-low-cue-react18':{
 'download-retries-until-ready-once':'The active foreground preparation did not complete the tested pending-to-ready flow once. Visible grounding: maintenance task and check/retry API.',
 'download-waits-after-pending':'The scored pending interval has a waiting-state mismatch. Visible grounding: task ongoing preparation, hook loading/retryScheduled state and dialog state consumer; this is feedback, not an added status schema.',
 'download-close-clears-loading':'Closing did not clear the tested foreground waiting indicator. Visible grounding: dialog close and visible loading state.',
 'download-close-ignores-ready':'A completed response after closing produced a foreground effect that the tested lifecycle should suppress. Visible grounding: foreground close/reopen versus completion callback.',
 'download-close-ignores-pending':'A pending response after closing continued foreground work on the tested path. Visible grounding: close, scheduler and callback ownership.',
 'download-reopen-ignores-old-ready':'A response from the earlier visit affected the tested reopened visit. Visible grounding: reopen changes token/access and callback captures.',
 'download-reopen-current-completes-once':'The current reopened preparation did not complete once on the tested path. Visible grounding: task reuse and hook completed/state consumers.',
 'background-active-retries-to-ready':'The active background path lost its existing preparation behavior. Visible grounding: adjacent background component and task preservation scope.',
 'background-continuation-policy-violated':'The background lifecycle policy changed on a tested path. Visible grounding: background component is an adjacent ownership contrast, not the foreground task.'}}


def feedback(row):
    case=row['case'];d=Path(row['path'])/'jobs/j-001';tr=read(d/'trajectory-index.json');changes=read(d/'changes.json');scope=read(OUT/'protocol.json')['cases'][case]
    command_summaries=[];actual_reads=[];validations=[];source_files=scope['input_files']
    for c in tr['commands']:
        command=c['command'];out=c['output'];entry=dict(event_line=c['line'],command=command[:8000],exit_code=c['exit_code'],actual_output=out[:5000],output_truncated=len(out)>5000,command_truncated=len(command)>8000)
        if re.search(r'\b(cat|nl|sed|head|tail)\b',command) and not ('rg --files' in command and not re.search(r'\b(cat|nl|sed)\b',command)):
            actual_reads.append(dict(event_line=c['line'],command=command[:1500],candidate_paths=[p for p in source_files if p in command]))
        if re.search(r'\b(node|pytest|npm|assert)\b|--check',command):validations.append(entry)
        command_summaries.append(entry)
    score=row.get('score');diffs=[]
    if score:
        for check,passed in score['checks'].items():
            if passed:continue
            ident=check.split(':',1)[1];description=DESCRIPTIONS[case].get(ident)
            assert description,'Every train check must have grounded natural-language feedback'
            diffs.append(description)
    data=dict(Inputs=dict(original_maintenance_task=(OUT/'materials'/case/'task.md').read_text(),visible_context=(OUT/'materials'/case/'source.md').read_text()),Generated_Outputs=dict(actual_reads=actual_reads,modified_locations=[dict(path=f['path'],diff=f.get('diff','')[:18000],truncated=len(f.get('diff',''))>18000) for f in changes.get('files',[])],tool_observations=command_summaries,visible_validation=validations,delivery=dict(candidate_patch_present=bool(changes.get('files')),trustworthy_whole_task_pass=bool(score and score['whole_pass']),execution_category=row['category'])),Feedback=dict(whole_behavior_score=row['metric'],grounded_behavior_differences=diffs,original_passed_check_loss_count=len(score['original_check_losses']) if score else None,original_passed_assertion_failure_count=len(score['original_assertion_failures']) if score else None,unknowns=['Tool reads prove available observations, not correct contract understanding.','Self-written checks cover only driven event orders; a final assertion that checks passed is not sufficient.','These scores do not isolate information omission, contract error, implementation or verification as a single cause.']+(['Execution/scoring unavailable; do not infer a business obligation from this zero.'] if not score else [])))
    # Hidden names are private; natural descriptions are source-grounded above.
    serialized=json.dumps(data,ensure_ascii=False)
    forbidden=read(OUT/'private-score-identifiers.json')
    leaked=[k for k in forbidden if k in serialized]
    assert not leaked,'Private score identifier entered reflective dataset'
    return data


class Adapter:
    propose_new_texts=None
    def evaluate(self,batch,candidate,capture_traces=False):
        frozen();assert all(x['split'] in ['train','val'] for x in batch)
        if any(x['case'] in TEST for x in batch):raise RuntimeError('test supplied to optimizer')
        allowed,check=ensure_review(candidate);key,folder=candidate_record(candidate)
        calls=read(OUT/'adapter-evaluations.json');record=dict(batch_call=len(calls)+1,candidate_key=key,case_ids=[x['case'] for x in batch],capture_traces=capture_traces,at=time.time(),valid_component=allowed);calls.append(record);save(OUT/'adapter-evaluations.json',calls)
        if not allowed:
            out=[dict(invalid_component=True,validation=check) for x in batch];return EvaluationBatch(outputs=out,scores=[0.0]*len(batch),trajectories=out if capture_traces else None,num_metric_calls=0)
        used=sum(r['phase']=='opt' for r in read(OUT/'task-ledger.json'))
        if used+len(batch)>24:raise RuntimeError('Batch hard budget guard: no partial/model execution')
        rows=[run_task(x['case'],candidate['temporal_skill'],'opt') for x in batch]
        outputs=[dict(task_execution_id=r['id'],case=r['case'],metric=r['metric'],category=r['category'],skill_sha256=r['skill_sha256']) for r in rows]
        record.update(task_ids=[r['id'] for r in rows],scores=[r['metric'] for r in rows],real_task_executions=len(rows));calls=read(OUT/'adapter-evaluations.json');calls[-1]=record;save(OUT/'adapter-evaluations.json',calls)
        return EvaluationBatch(outputs=outputs,scores=[r['metric'] for r in rows],trajectories=rows if capture_traces else None,num_metric_calls=len(rows))
    def make_reflective_dataset(self,candidate,eval_batch,components_to_update):
        assert list(components_to_update)==['temporal_skill'];rows=eval_batch.trajectories;assert rows and all(r['case'] in TRAIN and r['split']=='train' for r in rows)
        data=[feedback(r) for r in rows];records=read(OUT/'reflection-datasets.json');path=OUT/'reflection-data'/('dataset-'+str(len(records)+1).zfill(2)+'.json');save(path,dict(temporal_skill=data));records.append(dict(path=str(path),task_ids=[r['id'] for r in rows],sha256=sha(path.read_bytes()),train_only=True));save(OUT/'reflection-datasets.json',records)
        return {'temporal_skill':data}


class Budget:
    def __call__(self,state):
        used=sum(r['phase']=='opt' for r in read(OUT/'task-ledger.json'));remaining=24-used;ref=requests_used();bad=any(r['phase']=='opt' and r['category']!='behavior' for r in read(OUT/'task-results.json'))
        stop=remaining<6 or ref>=6 or bad;records=read(OUT/'budget-checks.json');records.append(dict(at=time.time(),official_metric_calls=state.total_num_evals,real_task_executions=used,remaining=remaining,reflection_native_requests=ref,stop=stop,reason='unverified_execution' if bad else 'fewer_than_six_reserved_tasks' if remaining<6 else 'reflection_cap' if ref>=6 else 'continue'));save(OUT/'budget-checks.json',records);return stop


class Callbacks:
    def __getattr__(self,name):
        if not name.startswith('on_'):raise AttributeError(name)
        def callback(event):
            def safe(x):
                if isinstance(x,dict):return {str(k):safe(v) for k,v in x.items() if k not in ['state','final_state','trainset_loader','valset_loader']}
                if isinstance(x,(list,tuple,set)):return [safe(v) for v in x]
                if isinstance(x,(str,int,float,bool)) or x is None:return x
                return repr(x)
            item=dict(event=name,data=safe(event),at=time.time())
            with (OUT/'official-events.jsonl').open('a') as f:f.write(json.dumps(item,ensure_ascii=False)+'\n')
            if name=='on_proposal_end' and event.get('new_instructions'):candidate_record(event['new_instructions'])
        return callback


def optimize():
    p=frozen();assert read(OUT/'preflight.json')['status']=='PASS'
    if read(OUT/'task-ledger.json') or (OUT/'gepa-run/gepa_state.bin').exists():raise RuntimeError('Refuse automatic formal resume/replay; budget ledger retained')
    config=p['gepa_config'];result=gepa.optimize(seed_candidate={'temporal_skill':(OUT/'K0.md').read_text()},trainset=[dict(case=c,split='train') for c in TRAIN],valset=[dict(case=c,split='val') for c in VAL],adapter=Adapter(),reflection_lm=reflection_lm,reflection_prompt_template=(OUT/'REFLECTION_TEMPLATE.md').read_text(),candidate_selection_strategy='pareto',frontier_type='instance',reflection_minibatch_size=2,module_selector='round_robin',batch_sampler='epoch_shuffled',skip_perfect_score=True,perfect_score=1.0,use_merge=False,max_metric_calls=24,stop_callbacks=Budget(),callbacks=[Callbacks()],run_dir=str(OUT/'gepa-run'),seed=config['seed'],cache_evaluation=False,write_agent_state=True,track_best_outputs=True,display_progress_bar=False,use_cloudpickle=False,raise_on_exception=True,acceptance_criterion='strict_improvement',val_evaluation_policy='full_eval')
    save(OUT/'official-result.json',result.to_dict());assert result.total_metric_calls==sum(r['phase']=='opt' for r in read(OUT/'task-ledger.json'))
    skill=result.best_candidate['temporal_skill'];(OUT/'Kstar.md').write_text(skill);same=skill==(OUT/'K0.md').read_text()
    save(OUT/'selection.freeze.json',dict(at=time.time(),best_idx=result.best_idx,best_score=result.best_score,selected_sha256=sha(skill),Kstar_equals_K0=same,rule='official result.best_idx = highest full val mean, earliest pool index on tie',before_any_test=True,official_candidate_count=result.num_candidates))
    schedule=[r for r in p['test_schedule'] if not same or r['arm']=='A'];save(OUT/'test.schedule.json',schedule)
    from runtime import full_prompt
    prompts={}
    for c in TEST:
        for arm,text in [('A',(OUT/'K0.md').read_text()),('B',skill)]:
            path=OUT/'materials'/c/(arm+'-final.prompt.md');path.write_text(full_prompt(c,text));prompts[str(path)]=sha(path.read_bytes())
    save(OUT/'test-prompts.freeze.json',dict(at=time.time(),files=prompts,B_cancelled=same))
    print('OPTIMIZATION_COMPLETE '+json.dumps(dict(best_idx=result.best_idx,candidates=result.num_candidates,metric_calls=result.total_metric_calls,Kstar_equals_K0=same,test_slots=len(schedule))),flush=True)


def final_test():
    p=frozen();selection=read(OUT/'selection.freeze.json');assert not any(r['phase']=='test' for r in read(OUT/'task-ledger.json'))
    for path,h in read(OUT/'test-prompts.freeze.json')['files'].items():assert sha(Path(path).read_bytes())==h
    for slot in read(OUT/'test.schedule.json'):
        assert sha((OUT/'Kstar.md').read_bytes())==selection['selected_sha256']
        text=(OUT/('K0.md' if slot['arm']=='A' else 'Kstar.md')).read_text();run_task(slot['case'],text,'test',slot['arm'],slot['replicate'])
    save(OUT/'completion.json',dict(status='COMPLETE',at=time.time(),optimization_tasks=sum(r['phase']=='opt' for r in read(OUT/'task-ledger.json')),test_tasks=sum(r['phase']=='test' for r in read(OUT/'task-ledger.json')),reflection_native_requests=requests_used(),no_resume=True))
    print('FINAL_TEST_COMPLETE',flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['optimize','final_test']);args=parser.parse_args();globals()[args.action]()
