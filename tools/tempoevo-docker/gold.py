"""Unchanged benchmark verdicts, with retained oracle worker diagnostics."""
import json,subprocess,sys,time
from pathlib import Path


def worker_diagnostics(case, candidate, node, score, deadline):
    """Replay only failed known schedules, without changing their verdicts."""
    worker=case/'oracle/worker.cjs';manifest=case/'oracle/schedules.json'
    if not worker.is_file() or not manifest.is_file():return []
    known={row['id'] for row in json.loads(manifest.read_text())['schedules']}
    failed={key for key,row in score.get('schedules',{}).items() if isinstance(row,dict) and row.get('runtimeError')}
    failed.update(row['schedule'] for row in score.get('runtime_errors',[]) if isinstance(row,dict) and isinstance(row.get('schedule'),str))
    details=[]
    for schedule in sorted(failed & known):
        remaining=deadline-time.monotonic()
        if remaining<=0:break
        command=[node,str(worker),candidate,schedule,'ungranted']
        try:
            run=subprocess.run(command,capture_output=True,text=True,timeout=min(5,remaining))
            detail=dict(schedule=schedule,returncode=run.returncode,stdout=run.stdout,stderr=run.stderr)
            try:
                value=json.loads(run.stdout)
                if isinstance(value,dict):detail['runtime_error']=value.get('runtimeError')
            except ValueError:detail['parse_error']='Worker did not return one JSON object'
        except (OSError,subprocess.TimeoutExpired) as error:
            detail=dict(schedule=schedule,diagnostic_error=str(error))
        details.append(detail)
    return details


def grade(case, candidate, node):
    deadline=time.monotonic()+170
    p=subprocess.run([node,str(case/'oracle/probe.cjs'),candidate,'ungranted'],capture_output=True,text=True,timeout=150)
    sys.stderr.write(p.stderr);score=json.loads(p.stdout)
    runtime_error=bool(score.get('runtime_errors')) or any(isinstance(x,dict) and x.get('runtimeError') for x in score.get('schedules',{}).values())
    invalid=p.returncode not in (0,1) or ((p.returncode==0)!=(score.get('verdict')=='PASS')) or runtime_error
    result=dict(valid=not invalid,passed=score['verdict']=='PASS',verdict=score['verdict'],full_score=score,error=None)
    if invalid:
        result.update(error='Oracle worker runtime error; inspect retained runtime_diagnostics' if runtime_error else 'Grader process error; retained trusted logs',
                      failure_type='oracle_runtime_error' if runtime_error else 'infrastructure_error')
    if runtime_error:
        try:result['runtime_diagnostics']=worker_diagnostics(case,candidate,node,score,deadline)
        except (OSError,ValueError,KeyError,TypeError) as error:result['diagnostic_error']=str(error)
    return result


if __name__=='__main__':
    c=json.loads(Path('/checks/case.json').read_text());case=Path('/opt/swe-tempoc')/Path(c['manifest']).parent
    print(json.dumps(grade(case,sys.argv[-1],'/opt/swe-tempoc/.swe-tempoc/toolchains/node-v16.20.2/bin/node')))
