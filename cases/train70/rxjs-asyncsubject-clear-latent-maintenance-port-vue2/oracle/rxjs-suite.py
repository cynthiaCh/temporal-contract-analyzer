import sys,json,shutil,tempfile,uuid,os,time
from pathlib import Path
root=next(p for p in Path(__file__).resolve().parents if(p/'casecatalog.py').exists());sys.path.insert(0,str(root))
from tempoc import upstreamagent as ua,upstreamcalibrate as cal
import casecatalog
out=root/'results/multi-family-expansion-20261005';parent=casecatalog.locations()['rxjs-asyncsubject-clear-latent-maintenance'].root;task=json.loads((parent/'task.json').read_text());node,env=ua.runtime(task,root/'results/student-case-expansion-runtime/node18/bin/node')
logs=out/'rxjs-executions'/uuid.uuid4().hex;logs.mkdir(parents=True);candidate=Path(sys.argv[1]);started=time.monotonic()
try:
 with tempfile.TemporaryDirectory(prefix='rxjs-preserved-')as tmp:
  work=Path(tmp)/'repository';shutil.copytree(candidate/'rxjs',work);(work/'node_modules').symlink_to(out/'rxjs-cache/workspace/node_modules',target_is_directory=True)
  ua.upstreambench.apply_patch(work,parent/task['test_patch']);tests=ua.execute_tests(task,work,logs/'tests',node,env);api=ua.execute_public_api(parent,task,work,logs/'public-api',node,env)
  groups=cal.read(parent/task['groups']);schedules={}
  for id,group in [('upstream-feature','fail_to_pass'),('upstream-preservation','pass_to_pass')]:
   assertions=[dict(id=name,passed=tests.get(name,{}).get('status')=='passed',actual=tests.get(name,{}).get('status'),expected='passed')for name in groups[group]]
   schedules[id]=dict(passed=all(a['passed']for a in assertions),runtimeError=None,assertions=assertions)
  schedules['public-api']=dict(passed=api['passed'],runtimeError=None,assertions=[dict(id='public-clear-void',passed=api['passed'],actual=api['exit_code'],expected=0)])
  result=dict(schedules=schedules,receipt=str(logs.relative_to(root)),versions=json.loads((out/'rxjs-cache/install-receipts/environment.json').read_text()),elapsed_seconds=time.monotonic()-started)
except Exception as e:result=dict(error=str(e),receipt=str(logs.relative_to(root)))
(logs/'suite.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));sys.exit(2 if'error'in result else 0)
