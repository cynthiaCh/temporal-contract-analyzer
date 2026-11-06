"""Read-only post-run behavior/control/cost audit. No model calls."""
from collections import Counter
from datetime import datetime
from pathlib import Path
import json
from run import OUT,REPO,DEV,HOLD,read,save,sha,frozen,normalize


def seconds(a,b):
    try:return (datetime.fromisoformat(b.replace('Z','+00:00'))-datetime.fromisoformat(a.replace('Z','+00:00'))).total_seconds()
    except (TypeError,ValueError,AttributeError):return None


def trace(directory):
    events=[];tools=[];commands=[];messages=[];errors=[];receipts=[]
    for n,l in enumerate((directory/'events.jsonl').read_text().splitlines(),1):
        e=json.loads(l)
        if e.get('type')=='turn.completed':receipts.append(e.get('usage',{}))
        if e.get('type') in ['turn.failed','error']:errors.append(dict(line=n,event=e))
        if e.get('type')!='item.completed':continue
        i=e.get('item',{});kind=i.get('type')
        if kind=='agent_message':messages.append(dict(line=n,text=i.get('text','')))
        elif kind=='error':errors.append(dict(line=n,item=i))
        elif kind not in ['reasoning',None]:
            tools.append(dict(line=n,kind=kind,item=i))
            if kind=='command_execution':commands.append(dict(line=n,command=i.get('command'),exit_code=i.get('exit_code'),output=i.get('aggregated_output','')))
    path=directory/'control/hook-events.jsonl';hooks=[json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []
    counts=Counter(h['event'].get('hook_event_name') for h in hooks);posts=[h['event'] for h in hooks if h['event'].get('hook_event_name')=='PostModelRequest'];request_usage={k:sum((e.get('token_usage') or {}).get(k,0) for e in posts) for k in ['input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens']}
    suffix=False;suffix_usage=Counter();suffix_requests=0
    for h in hooks:
        if h['decision']=='continue-same-session':suffix=True
        if suffix and h['event'].get('hook_event_name')=='PostModelRequest':
            suffix_requests+=1;suffix_usage.update({k:(h['event'].get('token_usage') or {}).get(k,0) for k in ['input_tokens','cached_input_tokens','output_tokens']})
    control=dict(event_counts=dict(counts),session_ids=sorted({h['session_id'] for h in hooks if h.get('session_id')}),turn_ids=sorted({h['turn_id'] for h in hooks if h.get('turn_id')}),model_request_attempts=counts['PreModelRequest'],post_model_attempts=len(posts),request_statuses=dict(Counter(e.get('status') for e in posts)),request_usage=request_usage,decisions=dict(Counter(h['decision'] for h in hooks)),feedback_characters=sum(len(h.get('reason','')) for h in hooks if h['decision'] in ['continue-with-observation','deny-edit-for-evidence','continue-same-session']),hook_seconds=sum(h.get('controller_seconds',0) for h in hooks),stop_continuation_suffix_requests=suffix_requests,stop_continuation_suffix_usage=dict(suffix_usage),post_tools_missing_exit_code=sum(h['event'].get('hook_event_name')=='PostToolUse' and h.get('exit_code') is None for h in hooks),state=read(directory/'control/state.json') if (directory/'control/state.json').exists() else None)
    return dict(commands=commands,tools=tools,messages=messages,errors=errors,terminal_receipts=receipts,control=control,hook_events_path=str(path))


def inner_shell(command):
    import shlex
    try:
        parts=shlex.split(command)
        return parts[-1] if '-lc' in parts or '-c' in parts else command
    except ValueError:return command


def costs(rows):
    return dict(sessions=len(rows),input_tokens=sum((r.get('usage') or {}).get('input_tokens',0) for r in rows),cached_input_tokens=sum((r.get('usage') or {}).get('cached_input_tokens',0) for r in rows),output_tokens=sum((r.get('usage') or {}).get('output_tokens',0) for r in rows),model_seconds=round(sum(r.get('model_seconds') or 0 for r in rows),3),tool_calls=sum(r['tool_calls'] for r in rows),model_request_attempts=sum(r['control']['model_request_attempts'] for r in rows),controller_hook_seconds=round(sum(r['control']['hook_seconds'] for r in rows),4),controller_feedback_characters=sum(r['control']['feedback_characters'] for r in rows),stop_continuations=sum(r['control']['decisions'].get('continue-same-session',0) for r in rows),edit_gate_denials=sum(r['control']['decisions'].get('deny-edit-for-evidence',0) for r in rows),shell_failures=sum(len(r['shell_failures']) for r in rows))


def main():
    p=frozen();base=read(OUT/'results.json');ledger=read(OUT/'invocations.json');selected=read(OUT/'selected.freeze.json');assert len(ledger)<=18
    traces=[];rows=[];evidence=['# 实际工具、控制事件、补丁与可信评分','','只依据实际输出和差异复核；controller机械完成门与语义成功分开。',''];commands=[]
    for original in base:
        r=dict(original);folder=Path(r['path']);d=folder/'jobs/j-001';m=read(folder/'manifest.json');j=m['jobs'][0]
        assert sha((d/'prompt.md').read_bytes())==r['prompt_sha256'];assert m['input_files']==p['cases'][r['case']]['input_files'];assert m['task']==(OUT/'materials'/r['case']/'task.md').read_text()
        assert (m['model'],m['effort'],m['mode'],m['timeout'])==('gpt-6-sol','low','workspace-write',600)
        for name,h in m['input_files'].items():assert sha((folder/'input'/name).read_bytes())==h
        assert sha((OUT/'materials'/r['case']/'common.md').read_bytes())==r['common_sha256']
        assert sha((OUT/(r['skill']+'.md')).read_bytes())==r['skill_sha256']
        expected_prompt=OUT/'materials'/r['case']/(r['arm']+'-final.prompt.md' if r['split']=='holdout' else 'B-'+r['skill']+'.prompt.md')
        assert (d/'prompt.md').read_bytes()==expected_prompt.read_bytes()
        cmd=j['command'];assert cmd[cmd.index('-m')+1]=='gpt-6-sol' and 'model_reasoning_effort="low"' in cmd and 'approval_policy="never"' in cmd and '--dangerously-bypass-hook-trust' in cmd
        commands.append([x.replace(r['path'],'<run>').replace(r['id'],'<id>') for x in cmd])
        tr=trace(d);tr.update(id=r['id'],case=r['case'],arm=r['arm'],skill=r['skill'],split=r['split'],replicate=r['replicate']);changes=read(d/'changes.json');tr['changes']=changes
        (d/'patch.diff').write_text('\n'.join(x.get('diff','') for x in changes.get('files',[])))
        r.update(tool_calls=len(tr['tools']),shell_failures=[dict(line=c['line'],exit_code=c['exit_code'],command=c['command']) for c in tr['commands'] if c['exit_code'] not in [0,None]],changed_paths=[x['path'] for x in changes.get('files',[])],model_seconds=seconds(r.get('started_at'),r.get('completed_at')),control=tr['control'],runtime_errors=tr['errors'])
        if r.get('score'):
            ev=read(r['evaluation']);assert ev['calibration_verdict']=='PASS' and ev['manifest_sha256']==p['cases'][r['case']]['manifest_sha256']
            cp=Path(p['cases'][r['case']]['manifest']);assert ev['oracle_files']=={str(Path(f).relative_to(cp.parent/'oracle')):h for f,h in p['cases'][r['case']]['oracle_files'].items()}
            for f,h in ev['jobs']['j-001']['candidate_files'].items():assert sha((Path(r['evaluation']).parent/'j-001/candidate'/f).read_bytes())==h
            raw=read(r['raw_oracle']);assert normalize(r['case'],raw)==r['score']
            conservative=r['score']['original_assertion_losses']
            r['score_audit']=dict(original_assertion_failures=[k for k in conservative if k in r['score']['assertions'] and not r['score']['assertions'][k]],original_assertion_not_emitted=[k for k in conservative if k not in r['score']['assertions']],conservative_missing_as_loss=conservative,all_explicit_failed_assertions=[dict(schedule=sc,id=a.get('id')) for sc,x in raw.get('schedules',{}).items() for a in x.get('assertions',[]) if a.get('passed') is False])
        ctl=tr['control'];assert len(ctl['session_ids'])==1
        assert all(h for h in [ctl['event_counts'].get('SessionStart'),ctl['event_counts'].get('Stop'),ctl['event_counts'].get('PostModelRequest')])
        assert ctl['post_model_attempts']==ctl['model_request_attempts']
        assert {k:(r.get('usage') or {}).get(k,0) for k in ['input_tokens','cached_input_tokens','output_tokens']}=={k:ctl['request_usage'][k] for k in ['input_tokens','cached_input_tokens','output_tokens']}
        if r['arm']=='A':assert not any(ctl['decisions'].get(k) for k in ['continue-with-observation','deny-edit-for-evidence','continue-same-session'])
        validation=[c for c in tr['commands'] if __import__('re').search(r'(?:^|\n|&&|;)\s*(?:node|npm|pytest|python[0-9.]*\s+-m\s+(?:pytest|unittest))\b',inner_shell(c['command']))]
        r['maintenance']=dict(candidate_patch_present=bool(changes.get('files')),visible_validation_commands=[dict(line=c['line'],exit_code=c['exit_code']) for c in validation],trusted_behavior_fulfilled=bool(r.get('score') and r['score']['whole_pass']),declared_status=(ctl['state'] or {}).get('completion_check',{}).get('declared_status'),mechanical_completion=(ctl['state'] or {}).get('completion_check'))
        traces.append(tr);rows.append(r)
        rel=lambda f:str(Path(f).relative_to(OUT));title=r['split']+'/'+r['case']+'/'+r['arm']+'/'+r['skill']+'/'+str(r['replicate'])
        evidence += [f'## {title}','',f"[prompt]({rel(d/'prompt.md')}) · [events]({rel(d/'events.jsonl')}) · [patch]({rel(d/'patch.diff')}) · [control]({rel(d/'control/hook-events.jsonl')}) · [result/usage]({rel(d/'result.json')})",'']
        if r.get('score_audit'):evidence += [f"原断言显式失败：{r['score_audit']['original_assertion_failures']}；未发出/不可逐项比较：{r['score_audit']['original_assertion_not_emitted']}。保留原机械缺项按损失的字段，不将其等同实际失败。",'']
        if r.get('raw_oracle'):evidence += [f"[可信原始评分]({rel(r['raw_oracle'])})；{r['score']['verdict']} {r['score']['required_passed']}/{r['score']['required_total']}；原通过检查丢失 {r['score']['original_check_losses']}，断言丢失 {r['score']['original_assertion_losses']}。",'']
        evidence += ['|events行|工具|退出/状态|实际命令或文件|','|---:|---|---|---|']
        for t in tr['tools']:
            i=t['item'];text=i.get('command',str(i.get('changes',[]))).replace('\n',' ↵ ').replace('|','\\|');evidence.append(f"|{t['line']}|{t['kind']}|{i.get('exit_code',i.get('status',''))}|{text[:420]}|")
        evidence += ['',f"控制决定：{ctl['decisions']}；同session={len(ctl['session_ids'])==1}；底层请求{ctl['model_request_attempts']}。",'']
    assert all(c==commands[0] for c in commands)
    optdir=OUT/'evolution';opt=read(optdir/'result.json');tr=trace(optdir);opt.update(split='evolution',tool_calls=len(tr['tools']),control=tr['control'],shell_failures=[c for c in tr['commands'] if c['exit_code'] not in [0,None]],model_seconds=seconds(opt['started_at'],opt['completed_at']));tr['split']='evolution';traces.append(tr)
    assert len(ledger)==len(rows)+1
    assert len(tr['control']['session_ids'])==1
    assert {k:opt['usage'].get(k,0) for k in ['input_tokens','cached_input_tokens','output_tokens']}=={k:tr['control']['request_usage'][k] for k in ['input_tokens','cached_input_tokens','output_tokens']}
    groups={}
    for label,rs in [('development-K0',[r for r in rows if r['split']=='development' and r['skill']=='K0']),('development-K1',[r for r in rows if r['split']=='development' and r['skill']=='K1'])]+[('holdout-'+a,[r for r in rows if r['split']=='holdout' and r['arm']==a]) for a in 'ABC']:
        scores=[r['score'] for r in rs if r.get('score')];groups[label]=dict(costs(rs),valid_scores=len(scores),whole_pass=sum(s['whole_pass'] for s in scores),original_check_loss_runs=sum(bool(s['original_check_losses']) for s in scores),original_assertion_loss_runs=sum(bool(s['original_assertion_losses']) for s in scores),original_assertion_failure_runs=sum(bool(r.get('score_audit',{}).get('original_assertion_failures')) for r in rs),original_assertion_not_emitted_runs=sum(bool(r.get('score_audit',{}).get('original_assertion_not_emitted')) for r in rs),forbidden_runs=sum(bool(s['forbidden']) for s in scores),maintenance_without_patch=sum(not r['maintenance']['candidate_patch_present'] for r in rs),categories=dict(Counter(r['category'] for r in rs)))
    pairs=[]
    for case in HOLD:
        for rep in [1,2]:
            by={r['arm']:r for r in rows if r['split']=='holdout' and r['case']==case and r['replicate']==rep}
            for a,b in [('A','B'),('B','C')]:
                x=by.get(a);y=by.get(b)
                if not x or not y:continue
                u=x.get('score');v=y.get('score');pairs.append(dict(case=case,replicate=rep,comparison=b+'-'+a,valid=bool(u and v),whole_difference=int(v['whole_pass'])-int(u['whole_pass']) if u and v else None,gained=[k for k,z in v['checks'].items() if z and not u['checks'][k]] if u and v else [],lost=[k for k,z in u['checks'].items() if z and not v['checks'][k]] if u and v else [],lost_assertions=[k for k,z in u['assertions'].items() if z and not v['assertions'].get(k)] if u and v else []))
    if selected['C_cancelled']:
        assert not any(r['arm']=='C' and r['split']=='holdout' for r in rows)
        for c in HOLD:assert (OUT/'materials'/c/'B-final.prompt.md').read_bytes()==(OUT/'materials'/c/'C-final.prompt.md').read_bytes()
    search=[r for r in rows if r['split']=='development']+[opt];incremental=[r for r in rows if r['split']=='development' and r['skill']=='K1']+[opt]
    for path,h in read(OUT/'K1.delivery.freeze.json')['files'].items():assert sha(Path(path).read_bytes())==h
    pipeline_seconds=seconds(ledger[0]['at'],read(OUT/'completion.json')['at'])
    save(OUT/'summary.json',dict(pipeline_elapsed_seconds=pipeline_seconds,status='COMPLETE',selected=selected['selected'],C_cancelled=selected['C_cancelled'],formal_sessions=len(ledger),formal_session_cap=18,unused_budget=18-len(ledger),reserve_used=False,independent_generalization_cases=0,groups=groups,pairs=pairs,development_and_evolution_cost=costs(search),additional_skill_search_cost=costs(incremental),evolver_cost=costs([opt]),total_cost=costs(rows+[opt]),results=rows,evolution=opt,limits=['exposed exploratory heldout; one candidate, two development cases, two holdout repeats','native hooks provide real external lifecycle control with heuristic/mechanical limits, not semantic state certification','K0/K1 affects only skill; fixed BASE, retriever, AST-off, question bank, tools and controller','all internal model requests and Stop continuations included; formal session count is not API request count','no same-condition C replication when Kstar equals K0']))
    save(OUT/'trajectory-evidence.json',traces);(OUT/'EVIDENCE.md').write_text('\n'.join(evidence))
    save(OUT/'audit.json',dict(status='PASS',protected_files_unchanged=len(p['frozen_files']),all_prompt_and_initial_file_hashes_verified=True,scored_bytes_and_oracle_hashes_verified=True,normalized_commands_identical=True,one_session_per_execution=True,native_hook_firing_verified=True,cli_usage_equals_sum_of_request_usage=True,optimizer_packet_heldout_excluded=True,all_original_scores_recomputed_from_raw=True,formal_sessions=len(ledger),budget_cap_ok=len(ledger)<=18,extra_preflight_model_calls=0,git_head_unchanged=__import__('subprocess').check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==read(OUT/'initial-git.json')['head'],git_diff_unchanged=__import__('subprocess').check_output(['git','diff'],cwd=REPO,text=True)==read(OUT/'initial-git.json')['diff']))
    print(json.dumps(groups,indent=2))
if __name__=='__main__':main()
