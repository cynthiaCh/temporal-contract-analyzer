"""Public syntax/build smoke checks only; no scorer, reference or business assertions."""
import ast,json,os,subprocess,sys,tempfile
from pathlib import Path
root=Path(sys.argv[-1]);rows=[]
native=Path('/opt/swe-tempoc/results/student-case-expansion-runtime/native')
node='/opt/swe-tempoc/.swe-tempoc/toolchains/node-v16.20.2/bin/node'
for p in sorted(root.rglob('*')):
 if not p.is_file() or 'node_modules' in p.parts:continue
 ext=p.suffix;cmd=None;env=dict(os.environ)
 try:
  if ext=='.py':ast.parse(p.read_text());rows.append(dict(check='syntax:'+str(p.relative_to(root)),passed=True));continue
  if ext in {'.js','.jsx','.ts','.tsx','.mjs','.cjs','.vue'}:
   code="const fs=require('fs'),p=require('/opt/swe-tempoc/.swe-tempoc/js/node_modules/@babel/parser');let s=fs.readFileSync(process.argv[1],'utf8');if(process.argv[1].endsWith('.vue')){s=[...s.matchAll(/<script[^>]*>([\\s\\S]*?)<\\/script>/g)].map(x=>x[1]).join('\\n')}p.parse(s,{sourceType:'unambiguous',plugins:['jsx','typescript']});"
   cmd=[node,'-e',code,str(p)]
  elif ext=='.go':cmd=[str(native/'usr/lib/go-1.13/bin/gofmt'),'-e',str(p)]
  elif ext=='.php':cmd=[str(native/'usr/bin/php7.4'),'-n','-l',str(p)]
  elif ext=='.rb':
   env.update(LD_LIBRARY_PATH=str(native/'usr/lib/x86_64-linux-gnu'),RUBYLIB=str(native/'usr/lib/ruby/2.7.0')+':'+str(native/'usr/lib/x86_64-linux-gnu/ruby/2.7.0'));cmd=[str(native/'usr/bin/ruby2.7'),'-c',str(p)]
  elif ext=='.java':continue
  if cmd:
   x=subprocess.run(cmd,capture_output=True,text=True,env=env,timeout=90);rows.append(dict(check='syntax:'+str(p.relative_to(root)),passed=x.returncode==0,error=(x.stderr or x.stdout)[-3000:] if x.returncode else None))
 except (SyntaxError,UnicodeError) as e:rows.append(dict(check='syntax:'+str(p.relative_to(root)),passed=False,error=str(e)))
java=list(root.rglob('*.java'))
if java:
 env=dict(os.environ,LD_LIBRARY_PATH='/usr/lib/jvm/java-11-openjdk-amd64/lib/jli')
 with tempfile.TemporaryDirectory() as build:
  x=subprocess.run([str(native/'usr/lib/jvm/java-11-openjdk-amd64/bin/javac'),'-d',build]+[str(p) for p in java],capture_output=True,text=True,env=env,timeout=90)
  rows.append(dict(check='public_java_compile',passed=x.returncode==0,error=x.stderr[-3000:] if x.returncode else None))
print(json.dumps(dict(passed=bool(rows) and all(x['passed'] for x in rows),observations=rows,regressions=[],unknowns=['Syntax/build checks only; business correctness is evaluated independently by training Oracle.'])))
