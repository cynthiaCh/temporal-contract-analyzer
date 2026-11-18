import asyncio, importlib.util, json, sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('candidate',Path(sys.argv[1])/'src/workflow.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class Host:
    def __init__(self):
        self.loop=asyncio.new_event_loop();self.requests=[];self.retries={};self.serial=0;self.published=[]
    def check(self,token):
        future=self.loop.create_future();self.requests.append((token,future));return future
    def schedule(self,callback):self.serial+=1;self.retries[self.serial]=callback;return self.serial
    def cancel(self,handle):self.retries.pop(handle,None)
    def publish(self,state):self.published.append(state)
    def drain(self):
        barrier=self.loop.create_future();self.loop.call_soon(barrier.set_result,None);self.loop.run_until_complete(barrier)
    def fire(self):
        if not self.retries:return False
        handle=next(iter(self.retries));self.retries.pop(handle)();return True
host=Host();resource=None
for line in sys.stdin:
    message=json.loads(line);m=message['method'];a=message['args'];result=None
    if m=='init':resource=module.create_resource(host,*a)
    elif m=='resolve':host.requests[a[0]][1].set_result(a[1])
    elif m=='drain':host.drain()
    elif m=='fire':result=host.fire()
    elif m=='inspect':result={'state':resource.snapshot(),'requests':[x[0] for x in host.requests],'timers':len(host.retries),'published':len(host.published)}
    elif m=='snapshot':result=resource.snapshot()
    elif m=='unmount':resource.dispose()
    else:getattr(resource,m)(*a)
    print(json.dumps({'result':result}),flush=True)
host.loop.close()
