class Attempt:
    def __init__(self,number,previous,options):self.number=number;self.previous=dict(previous);self.options=options;self.settled=False;self.consumed=False;self.retry_cancelled=False;self.failures=0;self.queued=False;self.started=False
class Query:
    def __init__(self,key,data):self.key=key;self.state=dict(status='success' if data is not None else 'pending',fetchStatus='idle',data=data);self.observers=set();self.attempt=None;self.consumed=False
class Session:
    def __init__(self,env,initial):self.env=env;self.cache={};self.handles={};self.online=initial.get('online',True);self.focused=initial.get('focused',True);self.serial=0;self.fetch_serial=0
    def eligible(self,a):return self.focused and (a.options.get('networkMode','online')=='always' or self.online)
    def active(self,q,a):return q.attempt is a and not a.settled
    def cancel(self,q,a):
        if a.settled:return
        a.settled=True;q.state=dict(a.previous);q.state['fetchStatus']='idle';self.env.call('abort',q.key,a.number)
    def invoke(self,q,a):
        a.queued=False
        if not self.active(q,a):return
        a.started=True
        q.state['fetchStatus']='fetching';q.consumed=False
        def consume(_):q.consumed=True;return None
        def complete(value):
            if not self.active(q,a):return
            if value['ok']:
                a.settled=True;q.state.update(data=value['value'],status='success',fetchStatus='idle')
            elif not a.retry_cancelled and a.failures<a.options.get('retry',0):
                a.failures+=1
                def retry(_):
                    if not self.active(q,a):return
                    if a.retry_cancelled:a.settled=True;q.state.update(status='error',fetchStatus='idle');return
                    if self.eligible(a):self.invoke(q,a)
                    else:q.state['fetchStatus']='paused'
                self.env.call('schedule',self.env.bind(retry),a.options.get('retryDelay',10))
            else:a.settled=True;q.state.update(status='error',fetchStatus='idle')
        self.env.call('request',q.key,a.number,self.env.bind(consume),self.env.bind(complete))
    def resume(self,q):
        a=q.attempt
        if a and self.active(q,a) and q.state['fetchStatus']=='paused' and self.eligible(a) and not a.queued:
            a.queued=True
            def continuation(_):
                a.queued=False
                if not self.active(q,a):return
                if a.retry_cancelled and not a.started and a.previous['status']=='pending':
                    a.settled=True;q.state['fetchStatus']='idle';return
                if a.failures and a.retry_cancelled:a.settled=True;q.state.update(status='error',fetchStatus='idle');return
                self.invoke(q,a)
            self.env.call('defer',self.env.bind(continuation))
    def subscribe(self,key,options):
        q=self.cache.get(key)
        if q is None:q=Query(key,options.get('initialData'));self.cache[key]=q
        self.serial+=1;handle=self.serial;self.handles[handle]=q;q.observers.add(handle)
        if q.attempt and not q.attempt.settled:q.attempt.retry_cancelled=False;self.resume(q)
        else:
            self.fetch_serial+=1;a=Attempt(self.fetch_serial,q.state,options);q.attempt=a;self.env.call('newAttempt',key,a.number)
            if options.get('networkMode','online')!='online' or self.online:self.invoke(q,a)
            else:q.state['fetchStatus']='paused'
        return handle
    def unsubscribe(self,handle):
        q=self.handles.pop(handle,None)
        if q is None:return
        q.observers.remove(handle)
        if not q.observers:
            a=q.attempt
            if a and not a.settled:
                if q.consumed:self.cancel(q,a)
                else:a.retry_cancelled=True
    def handle(self,name,args):
        if name=='subscribe':return self.subscribe(*args)
        if name=='unsubscribe':return self.unsubscribe(*args)
        if name=='online':self.online=args[0]
        elif name=='focus':self.focused=args[0]
        elif name=='snapshot':return dict(self.cache[args[0]].state)
        elif name=='dispose':
            for h in list(self.handles):self.unsubscribe(h)
            return None
        else:raise ValueError(name)
        for q in list(self.cache.values()):self.resume(q)
