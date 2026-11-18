import importlib.util,json,sys
from concurrent.futures import Future
spec=importlib.util.spec_from_file_location('candidate',sys.argv[1]+'/src/workflow.py')
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
def emit(v):print(json.dumps(v),flush=True)
class Host:
    def __init__(self):self.feeds={};self.workspaces={};self.callbacks={};self.serial=0
    def call(self, kind, *args):
        emit(dict(call=kind,args=args))
        while True:
            message=json.loads(sys.stdin.readline())
            if 'reply' in message:return message['reply']
            self.dispatch(message)
    def bind(self, callback):
        self.serial+=1;self.callbacks[self.serial]=callback;return self.serial
    def defer(self, callback):self.call('defer',self.bind(lambda _:callback()))
    def resolve(self, kind, key, frame):
        future=Future();id=self.bind(future.set_result);reply=self.call(kind,key,frame,id)
        if not reply['deferred']:self.callbacks.pop(id)(reply.get('value'))
        return future
    def output(self, kind, key, value):self.call(kind,key,value)
    def dispatch(self, m):
        method,a=m['method'],m['args'];result=None
        if method=='feed':self.feeds[a[0]]=module.Channel(self,*a)
        elif method=='workspace':self.workspaces[a[0]]=module.Workspace(self,a[0])
        elif method=='select':self.workspaces[a[0]].select(self.feeds[a[1]],a[2])
        elif method=='hide':self.workspaces[a[0]].hide()
        elif method=='delta':self.feeds[a[0]].update()
        elif method=='start':self.feeds[a[0]].connect(a[1])
        elif method=='listeners':result=len(self.feeds[a[0]].listeners)
        elif method=='invoke':self.callbacks.pop(a[0])(a[1])
        elif method=='metrics':module.collect_metrics(self,a[0],self.feeds[a[1]])
        else:raise ValueError(method)
        emit(dict(result=result))
host=Host()
for line in sys.stdin:host.dispatch(json.loads(line))
