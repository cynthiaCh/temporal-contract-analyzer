"""Research-side descriptive scoring and actual tool/patch indexes; no models."""
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
from run import OUT,REPO,CASE,freeze,read,save,sha,token_count


def main():
    p=freeze();rows=read(OUT/'results.json');runs=read(OUT/'runs.json');ledger=read(OUT/'invocations.json')
    assert len(rows)==len(ledger)==len(runs)==9
    assert {r['id'] for r in rows}=={r['id'] for r in runs}=={r['id'] for r in ledger}
    cp=Path(p['case_meta']['manifest']);cm=read(cp);effects=read(cp.parent/cm['oracle']['effects'])['variants']['ungranted']
    def vector(raw):return {**{'required:'+k:raw['observed_effects'][k] is True for k in effects['required']},**{'forbidden:'+k:raw['observed_effects'][k] is False for k in effects['forbidden']}}
    def assertions(raw):return {s+'/'+a['id']:a['passed'] for s,v in raw['schedules'].items() for a in v.get('assertions',[])}
    baseline=read(OUT/'calibration/unchanged/oracle/stdout.json');before=vector(baseline);baseline_assert=assertions(baseline)
    historical=read(p['baseline_history']['raw_oracle']);hv=vector(historical)
    traces=[];results=[];lines=['# 可信评分、实际工具输出与补丁索引','','仅研究侧，未交付执行 Agent。分析依据完整工具输出和差异；不以自述“已检查”为证明。','']
    commands_normal=[]
    for row in rows:
        r=dict(row);folder=Path(r['path']);d=folder/'jobs/j-001';m=read(folder/'manifest.json');j=m['jobs'][0]
        assert sha((d/'prompt.md').read_bytes())==r['prompt_sha256']
        assert m['input_files']==p['case_meta']['input_files']
        assert m['task']==(OUT/'materials/task.md').read_text()
        assert (m['model'],m['effort'],m['mode'],m['timeout'])==('gpt-6-sol','low','workspace-write',600)
        for path,h in m['input_files'].items():assert sha((folder/'input'/path).read_bytes())==h
        cmd=j.get('command',[])
        assert cmd[cmd.index('-m')+1]=='gpt-6-sol' and 'model_reasoning_effort="low"' in cmd and 'approval_policy="never"' in cmd
        assert cmd[cmd.index('--sandbox')+1]=='workspace-write'
        commands_normal.append([x.replace(r['path'],'<run>').replace(r['id'],'<id>') for x in cmd])
        tools=[];commands=[];messages=[];errors=[]
        for n,l in enumerate((d/'events.jsonl').read_text().splitlines(),1):
            e=json.loads(l);i=e.get('item',{});kind=i.get('type')
            if e.get('type') in ['error','turn.failed']:errors.append(dict(line=n,event=e))
            if e.get('type')!='item.completed':continue
            if kind=='agent_message':messages.append(dict(line=n,text=i.get('text','')))
            elif kind=='reasoning':continue
            elif kind=='error':errors.append(dict(line=n,item=i))
            elif kind:
                t=dict(line=n,kind=kind,item=i);tools.append(t)
                if kind=='command_execution':commands.append(dict(line=n,command=i.get('command'),exit_code=i.get('exit_code'),output=i.get('aggregated_output','')))
        changes=read(d/'changes.json') if (d/'changes.json').exists() else {}
        (d/'patch.diff').write_text('\n'.join(f['diff'] for f in changes.get('files',[]) if 'diff' in f))
        tr=dict(id=r['id'],arm=r['arm'],replicate=r['replicate'],commands=commands,tools=tools,visible_messages=messages,errors=errors,changes=changes,
                stages=(d/'stages/records.jsonl').read_text() if (d/'stages/records.jsonl').exists() else None)
        traces.append(tr)
        r.update(tool_calls=len(tools),shell_calls=len(commands),tool_types=dict(Counter(t['kind'] for t in tools)),errors=errors,shell_failures=[dict(line=c['line'],command=c['command'],exit_code=c['exit_code']) for c in commands if c['exit_code'] not in [0,None]],changed_paths=[f['path'] for f in changes.get('files',[])])
        try:r['model_seconds']=(datetime.fromisoformat(r['completed_at'].replace('Z','+00:00'))-datetime.fromisoformat(r['started_at'].replace('Z','+00:00'))).total_seconds()
        except (KeyError,TypeError,ValueError):r['model_seconds']=None
        if r['category']=='behavior':
            ev=read(r['evaluation']);assert ev['calibration_verdict']=='PASS' and ev['manifest_sha256']==p['case_meta']['manifest_sha256']
            assert ev['oracle_files']=={str(Path(f).relative_to(cp.parent/'oracle')):h for f,h in p['case_meta']['oracle_files'].items()}
            for name,h in ev['jobs']['j-001']['candidate_files'].items():assert sha((Path(r['evaluation']).parent/'j-001/candidate'/name).read_bytes())==h
            raw=read(r['raw_oracle']);v=vector(raw);av=assertions(raw)
            r['score']=dict(verdict=raw['verdict'],whole_pass=raw['verdict']=='PASS',checks=v,required_passed=sum(raw['observed_effects'][k] is True for k in effects['required']),required_total=len(effects['required']),target_pass=raw['observed_effects']['start-switch-admission'] is True,retry_pass=raw['observed_effects']['retry-preserved'] is True,
               original_check_losses=[k for k,b in before.items() if b and not v.get(k)],original_assertion_losses=[k for k,b in baseline_assert.items() if b and av.get(k) is not True],historical_P0_check_losses=[k for k,b in hv.items() if b and not v.get(k)],forbidden_effects=raw.get('observed_forbidden_effects',[]),
               failed_assertions=[dict(schedule=s,assertion=a['id'],actual=a.get('actual'),expected=a.get('expected')) for s,x in raw['schedules'].items() for a in x.get('assertions',[]) if a['passed'] is False])
        else:r['score']=None
        results.append(r)
        rel=lambda f:str(Path(f).relative_to(OUT))
        lines += [f"## {r['sequence']:02} {r['arm']}{r['replicate']}",'',f"类别 {r['category']}；评分 {r['score']['verdict'] if r['score'] else '未确认'}。",'',f"[完整prompt]({rel(d/'prompt.md')}) · [events]({rel(d/'events.jsonl')}) · [完整补丁]({rel(d/'patch.diff')}) · [用量与命令]({rel(d/'result.json')}) · [阶段记录]({rel(d/'stages/records.jsonl')})",'']
        if r.get('raw_oracle'):lines += [f"[原始可信评分]({rel(r['raw_oracle'])})",'']
        if r['score']:lines += [f"原样已通过检查丢失：{r['score']['original_check_losses']}；原样已通过断言丢失：{r['score']['original_assertion_losses']}；历史P0已通过检查丢失：{r['score']['historical_P0_check_losses']}。",'']
        lines += ['|events行|类型|退出|实际命令/文件|','|---:|---|---|---|']
        for t in tools:
            i=t['item'];content=i.get('command',str(i.get('changes',[]))).replace('\n',' ↵ ').replace('|','\\|')
            lines.append(f"|{t['line']}|{t['kind']}|{i.get('exit_code',i.get('status',''))}|{content[:350]}|")
        lines += ['']
    assert all(c==commands_normal[0] for c in commands_normal)
    paired=[]
    for rep in [1,2,3]:
        by={r['arm']:r for r in results if r['replicate']==rep}
        for a,b in [('A','B'),('B','C'),('A','C')]:
            x=by[a]['score'];y=by[b]['score']
            paired.append(dict(replicate=rep,comparison=b+'-'+a,valid=bool(x and y),whole_difference=int(y['whole_pass'])-int(x['whole_pass']) if x and y else None,gained=[k for k,v in y['checks'].items() if v and not x['checks'][k]] if x and y else None,lost=[k for k,v in x['checks'].items() if v and not y['checks'][k]] if x and y else None))
    arms={}
    for arm in 'ABC':
        rs=[r for r in results if r['arm']==arm];scores=[r['score'] for r in rs if r['score']]
        arms[arm]=dict(scheduled=3,valid=len(scores),whole_pass=sum(s['whole_pass'] for s in scores),target_pass=sum(s['target_pass'] for s in scores),retry_pass=sum(s['retry_pass'] for s in scores),original_check_loss_runs=sum(bool(s['original_check_losses']) for s in scores),original_assertion_loss_runs=sum(bool(s['original_assertion_losses']) for s in scores),historical_P0_loss_runs=sum(bool(s['historical_P0_check_losses']) for s in scores),forbidden_runs=sum(bool(s['forbidden_effects']) for s in scores),input_tokens=sum((r.get('usage') or {}).get('input_tokens',0) for r in rs),cached_input_tokens=sum((r.get('usage') or {}).get('cached_input_tokens',0) for r in rs),output_tokens=sum((r.get('usage') or {}).get('output_tokens',0) for r in rs),model_seconds=round(sum(r['model_seconds'] or 0 for r in rs),3),including_score_seconds=round(sum(r['including_score_seconds'] for r in rs),3),tool_calls=sum(r['tool_calls'] for r in rs),shell_failures=sum(len(r['shell_failures']) for r in rs),categories=dict(Counter(r['category'] for r in rs)))
    prompt_lengths={arm:dict(characters=len((OUT/'materials'/(arm+'.prompt.md')).read_text()),utf8_bytes=(OUT/'materials'/(arm+'.prompt.md')).stat().st_size,proxy_tokens=token_count((OUT/'materials'/(arm+'.prompt.md')).read_text())) for arm in 'ABC'}
    summary=dict(prompt_lengths=prompt_lengths,status='COMPLETE',case=CASE,exposure='author/research exposed development diagnostic',independent_generalization_cases=0,model='gpt-6-sol',effort='low',formal_calls=len(ledger),extra_model_calls=0,retries=0,seed=p['seed'],schedule=[dict(rep=r['replicate'],arm=r['arm']) for r in runs],lengths=p['lengths'],arms=arms,pairs=paired,results=results,limits=['one exposed case and 3 replicates per condition; descriptive only','manual failure-targeted evidence does not measure automatic retrieval','o200k_base proxy prompt token counts; actual usage from CLI includes repeated context and cached input','no independent blind reviewer; research-side human-readable tool and patch audit','finite trusted scores do not establish all-input behavioral equivalence'])
    save(OUT/'trajectory-evidence.json',traces);save(OUT/'summary.json',summary);(OUT/'EVIDENCE.md').write_text('\n'.join(lines))
    save(OUT/'audit.json',dict(status='PASS',protected_hashes=len(p['frozen_files']),frozen_files_unchanged=True,actual_prompt_hashes_verified=9,starting_file_hashes_verified=9,normalized_commands_identical=True,valid_scores=sum(bool(r['score']) for r in results),execution_or_validation_anomalies=[dict(id=r['id'],category=r['category'],errors=r['errors']) for r in results if r['category']!='behavior' or r['errors']],git_head_unchanged=subprocess_head()==read(OUT/'initial-git.json')['head'],git_diff_unchanged=subprocess_diff()==read(OUT/'initial-git.json')['diff']))
    print(json.dumps(arms,indent=2))

def subprocess_head():
    import subprocess
    return subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
def subprocess_diff():
    import subprocess
    return subprocess.check_output(['git','diff'],cwd=REPO,text=True)
if __name__=='__main__':main()
