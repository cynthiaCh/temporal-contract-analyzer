import sys,json,importlib.util
spec=importlib.util.spec_from_file_location('candidate',sys.argv[1]+'/src/workflow.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
telemetry={};callbacks={};sessions={};handles={};files={};serial=0
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
def file(value):
    token=value['token']
    if token not in files:files[token]=value
    return files[token]
def remember(w,h):
    if h is None:return None
    handles[(w,h.number)]=h;return h.number
def dispatch(m):
    name=m['method'];a=m['args']
    if name=='invoke':callbacks[a[0]](a[1]);return None
    w=a[0]
    if name=='telemetryStart':telemetry[w]=app.Telemetry(Env(w),file(a[1]));return None
    if name=='telemetryStop':telemetry[w].stop();return None
    if name=='init':sessions[w]=app.Session(Env(w));return None
    if name=='standalone':return remember(w,app.Attempt(Env(w),file(a[1]),a[2]))
    if name=='cancelHandle':handles[(w,a[1])].cancel();return None
    s=sessions[w]
    if name=='select':return remember(w,s.select(file(a[1])))
    if name=='retry':return remember(w,s.retry())
    return getattr(s,name)()
def answer(m):send(dict(result=dispatch(m)))
for line in sys.stdin:answer(json.loads(line))
