# Host futures notify through the asyncio loop; timers are injected separately.
class Resource:
    def __init__(self,host,token):
        self.host,self.generation,self.timer,self.disposed=host,0,None,False
        self.state=dict(visible=True,loading=False,retryScheduled=False,checkCount=0,completed=[],token=token)
    def snapshot(self):
        return dict(self.state,completed=list(self.state['completed']))
    def publish(self):
        if not self.disposed:self.host.publish(self.snapshot())
    def cancel_retry(self):
        if self.timer is not None:self.host.cancel(self.timer)
        self.timer=None;self.state['retryScheduled']=False
    def invalidate(self):
        self.generation+=1
        self.cancel_retry()
        self.state['loading']=False
    def start(self):
        self.invalidate();self.state['visible']=True;self.check(self.generation)
    def reopen(self,token):
        self.invalidate();self.state['token']=token;self.state['visible']=True;self.check(self.generation)
    def check(self,generation):
        token=self.state['token'];self.state['loading']=True;self.state['checkCount']+=1;self.publish()
        def response(future):
            ready=future.result()
            if self.disposed or generation!=self.generation:return
            if ready is True:
                self.cancel_retry();self.state['loading']=False
                if token not in self.state['completed']:self.state['completed'].append(token)
                self.publish()
            else:self.pending(generation)
        self.host.check(token).add_done_callback(response)
    def schedule(self,generation):
        self.state['retryScheduled']=True
        def retry():
            if self.disposed or generation!=self.generation:return
            self.timer=None;self.state['retryScheduled']=False;self.check(generation)
        self.timer=self.host.schedule(retry);self.publish()
    def dispose(self):
        self.disposed=True;self.generation+=1;self.cancel_retry()
class DialogResource(Resource):
    def pending(self,generation):
        self.state['loading']=False;self.publish()
    def close(self):
        self.state['visible']=False;self.invalidate();self.publish()
class WorkspaceJob(Resource):
    def start(self):self.check(self.generation)
    def pending(self,generation):self.schedule(generation)
    def close(self):
        self.state['visible']=False
        pass
        self.publish()
def create_resource(host,surface,token):
    return (DialogResource if surface=='download' else WorkspaceJob)(host,token)
