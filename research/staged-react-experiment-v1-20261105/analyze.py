"""Descriptive audit. Never calls a model or feeds hidden scoring back to repairs."""
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import re
from run import OUT, REPO, CASES, read, save, sha, frozen


def elapsed(row):
    try:
        return (datetime.fromisoformat(row['completed_at'].replace('Z','+00:00'))-
                datetime.fromisoformat(row['started_at'].replace('Z','+00:00'))).total_seconds()
    except (KeyError,TypeError,ValueError):
        return None


def stage_audit(path, arm):
    if not path.exists():
        return dict(expected=arm=='B',present=False,characters=0,records=[],format_compliant=False if arm=='B' else None)
    raw=path.read_text();records=[];errors=[]
    for n,line in enumerate(raw.splitlines(),1):
        if not line.strip(): continue
        try: records.append(dict(line=n,characters=len(line),value=json.loads(line)))
        except ValueError: errors.append(dict(line=n,error='invalid-json',characters=len(line)))
    returns=sum(r['value'].get('event')=='return' for r in records if isinstance(r['value'],dict))
    return dict(expected=arm=='B',present=True,characters=len(raw),records=records,errors=errors,returns=returns,
         format_compliant=not errors and len(records)<=6 and all(r['characters']<=1800 for r in records) and returns<=2,
         semantic_validity='not inferred from JSON; needs trajectory/patch review')


