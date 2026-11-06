"""Audit and summarize search cost, development selection and held-out outcomes."""
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
from run import OUT,REPO,DEV,HOLDOUT,read,save,sha,check_frozen,decide


def seconds(row):
    try:return (datetime.fromisoformat(row['completed_at'].replace('Z','+00:00'))-datetime.fromisoformat(row['started_at'].replace('Z','+00:00'))).total_seconds()
    except (KeyError,TypeError,ValueError):return None


def events(path):
    tools=[];messages=[];errors=[];types=Counter()
    for n,line in enumerate(path.read_text().splitlines(),1):
        e=json.loads(line)
        if e.get('type') in ['error','turn.failed']:errors.append(dict(line=n,event=e))
        if e.get('type')!='item.completed':continue
        i=e.get('item',{});kind=i.get('type');types[kind]+=1
        if kind=='error':errors.append(dict(line=n,item=i))
        elif kind=='agent_message':messages.append(dict(line=n,text=i.get('text','')))
        elif kind not in ['reasoning',None]:tools.append(dict(line=n,kind=kind,item=i))
    return dict(tools=tools,messages=messages,errors=errors,item_types=dict(types))


def resources(rows):
    result=dict(n=len(rows),input_tokens=0,cached_input_tokens=0,output_tokens=0,seconds=0,tool_calls=0,stage_characters=0)
    for row in rows:
        for k in ['input_tokens','cached_input_tokens','output_tokens']:result[k]+=(row.get('usage') or {}).get(k,0)
        result['seconds']+=seconds(row) or 0;result['tool_calls']+=row.get('tool_calls',0);result['stage_characters']+=row.get('stage_characters',0)
    result['seconds']=round(result['seconds'],3)
    result['uncached_input_tokens']=result['input_tokens']-result['cached_input_tokens']
    return result


