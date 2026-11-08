import sys,json,importlib.util
spec=importlib.util.spec_from_file_location('candidate',sys.argv[1]+'/src/workflow.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
callbacks={};sessions={};serial=0
class Env:
    def __init__(self,w):self.w=w
    def bind(self,fn):
        global serial
        serial+=1;callbacks[serial]=fn;return serial
    def call(self,name,*args):
        send(dict(call=name,args=[self.w]+list(args)))
        while True:
            m=json.loads(sys.stdin.readline())
            if 'reply' in m:return m['reply']
            answer(m)
def send(value):print(json.dumps(value),flush=True)
def dispatch(m):
    name=m['method'];a=m['args']
    if name=='invoke':return callbacks[a[0]](a[1])
    if name=='init':sessions[a[0]]=app.Session(Env(a[0]),a[1]);return None
    return sessions[a[0]].handle(name,a[1:])
def answer(m):send(dict(result=dispatch(m)))
for line in sys.stdin:answer(json.loads(line))