def main():
    p=frozen();runs=read(OUT/'runs.json');rows=read(OUT/'results.json');ledger=read(OUT/'invocations.json')
    assert len({r['id'] for r in ledger})==len(ledger)<=16
    assert {r['id'] for r in rows}<={r['id'] for r in ledger}
    protected=read(OUT/'protocol.pre-runtime-fix.json')['frozen_files']
    unchanged={name:sha(Path(name).read_bytes())==h for name,h in protected.items() if not str(Path(name)).startswith(str(OUT))}
    assert all(unchanged.values())
    traces=[];vectors=[];results=[];commands_normalized=[]
    for r in rows:
        folder=Path(r['path']);d=folder/'jobs/j-001';m=read(folder/'manifest.json');j=m['jobs'][0]
        assert sha((d/'prompt.md').read_bytes())==r['prompt_sha256']
        assert m['input_files']==r['input_files']
        events=[];commands=[];tools=[];messages=[];errors=[];types=Counter()
        for n,line in enumerate((d/'events.jsonl').read_text().splitlines(),1):
            try:e=json.loads(line)
            except ValueError:errors.append(dict(line=n,text=line));continue
            if e.get('type') in ['error','turn.failed']: errors.append(dict(line=n,event=e))
            if e.get('type')!='item.completed':continue
            item=e.get('item',{});kind=item.get('type');types[kind]+=1
            if kind=='error':errors.append(dict(line=n,item=item))
            elif kind=='agent_message':messages.append(dict(line=n,text=item.get('text','')))
            elif kind=='command_execution':
                entry=dict(line=n,command=item.get('command'),exit_code=item.get('exit_code'),output=item.get('aggregated_output',''))
                commands.append(entry);tools.append(dict(line=n,kind=kind,item=item))
            elif kind not in ['reasoning',None]:tools.append(dict(line=n,kind=kind,item=item))
        stage=stage_audit(d/'stages/records.jsonl',r['arm'])
        edits=[t['line'] for t in tools if t['kind']=='file_change']
        if r['arm']=='B' and edits:
            pre=[c['command'].replace('\\','') for c in commands if c['line']<min(edits) and c['exit_code']==0 and '/stage/' in c['command']]
            stage['first_edit_line']=min(edits)
            stage['stages_1_2_recorded_before_first_edit']=all(any(re.search(r'"stage"\s*:\s*'+str(k),s) for s in pre) for k in [1,2])
        changes=read(d/'changes.json') if (d/'changes.json').exists() else {}
        missing_host=any('failed to spawn code-mode host' in json.dumps(e) for e in errors)
        category='execution-tool-unavailable' if missing_host else r['category']
        if not missing_host:
            command=j['command']
            assert command[command.index('-m')+1]=='gpt-6-sol'
            assert 'model_reasoning_effort="low"' in command and 'approval_policy="never"' in command
            assert command[command.index('--sandbox')+1]=='workspace-write'
            assert command[-2:]==['--add-dir','/stage']
            commands_normalized.append([s.replace(r['path'],'<run>').replace(r['id'],'<id>') for s in command])
        tr=dict(id=r['id'],case=r['case'],arm=r['arm'],replicate=r['replicate'],
                events_path=str(d/'events.jsonl'),changes_path=str(d/'changes.json'),answer_path=str(d/'cli-output/answer.md'),
                commands=commands,tools=tools,messages=messages,errors=errors,item_types=dict(types),
                changed_paths=[x['path'] for x in changes.get('files',[])],stage=stage)
        traces.append(tr)
        rr=dict(r,analysis_category=category,model_seconds=elapsed(r),tool_calls=len(tools),
                command_calls=len(commands),stage_characters=stage['characters'],stage_format_compliant=stage['format_compliant'],
                tool_errors=errors,item_types=dict(types),command_failures=[dict(line=c['line'],exit_code=c['exit_code'],command=c['command']) for c in commands if c['exit_code'] not in [0,None]],
                record_write_calls=sum('/stage/' in (c['command'] or '') and any(s in (c['command'] or '') for s in ['>','write_text','write(','tee ']) for c in commands))
        results.append(rr)
        if category not in ['behavior-pass','behavior-failure']:continue
        ep=Path(r['evaluation']);ev=read(ep);assert ev['calibration_verdict']=='PASS'
        meta=p['cases'][r['case']];cp=Path(meta['manifest']);cm=read(cp)
        assert ev['manifest_sha256']==meta['manifest_sha256']
        assert ev['oracle_files']=={str(Path(f).relative_to(cp.parent/'oracle')):h for f,h in meta['oracle_files'].items()}
        raw_path=ep.parent/'j-001/oracle/stdout.json';raw=read(raw_path)
        for name,h in ev['jobs']['j-001']['candidate_files'].items():
            assert sha((ep.parent/'j-001/candidate'/name).read_bytes())==h
        effects=read(cp.parent/cm['oracle']['effects'])['variants']['ungranted']
        base=read(OUT/'calibration'/r['case']/'unchanged/oracle/stdout.json')['observed_effects']
        obs=raw['observed_effects']
        checks={**{'required:'+k:obs[k] is True for k in effects['required']},
                **{'forbidden:'+k:obs[k] is False for k in effects['forbidden']}}
        before={**{'required:'+k:base[k] is True for k in effects['required']},
                **{'forbidden:'+k:base[k] is False for k in effects['forbidden']}}
        vectors.append(dict(id=r['id'],case=r['case'],arm=r['arm'],replicate=r['replicate'],
             whole_pass=raw['verdict']=='PASS',verdict=raw['verdict'],checks=checks,
             required_passed=sum(obs[k] for k in effects['required']),required_total=len(effects['required']),
             forbidden_violated=[k for k in effects['forbidden'] if obs[k]],
             lost_original_passed=[k for k,v in before.items() if v and not checks[k]],
             missing_required_effects=raw.get('missing_required_effects',[]),raw_oracle=str(raw_path),
             patch=str(d/'changes.json'),scored_candidate=str(ep.parent/'j-001/candidate')))
    pairs=[]
    for case in CASES:
        for rep in [1,2]:
            a=next((v for v in vectors if v['case']==case and v['replicate']==rep and v['arm']=='A'),None)
            b=next((v for v in vectors if v['case']==case and v['replicate']==rep and v['arm']=='B'),None)
            if a and b:
                pairs.append(dict(case=case,replicate=rep,A=a['whole_pass'],B=b['whole_pass'],
                     difference=int(b['whole_pass'])-int(a['whole_pass']),
                     B_gained=[k for k,v in b['checks'].items() if v and not a['checks'][k]],
                     B_lost=[k for k,v in a['checks'].items() if v and not b['checks'][k]]))
    arms={};per_case={}
    for arm in ['A','B']:
        rs=[r for r in results if r['arm']==arm];vs=[v for v in vectors if v['arm']==arm]
        arms[arm]=dict(scheduled=8,recorded=len(rs),valid_scored=len(vs),whole_pass=sum(v['whole_pass'] for v in vs),
             required_passed=sum(v['required_passed'] for v in vs),required_total=sum(v['required_total'] for v in vs),
             original_loss_runs=sum(bool(v['lost_original_passed']) for v in vs),
             forbidden_effects=sum(len(v['forbidden_violated']) for v in vs),
             input_tokens=sum((r.get('usage') or {}).get('input_tokens',0) for r in rs),
             cached_input_tokens=sum((r.get('usage') or {}).get('cached_input_tokens',0) for r in rs),
             output_tokens=sum((r.get('usage') or {}).get('output_tokens',0) for r in rs),
             model_seconds=round(sum(r['model_seconds'] or 0 for r in rs),3),
             tool_calls=sum(r['tool_calls'] for r in rs),command_calls=sum(r['command_calls'] for r in rs),
             nonzero_command_calls=sum(len(r['command_failures']) for r in rs),
             stage_characters=sum(r['stage_characters'] for r in rs),
             record_write_calls=sum(r['record_write_calls'] for r in rs),controller_model_calls=0,
             categories=dict(Counter(r['analysis_category'] for r in rs)))
    paired_cost={}
    valid_ids={v['id'] for v in vectors if any(q['case']==v['case'] and q['replicate']==v['replicate'] for q in pairs)}
    for arm in ['A','B']:
        rs=[r for r in results if r['id'] in valid_ids and r['arm']==arm]
        paired_cost[arm]=dict(n=len(rs),input_tokens=sum((r.get('usage') or {}).get('input_tokens',0) for r in rs),
                output_tokens=sum((r.get('usage') or {}).get('output_tokens',0) for r in rs),
                cached_input_tokens=sum((r.get('usage') or {}).get('cached_input_tokens',0) for r in rs),
                model_seconds=round(sum(r['model_seconds'] or 0 for r in rs),3),tool_calls=sum(r['tool_calls'] for r in rs))
    paired_case_cost={}
    for case in CASES:
        paired_case_cost[case]={}
        for arm in ['A','B']:
            rs=[r for r in results if r['id'] in valid_ids and r['arm']==arm and r['case']==case]
            paired_case_cost[case][arm]=dict(n=len(rs),input_tokens=sum((r.get('usage') or {}).get('input_tokens',0) for r in rs),
              output_tokens=sum((r.get('usage') or {}).get('output_tokens',0) for r in rs),
              model_seconds=round(sum(r['model_seconds'] or 0 for r in rs),3),tool_calls=sum(r['tool_calls'] for r in rs))
    paired_delta={k:dict(absolute=paired_cost['B'][k]-paired_cost['A'][k],
              percent=100*(paired_cost['B'][k]/paired_cost['A'][k]-1) if paired_cost['A'][k] else None)
              for k in ['input_tokens','output_tokens','model_seconds','tool_calls']}
    for case in CASES:
        per_case[case]={arm:[dict(replicate=rep,
            result=next((v for v in vectors if v['case']==case and v['arm']==arm and v['replicate']==rep),None),
            run=next((r for r in results if r['case']==case and r['arm']==arm and r['replicate']==rep),None))
            for rep in [1,2]] for arm in ['A','B']}
    stable_a_losses={}
    for case in CASES:
        av=[v for v in vectors if v['case']==case and v['arm']=='A']
        if len(av)==2:
            stable=set.intersection(*[{k for k,b in v['checks'].items() if b} for v in av])
            stable_a_losses[case]=[dict(replicate=v['replicate'],lost=sorted(k for k in stable if not v['checks'][k]))
                 for v in vectors if v['case']==case and v['arm']=='B']
    summary=dict(at=datetime.now().isoformat(),scheduled=16,invocations=len(ledger),recorded=len(rows),
         independent_generalization_cases=0,history_failure_selected=True,arms=arms,per_case=per_case,pairs=pairs,
         pair_wins=sum(q['difference']>0 for q in pairs),pair_losses=sum(q['difference']<0 for q in pairs),
         pair_ties=sum(q['difference']==0 for q in pairs),paired_cost=paired_cost,paired_cost_delta=paired_delta,
         stable_A_check_losses=stable_a_losses,paired_cost_per_case=paired_case_cost,
         runtime_deviation=read(OUT/'runtime-correction.json'),limits='Prompt-only staging; selected exposed fixtures; small N; no causal line attribution or significance; no retries.')
    save(OUT/'summary.json',summary);save(OUT/'raw-vectors.json',vectors);save(OUT/'trajectory-evidence.json',traces)
    save(OUT/'analysis-runs.json',results)
    command_variants={json.dumps(c) for c in commands_normalized}
    assert len(command_variants)<=1, 'valid slots must use identical normalized commands'
    save(OUT/'audit.json',dict(status='PASS_WITH_RUNTIME_DEVIATION',original_protected_files_unchanged=all(unchanged.values()),
        protected_file_count=len(unchanged),frozen_prompt_and_input_hashes=True,unique_invocations=len(ledger),
        valid_command_variants=len(command_variants),valid_model_permissions_budgets_equal=True,
        credential_profiles_remaining=list(str(x) for x in (OUT/'.runtime').glob('*')),
        excluded_execution_slots=[r['id'] for r in results if r['analysis_category'].startswith('execution')],
        validation_unverified=[r['id'] for r in results if r['analysis_category']=='validation-unverified']))
    print(json.dumps(dict(arms=arms,pair_wins=summary['pair_wins'],pair_losses=summary['pair_losses'],
          pair_ties=summary['pair_ties'],paired_cost_delta=paired_delta),ensure_ascii=False,indent=2))


if __name__=='__main__': main()
