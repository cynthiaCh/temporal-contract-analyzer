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