def main():
    p=check_frozen();raw=read(OUT/'results.json');ledger=read(OUT/'invocations.json')
    assert len(ledger)<=16 and len({r['label'] for r in ledger})==len(ledger)
    rows=[];traces=[];normalized=[]
    for r in raw:
        folder=Path(r['path']);d=folder/'jobs/j-001';m=read(folder/'manifest.json');meta=p['cases'][r['case']]
        assert sha((d/'prompt.md').read_bytes())==r['prompt_sha256']
        assert sha((OUT/'cases'/r['case']/'common.md').read_bytes())==r['common_sha256']==meta['common_sha256']
        assert sha((OUT/(r['variant']+'.md')).read_bytes())==r['variant_sha256']
        assert m['input_files']==r['input_files']==meta['input_files']
        assert m['model']=='gpt-6-sol' and m['effort']=='low' and m['timeout']==600 and m['mode']=='workspace-write'
        for name,h in r['input_files'].items():assert sha((folder/'input'/name).read_bytes())==h
        cmd=m['jobs'][0].get('command',[])
        if cmd:
            assert cmd[cmd.index('-m')+1]=='gpt-6-sol' and 'model_reasoning_effort="low"' in cmd
            normalized.append([v.replace(r['path'],'<run>').replace(r['id'],'<id>') for v in cmd])
        trace=events(d/'events.jsonl');stagefile=d/'stages/records.jsonl';records=[];format_errors=[]
        if stagefile.exists():
            text=stagefile.read_text()
            for n,line in enumerate(text.splitlines(),1):
                if not line.strip():continue
                try:records.append(dict(line=n,characters=len(line),value=json.loads(line)))
                except ValueError:format_errors.append(dict(line=n,characters=len(line),error='invalid JSON'))
        else:text=''
        stage=dict(characters=len(text),records=records,errors=format_errors,
                   format_within_limits=bool(records) and not format_errors and len(records)<=6 and all(v['characters']<=1800 for v in records))
        commands=[dict(line=t['line'],command=t['item'].get('command'),exit_code=t['item'].get('exit_code'),output=t['item'].get('aggregated_output','')) for t in trace['tools'] if t['kind']=='command_execution']
        trace.update(id=r['id'],label=r['label'],case=r['case'],variant=r['variant'],split=r['split'],arm=r['arm'],replicate=r['replicate'],
                     events=str(d/'events.jsonl'),changes=str(d/'changes.json'),stage=stage,commands=commands)
        traces.append(trace)
        row=dict(r,tool_calls=len(trace['tools']),stage_characters=len(text),command_failures=sum(c['exit_code'] not in [0,None] for c in commands))
        rows.append(row)
        if r['category']=='behavior':
            ep=Path(r['evaluation']);ev=read(ep);assert ev['calibration_verdict']=='PASS'
            assert ev['manifest_sha256']==meta['manifest_sha256']
            cp=Path(meta['manifest']);assert ev['oracle_files']=={str(Path(f).relative_to(cp.parent/'oracle')):h for f,h in meta['oracle_files'].items()}
            for name,h in ev['jobs']['j-001']['candidate_files'].items():assert sha((ep.parent/'j-001/candidate'/name).read_bytes())==h
            assert read(r['raw_oracle'])['verdict']==r['score']['verdict']
    assert len({json.dumps(c) for c in normalized})<=1
    optimizers=[]
    for name in ['P1','P2']:
        d=OUT/'candidates'/name
        if not (d/'result.json').exists():continue
        rec=read(d/'result.json');t=events(d/'events.jsonl');rec['tool_calls']=len(t['tools']);rec['stage_characters']=0;optimizers.append(rec)
        assert rec['command'][rec['command'].index('-m')+1]=='gpt-6-sol' and 'model_reasoning_effort="low"' in rec['command']
        expected=read(d/'packet-hashes.json')
        for path,h in expected.items():assert sha((d/'workspace'/path).read_bytes())==h
        assert all(not c in path for c in HOLDOUT for path in expected)
        payload='\n'.join((d/'workspace'/path).read_text(errors='replace') for path in expected)
        assert all(c not in payload for c in HOLDOUT)
        t.update(variant=name,split='optimizer',events=str(d/'events.jsonl'));traces.append(t)
    selections=read(OUT/'selection.json') if (OUT/'selection.json').exists() else []
    current='P0';current_rows=[r for r in rows if r['split']=='development' and r['variant']=='P0']
    for receipt in selections:
        candidate=[r for r in rows if r['split']=='development' and r['variant']==receipt['candidate']]
        expected=decide(current_rows,candidate) if candidate else dict(accept=False,reason='invalid generated workflow; development slots skipped')
        # JSON serialization turns tuples into lists.
        assert json.loads(json.dumps(expected))==receipt['decision']
        assert receipt['incumbent_before']==current
        if receipt['decision']['accept']:current=receipt['candidate'];current_rows=candidate
    selected=read(OUT/'selected.freeze.json') if (OUT/'selected.freeze.json').exists() else None
    if selected:
        assert selected['selected']==current and sha((OUT/'Pstar.md').read_bytes())==selected['sha256']
        held=[r for r in rows if r['split']=='holdout']
        if held:
            assert selected['at']<min(r['started_at'] for r in held)
            assert all(r['variant']==('P0' if r['arm']=='P0' else current) for r in held)
    dev={}
    for variant in ['P0','P1','P2']:
        rr=[r for r in rows if r['split']=='development' and r['variant']==variant];valid=[r for r in rr if r.get('score')]
        dev[variant]=dict(recorded=len(rr),whole_pass=sum(r['score']['whole_pass'] for r in valid),valid=len(valid),
          required_passed=sum(r['score']['required_passed'] for r in valid),required_total=sum(r['score']['required_total'] for r in valid),
          resources=resources(rr),cases=[{k:r[k] for k in ['case','score','category','path']} for r in rr])
    pairs=[]
    for c in HOLDOUT:
        for rep in [1,2]:
            base=next((r for r in rows if r['split']=='holdout' and r['case']==c and r['replicate']==rep and r['arm']=='P0'),None)
            new=next((r for r in rows if r['split']=='holdout' and r['case']==c and r['replicate']==rep and r['arm']=='Pstar'),None)
            if base and new and base['score'] and new['score']:
                pairs.append(dict(case=c,replicate=rep,P0=base['score']['whole_pass'],Pstar=new['score']['whole_pass'],
                  difference=int(new['score']['whole_pass'])-int(base['score']['whole_pass']),
                  gained=[k for k,v in new['score']['checks'].items() if v and not base['score']['checks'][k]],
                  lost=[k for k,v in base['score']['checks'].items() if v and not new['score']['checks'][k]]))
    holdout={}
    for arm in ['P0','Pstar']:
        rr=[r for r in rows if r['split']=='holdout' and r['arm']==arm];valid=[r for r in rr if r['score']]
        holdout[arm]=dict(recorded=len(rr),valid=len(valid),whole_pass=sum(r['score']['whole_pass'] for r in valid),
          required_passed=sum(r['score']['required_passed'] for r in valid),required_total=sum(r['score']['required_total'] for r in valid),
          forbidden_runs=sum(bool(r['score']['forbidden']) for r in valid),original_loss_runs=sum(bool(r['score']['lost_original']) for r in valid),
          resources=resources(rr))
    costs=dict(development=resources([r for r in rows if r['split']=='development']),optimizer=resources(optimizers),
      holdout=resources([r for r in rows if r['split']=='holdout']),all=resources(rows+optimizers))
    differences={}
    for metric in ['input_tokens','output_tokens','seconds','tool_calls']:
        a=holdout['P0']['resources'][metric];b=holdout['Pstar']['resources'][metric]
        differences[metric]=dict(absolute=b-a,percent=100*(b/a-1) if a else None)
    summary=dict(status=read(OUT/'completion.json')['status'] if (OUT/'completion.json').exists() else 'RUNNING',
       invocations=len(ledger),repairs=len(rows),optimizer_calls=len(optimizers),model='gpt-6-sol',effort='low',
       development=dev,selection=selections,selected=selected,holdout=holdout,pairs=pairs,
       accepted_updates=sum(r['decision']['accept'] for r in selections),new_prompt_selected=bool(selected and selected['selected']!='P0'),
       holdout_interpretation='Identical P0 inputs; repeatability only, no prompt-optimization treatment contrast' if selected and selected['selected']=='P0' else 'Frozen selected workflow versus P0; optimizer-heldout only',
       wins=sum(v['difference']>0 for v in pairs),losses=sum(v['difference']<0 for v in pairs),ties=sum(v['difference']==0 for v in pairs),
       holdout_cost_delta=differences,costs=costs,independent_generalization_cases=0,
       limits='Development selected on single draws; optimizer-heldout tasks are historically exposed; two rounds only; no statistical or broad generalization claim.')
    save(OUT/'summary.json',summary);save(OUT/'analysis-runs.json',rows);save(OUT/'trajectory-evidence.json',traces)
    save(OUT/'audit.json',dict(status='PASS',frozen_files_verified=True,unique_invocations=len(ledger),maximum=16,
      identical_normalized_repair_commands=True,optimizer_packets_dev_only=True,packet_hashes_unchanged=True,
      selection_replayed=True,selected_frozen_before_holdout=bool(selected),candidate_and_oracle_hashes_verified=True,
      execution_failures=[r['label'] for r in rows if r['category'].startswith('execution')],
      validation_unverified=[r['label'] for r in rows if r['category']=='validation-unverified'],
      active_runtime_profiles=[str(f) for f in (OUT/'.runtime').glob('*')]))
    print(json.dumps(dict(invocations=len(ledger),dev={k:(v['whole_pass'],v['required_passed'],v['required_total']) for k,v in dev.items()},selected=current,holdout={k:v['whole_pass'] for k,v in holdout.items()},costs=costs),indent=2))


if __name__=='__main__':main()
